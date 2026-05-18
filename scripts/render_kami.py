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
# long-doc-claude   = long-doc 的 Anthropic/Claude 烧橙皮肤变体（触发词"claude 风格"）
# long-doc-openai   = long-doc 的 OpenAI 极简白底+绿强调皮肤变体（触发词"openai 风格"）
# long-doc-starwars = long-doc 的 Star Wars 戏剧化皮肤变体（深空 + 标志黄；触发词"星球大战风格"）
DOC_TYPES = {
    "one-pager", "long-doc",
    "long-doc-claude", "long-doc-openai", "long-doc-starwars",
    "letter", "portfolio", "resume",
    "founders-playbook",  # 创始人指南
}

# 每个 doc_type 的页数硬约束（见 design-constraints 第 5 节）
PAGE_LIMITS = {
    "resume":             (1, 2),    # 严格 ≤2
    "one-pager":          (1, 1),    # 严格 = 1
    "letter":             (1, 1),    # 严格 = 1
    "long-doc":           (5, 9),    # 7±2 软
    "long-doc-claude":    (5, 80),   # 长篇研究报告（管理层讨论稿场景，60-70 页常见），上限放宽
    "long-doc-openai":    (5, 100),  # OpenAI 极简风格长文（执行概要 + 多案例 + 方向 + 附录），上限放至 100
    "long-doc-starwars":  (5, 80),   # Star Wars 戏剧化风格（封面+扉页深空底，正文米白）
    "portfolio":          (4, 8),    # 6±2 软
    "founders-playbook":  (10, 40),  # 创始人指南（封面+目录+N 章节）
}

# ── founders-playbook 数据驱动渲染 ─────────────────────────────────────

# 章节扉页 7 色循环
FPB_COLORS = [
    '#D36F53',  # coral
    '#5F9B89',  # teal
    '#8C77D1',  # purple
    '#BBD1C9',  # mint
    '#CAC9DB',  # lavender
    '#EFD4C6',  # peach
    '#AFADA4',  # warm gray
]

# 扉页 SVG Logo（Claude 太阳花）
_LOGO_SVG = (
    '<svg style="position:absolute;left:54pt;top:528pt;width:40pt;height:40pt;" viewBox="0 0 40 40">'
    '<circle cx="20" cy="20" r="3" fill="#141413"/>'
    '<g fill="#141413">'
    '<ellipse cx="20" cy="5" rx="4" ry="12" transform="rotate(0 20 20)"/>'
    '<polygon points="20,0 22,10 18,10" transform="rotate(30 20 20)"/>'
    '<ellipse cx="20" cy="5" rx="4" ry="12" transform="rotate(60 20 20)"/>'
    '<polygon points="20,0 22,10 18,10" transform="rotate(90 20 20)"/>'
    '<ellipse cx="20" cy="5" rx="4" ry="12" transform="rotate(120 20 20)"/>'
    '<polygon points="20,0 22,10 18,10" transform="rotate(150 20 20)"/>'
    '<ellipse cx="20" cy="5" rx="4" ry="12" transform="rotate(180 20 20)"/>'
    '<polygon points="20,0 22,10 18,10" transform="rotate(210 20 20)"/>'
    '<ellipse cx="20" cy="5" rx="4" ry="12" transform="rotate(240 20 20)"/>'
    '<polygon points="20,0 22,10 18,10" transform="rotate(270 20 20)"/>'
    '<ellipse cx="20" cy="5" rx="4" ry="12" transform="rotate(300 20 20)"/>'
    '<polygon points="20,0 22,10 18,10" transform="rotate(330 20 20)"/>'
    '</g></svg>'
)


