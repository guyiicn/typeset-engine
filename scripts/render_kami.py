#!/usr/bin/env python3
"""
render_kami.py — kami 主题的 HTML → PDF 渲染器（WeasyPrint 后端）

两种使用方式：

1) **完整 HTML 直出**：agent 在本地按 kami 模板填好全部 HTML 后，直接送渲染
   render_html(html_text, base_url, out_path)

2) **按模板类型渲染**：server 从 templates/kami/ 加载指定模板，agent 只提供 body 内容
   render_template(doc_type, language, body_html, slots, out_path)

CLI:
    python3 scripts/render_kami.py --template one-pager --lang en --body body.html --out /tmp/o.pdf
    python3 scripts/render_kami.py --html full.html --out /tmp/o.pdf
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
KAMI_DIR = ROOT / "templates" / "kami"

# 支持的模板类型（中英文对应的模板名约定）
# long-doc-claude = long-doc 的 Anthropic/Claude 烧橙皮肤变体（用于触发词"claude 风格"）
DOC_TYPES = {"one-pager", "long-doc", "long-doc-claude", "letter", "portfolio", "resume"}

# 每个 doc_type 的页数硬约束（见 design-constraints 第 5 节）
PAGE_LIMITS = {
    "resume":           (1, 2),    # 严格 ≤2
    "one-pager":        (1, 1),    # 严格 = 1
    "letter":           (1, 1),    # 严格 = 1
    "long-doc":         (5, 9),    # 7±2 软
    "long-doc-claude":  (5, 80),   # 长篇研究报告（管理层讨论稿场景，60-70 页常见），上限放宽
    "portfolio":        (4, 8),    # 6±2 软
}


def _lazy_import():
    """延迟导入 weasyprint（重量级依赖），让本模块可在 CI 中 import 而不必先装它"""
    from weasyprint import HTML
    from pypdf import PdfReader
    return HTML, PdfReader


# ── 公共 API ────────────────────────────────────────────────────────────

def render_html(html_text: str, base_url: str, out_path: str) -> dict:
    """把完整 HTML 字符串渲染成 PDF。

    Args:
        html_text:  完整 HTML（含 <!DOCTYPE html> 和 <html>）
        base_url:   解析 @font-face url(../fonts/...) 等相对路径的基点；
                    通常传 templates/kami/ 的绝对路径
        out_path:   PDF 输出路径

    Returns:
        { "path": str, "pages": int, "size_bytes": int }
    """
    HTML, PdfReader = _lazy_import()
    HTML(string=html_text, base_url=base_url).write_pdf(out_path)
    pages = len(PdfReader(out_path).pages)
    return {
        "path": out_path,
        "pages": pages,
        "size_bytes": Path(out_path).stat().st_size,
    }


def render_template(
    doc_type: str,
    language: str,
    body_html: str | None,
    slots: dict[str, Any] | None,
    out_path: str,
    base_url: str | None = None,
) -> dict:
    """加载 templates/kami/{doc_type}[-en].html，用 body_html 或 slots 填入后渲染。

    两种填充模式（二选一）：
      - body_html: 直接替换整个 <body>...</body> 的内容
      - slots: {key: value} 替换模板里的 {{key}} 占位符（简单字符串替换，非完整 Jinja）

    两者都不传时使用模板原样（只验证渲染链路）。

    Args:
        doc_type: one-pager / long-doc / long-doc-claude / letter / portfolio / resume
        language: 'zh' or 'en'
        body_html: 替换整个 body innerHTML（优先级最高）
        slots: {{key}} 占位符字典（当 body_html 未提供时使用）
        out_path: PDF 输出路径
        base_url: WeasyPrint 解析相对路径的基点。
                  - None（默认）：用 templates/kami/ 路径（适合模板自带资源）
                  - 自定义路径：当 body_html 中引用了项目本地图片时（如长文报告
                    包含 ./images/fig_*.png），传入项目目录绝对路径，确保图片能加载
    """
    if doc_type not in DOC_TYPES:
        raise ValueError(
            f"不支持的 doc_type: {doc_type}。可选: {sorted(DOC_TYPES)}"
        )
    lang = (language or "zh").lower()
    if lang not in {"zh", "en"}:
        raise ValueError(f"language 必须是 'zh' 或 'en'，got {language!r}")

    template_name = f"{doc_type}-en.html" if lang == "en" else f"{doc_type}.html"
    template_path = KAMI_DIR / template_name
    if not template_path.exists():
        # 优雅降级：long-doc-claude-en.html 不存在时回退到 long-doc-en.html
        # （Claude 皮肤目前仅 zh，但 long-doc 的 en 模板可作为后备）
        if lang == "en" and doc_type.endswith("-claude"):
            base = doc_type.rsplit("-claude", 1)[0]
            fallback = KAMI_DIR / f"{base}-en.html"
            if fallback.exists():
                template_path = fallback
                template_name = fallback.name
            else:
                raise FileNotFoundError(f"模板不存在: {template_path}")
        else:
            raise FileNotFoundError(f"模板不存在: {template_path}")

    html = template_path.read_text(encoding="utf-8")

    # 两个填充阶段相互独立、可叠加：
    # 1. slots 先替换模板里的 {{文档标题}} 等占位符（@page 页脚 / <title> 等模板自带 slot）
    # 2. body_html 整段替换 <body>...</body> 内部
    if slots:
        html = _apply_slots(html, slots)
    if body_html is not None:
        html = _replace_body(html, body_html)

    effective_base = base_url if base_url is not None else str(KAMI_DIR)
    result = render_html(html, base_url=effective_base, out_path=out_path)
    result["doc_type"] = doc_type
    result["language"] = lang
    result["template"] = template_name

    # 页数约束校验（不报错，只附信息）
    limit = PAGE_LIMITS.get(doc_type)
    if limit:
        lo, hi = limit
        result["page_limit"] = [lo, hi]
        if result["pages"] > hi:
            result["warnings"] = result.get("warnings", []) + [
                f"页数 {result['pages']} 超出 {doc_type} 约束 ({lo}-{hi})；"
                "字体 fallback / 行高 / 字号稍动可能就爆"
            ]
        elif result["pages"] < lo:
            result["warnings"] = result.get("warnings", []) + [
                f"页数 {result['pages']} 低于 {doc_type} 约束 ({lo}-{hi})；内容过薄"
            ]
    return result


# ── 内部辅助 ────────────────────────────────────────────────────────────

_BODY_RE = re.compile(r"(<body[^>]*>)(.*?)(</body>)", re.DOTALL | re.IGNORECASE)


def _replace_body(html: str, new_body: str) -> str:
    """替换 <body>...</body> 的内容，保留 body 标签属性"""
    def repl(m: re.Match) -> str:
        return m.group(1) + "\n" + new_body + "\n" + m.group(3)

    result, n = _BODY_RE.subn(repl, html, count=1)
    if n == 0:
        raise ValueError("模板中找不到 <body>...</body>")
    return result


_SLOT_RE = re.compile(r"\{\{\s*([a-zA-Z_][a-zA-Z0-9_.-]*)\s*\}\}")


def _apply_slots(html: str, slots: dict[str, Any]) -> str:
    """简单 {{key}} 字符串替换，**不做 HTML 转义**——slot 值由 agent 负责预转义。
    缺失 key 保留 {{key}} 原样（方便 debug）。"""
    def repl(m: re.Match) -> str:
        key = m.group(1)
        if key in slots:
            return str(slots[key])
        return m.group(0)
    return _SLOT_RE.sub(repl, html)


# ── CLI ─────────────────────────────────────────────────────────────────

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--html", help="完整 HTML 文件路径")
    mode.add_argument("--template", choices=sorted(DOC_TYPES),
                      help="kami 模板类型")

    ap.add_argument("--lang", choices=["zh", "en"], default="zh",
                    help="语言（仅 --template 模式）")
    ap.add_argument("--body", help="body 内容 HTML 文件（仅 --template 模式）")
    ap.add_argument("--slots", help="JSON 文件，{{key}} 替换字典")
    ap.add_argument("--base-url", help="HTML 模式下解析相对路径的基点")
    ap.add_argument("--out", required=True, help="输出 PDF 路径")
    args = ap.parse_args()

    if args.html:
        html_text = Path(args.html).read_text(encoding="utf-8")
        base = args.base_url or str(Path(args.html).resolve().parent)
        result = render_html(html_text, base, args.out)
    else:
        body = Path(args.body).read_text(encoding="utf-8") if args.body else None
        slots = json.loads(Path(args.slots).read_text()) if args.slots else None
        result = render_template(
            args.template, args.lang, body, slots, args.out,
            base_url=args.base_url,
        )

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