def _build_fpb_html(slots: dict) -> str:
    """根据 slots 数据生成 founders-playbook 完整 HTML body 内容。

    Args:
        slots: {
            "title": str,
            "subtitle": str,
            "mode": "full" | "minimal" | "plain" (默认 "full"),
            "chapters": [
                {"number": int, "title": str, "mode": ..., "body": "<p>...</p>"},
                ...
            ],
        }

    Returns:
        完整 HTML body 内容（不含 <body> 标签，由外部包裹）
    """
    global_mode = slots.get("mode", "full")
    title = slots.get("title", "")
    subtitle = slots.get("subtitle", "")
    chapters = slots.get("chapters", [])

    parts: list[str] = []

    # 封面
    parts.append(
        f'<div class="page" style="position:relative;width:792pt;height:612pt;background:#D36F53;">'
        f'<div class="serif" style="position:absolute;left:54pt;top:110pt;font-size:56pt;color:#141413;line-height:62pt;">{title}</div>'
        f'<div class="serif" style="position:absolute;left:54pt;top:172pt;font-size:56pt;color:#141413;line-height:62pt;">{subtitle}</div>'
        f'{_LOGO_SVG}'
        f'<svg style="position:absolute;left:94pt;top:531pt;width:113pt;height:26pt;" viewBox="0 0 113 26">'
        f'<text x="0" y="20" font-family="Georgia,serif" font-size="22pt" fill="#141413">Claude</text>'
        f'</svg></div>'
    )

    # 目录
    toc_items = []
    for ch in chapters:
        toc_items.append(
            f'<tr><td style="padding:4pt 0;">{ch["title"]}</td>'
            f'<td style="text-align:right;padding:4pt 0;width:40pt;">{ch.get("number", "?")}</td></tr>'
        )
    parts.append(
        f'<div class="page" style="position:relative;width:792pt;height:612pt;background:#fff;">'
        f'<div class="serif" style="position:absolute;left:54pt;top:84pt;font-size:30pt;color:#0b0b0b;">Contents</div>'
        f'<table style="position:absolute;left:54pt;top:138pt;width:684pt;font-family:Noto Sans CJK SC,sans-serif;font-size:12pt;color:#0b0b0b;">'
        f'{"".join(toc_items)}'
        f'</table>'
        f'<div class="sans" style="position:absolute;right:60pt;bottom:30pt;font-size:7pt;color:#231f20;">2</div>'
        f'</div>'
    )

    # 章节
    for i, ch in enumerate(chapters):
        mode = ch.get("mode", global_mode)
        number = ch.get("number", i + 1)
        ch_title = ch.get("title", "")
        ch_body = ch.get("body", "")
        color = FPB_COLORS[i % 7]

        if mode == "full":
            # 扉页
            parts.append(
                f'<div class="page" style="position:relative;width:792pt;height:612pt;background:{color};">'
                f'<rect x="0" y="0" width="792" height="612" fill="{color}"/>'
                f'<rect x="54.25" y="418.6" width="68" height="19.15" rx="9.5" stroke="#141413" stroke-width="1.5" fill="none"/>'
                f'<div class="sans" style="position:absolute;left:63pt;top:484pt;font-size:11pt;color:#0b0b0b;">Chapter {number}</div>'
                f'<div class="serif" style="position:absolute;left:54pt;top:506pt;font-size:48pt;color:#0b0b0b;line-height:52pt;">{ch_title}</div>'
                f'<div class="sans" style="position:absolute;right:60pt;bottom:30pt;font-size:7pt;color:#231f20;">{3 + i * 2}</div>'
                f'</div>'
            )
            # 正文
            parts.append(
                f'<div class="page" style="position:relative;width:792pt;height:612pt;background:#fff;">'
                f'<div class="serif" style="position:absolute;left:54pt;top:118pt;font-size:30pt;color:#0b0b0b;">{ch_title}</div>'
                f'<div class="serif" style="position:absolute;left:54pt;top:160pt;width:354pt;font-size:9pt;color:#0b0b0b;line-height:12.9pt;">'
                f'{ch_body}'
                f'</div></div>'
            )
        elif mode == "minimal":
            # 只有标题页（白色背景，无彩色）
            parts.append(
                f'<div class="page" style="position:relative;width:792pt;height:612pt;background:#fff;">'
                f'<div class="serif" style="position:absolute;left:54pt;top:200pt;font-size:48pt;color:#0b0b0b;line-height:52pt;">{ch_title}</div>'
                f'<div class="sans" style="position:absolute;left:63pt;top:484pt;font-size:11pt;color:#0b0b0b;">Chapter {number}</div>'
                f'</div>'
            )
            parts.append(
                f'<div class="page" style="position:relative;width:792pt;height:612pt;background:#fff;">'
                f'<div class="serif" style="position:absolute;left:54pt;top:118pt;font-size:30pt;color:#0b0b0b;">{ch_title}</div>'
                f'<div class="serif" style="position:absolute;left:54pt;top:160pt;width:354pt;font-size:9pt;color:#0b0b0b;line-height:12.9pt;">'
                f'{ch_body}'
                f'</div></div>'
            )
        elif mode == "plain":
            # 只有正文
            parts.append(
                f'<div class="page" style="position:relative;width:792pt;height:612pt;background:#fff;">'
                f'<div class="serif" style="position:absolute;left:54pt;top:50pt;font-size:30pt;color:#0b0b0b;">{ch_title}</div>'
                f'<div class="serif" style="position:absolute;left:54pt;top:100pt;width:354pt;font-size:9pt;color:#0b0b0b;line-height:12.9pt;">'
                f'{ch_body}'
                f'</div></div>'
            )

    # 封底
    parts.append(
        '<div class="page" style="position:relative;width:792pt;height:612pt;background:#D36F53;">'
        '<div class="sans" style="position:absolute;right:110pt;bottom:55pt;font-size:13pt;color:#fff;">claude.ai</div>'
        '</div>'
    )

    return '\n'.join(parts)


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
        doc_type: one-pager / long-doc / long-doc-claude / long-doc-openai / letter / portfolio / resume
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
        # 优雅降级：皮肤变体（-claude / -openai）的 -en.html 不存在时回退到 long-doc-en.html
        # （皮肤变体目前仅 zh，但 long-doc 的 en 模板可作为后备）
        if lang == "en" and any(s in doc_type for s in ("-claude", "-openai", "-starwars")):
            for suffix in ("-claude", "-openai", "-starwars"):
                if doc_type.endswith(suffix):
                    base = doc_type.rsplit(suffix, 1)[0]
                    fallback = KAMI_DIR / f"{base}-en.html"
                    if fallback.exists():
                        template_path = fallback
                        template_name = fallback.name
                        break
            else:
                raise FileNotFoundError(f"模板不存在: {template_path}")
            if not template_path.exists():
                raise FileNotFoundError(f"模板不存在: {template_path}")
        else:
            raise FileNotFoundError(f"模板不存在: {template_path}")

    html = template_path.read_text(encoding="utf-8")

    # ── founders-playbook: 数据驱动渲染 ──────────────────────────────
    # 这个模板不是简单的 {{key}} 替换，而是用 Python 生成完整 body HTML
    if doc_type == "founders-playbook":
        if slots is None:
            slots = {}
        body_html = _build_fpb_html(slots)
        # 把生成的 body 注入模板骨架
        html = _replace_body(html, body_html)
        effective_base = base_url if base_url is not None else str(KAMI_DIR)
        result = render_html(html, base_url=effective_base, out_path=out_path)
        result["doc_type"] = doc_type
        result["language"] = lang
        result["template"] = template_name
        limit = PAGE_LIMITS.get(doc_type)
        if limit:
            lo, hi = limit
            result["page_limit"] = [lo, hi]
        return result

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
