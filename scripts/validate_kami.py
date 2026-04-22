#!/usr/bin/env python3
"""
validate_kami.py — Kami 美学宪法扫描器（typeset-engine）

检查 typeset-engine 的模板、内联 CSS、Python 渲染器是否违反
~/.openclaw/skills/typeset-engine/references/design-constraints.md 里的 9 条铁律。

扫描目标（默认）：
    templates/**/*.html  .typ  .css
    scripts/*.py         （内联 CSS）

使用：
    python3 scripts/validate_kami.py                          # 全量扫描
    python3 scripts/validate_kami.py templates/cicc-report.typ
    python3 scripts/validate_kami.py -v                       # 带上下文
    python3 scripts/validate_kami.py --format json            # CI 可读
    python3 scripts/validate_kami.py --only rgba,coolgray     # 只跑子集
    python3 scripts/validate_kami.py --all                    # 也扫 styles/ (AI 插画风格)

返回码：
    0  无 error
    1  至少一条 error
    2  内部错误 / 参数错
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable, Iterable

ROOT = Path(__file__).resolve().parent.parent

DEFAULT_GLOBS = [
    "templates/**/*.html",
    "templates/**/*.typ",
    "templates/**/*.css",
    "scripts/*.py",
]

EXTENDED_GLOBS = DEFAULT_GLOBS + ["styles/**/*.md"]

# 路径片段黑名单——任意包含这些 segment 的文件都跳过（测试 fixture 常含有意违规）
SKIP_PATH_SEGMENTS = ("/tests/", "/test_output/", "/.venv/", "/__pycache__/")

# 公文模板走国家规范，不走暖调美学
WHITELISTED_FILES = {"gongwen.typ"}

# 验证器自身不扫（否则 COOL_GRAYS 字面量会触发自己）
SELF_SKIP = {"validate_kami.py", "validate_docx.py"}

# 现有主题和渲染器的 legacy 冷灰豁免。
# 2026-04-22 决定（用户选项 d）：不改现有 cicc/ms/cms/dachen 主题的中性色；
# 新加的 kami theme（templates/kami/*）会严格执行全部 9 条规则。
# 如果要将某个现有主题迁移到暖调系统，从此 set 里移除对应文件即可。
COOLGRAY_LEGACY_EXEMPT = {
    "themes.typ",        # 9 主题中性色 token 的源头
    "cicc-report.typ",   # 继承 themes.typ
    "render_pdf.py",     # 内联 CSS 继承主题风格
    "render_charts.py",  # 图表调色板继承主题
}

# 一行里出现这些词就视为"在讨论规则本身"（非真实使用）
DOC_MARKERS = (
    "禁用", "禁止", "不要用", "反例", "示例", "例：",  "例如", "例子",
    "slop", "bad example", "for example", "example:",
    "forbidden", "blocklist", "banned", "don't use",
)

# ── 色板黑名单 ──────────────────────────────────────────────────────────

COOL_GRAYS = {
    # 纯冷灰（R==G==B）
    "#8c8c8c", "#999999", "#a0a0a0", "#666666", "#333333",
    "#808080", "#b0b0b0", "#c0c0c0", "#d0d0d0", "#e0e0e0",
    # Tailwind gray
    "#f3f4f6", "#e5e7eb", "#d1d5db", "#9ca3af",
    "#6b7280", "#4b5563", "#374151", "#1f2937", "#111827",
    # Tailwind slate（冷蓝灰）
    "#f1f5f9", "#e2e8f0", "#cbd5e1", "#94a3b8",
    "#64748b", "#475569", "#334155", "#1e293b", "#0f172a",
    # Tailwind zinc（偏冷）
    "#a1a1aa", "#71717a", "#52525b",
}


# ── Issue 数据模型 ─────────────────────────────────────────────────────

@dataclass
class Issue:
    severity: str      # "error" | "warning"
    rule: str
    file: str
    line: int
    col: int
    match: str
    message: str
    context: str = ""


ISSUES: list[Issue] = []


def add(severity: str, rule: str, path: Path, offset: int, text: str,
        match: str, message: str) -> None:
    line, col = _pos(text, offset)
    ctx = _line_at(text, line)
    if _is_doc_context(ctx):
        return
    ISSUES.append(Issue(
        severity=severity, rule=rule,
        file=str(path), line=line, col=col,
        match=match, message=message, context=ctx,
    ))


# ── 辅助 ────────────────────────────────────────────────────────────────

def _pos(text: str, offset: int) -> tuple[int, int]:
    line = text.count("\n", 0, offset) + 1
    col = offset - (text.rfind("\n", 0, offset) + 1) + 1
    return line, col


def _line_at(text: str, lineno: int) -> str:
    lines = text.splitlines()
    if 1 <= lineno <= len(lines):
        return lines[lineno - 1].strip()
    return ""


def _is_doc_context(line_text: str) -> bool:
    lower = line_text.lower()
    return any(marker.lower() in lower for marker in DOC_MARKERS)


def _normalize_hex(h: str) -> str:
    h = h.lower()
    if len(h) == 4:  # #abc → #aabbcc
        c = h[1:]
        h = "#" + c[0] * 2 + c[1] * 2 + c[2] * 2
    return h


# ── 规则实现 ────────────────────────────────────────────────────────────

def rule_rgba_in_tag(path: Path, text: str) -> None:
    """约束 7：.tag / .badge / .chip / .pill / .label 禁用 rgba() 底色"""
    if path.suffix not in {".html", ".css", ".md", ".py"}:
        return

    tag_selectors = re.compile(r"\.(tag|badge|chip|pill|label)\b", re.I)
    rgba_re = re.compile(r"\brgba\s*\([^)]+\)", re.I)

    for m in rgba_re.finditer(text):
        back = text[max(0, m.start() - 250): m.start()]
        if tag_selectors.search(back):
            add("error", "rgba", path, m.start(), text, m.group(),
                "rgba() 在 tag/badge 选择器上触发 WeasyPrint 双矩形 bug；"
                "必须预合成成实色 hex")


def rule_cool_gray(path: Path, text: str) -> None:
    """约束 3：中性色必须暖调，禁冷灰"""
    if path.name in COOLGRAY_LEGACY_EXEMPT:
        return
    for m in re.finditer(r"#[0-9a-fA-F]{3}\b|#[0-9a-fA-F]{6}\b", text):
        if _normalize_hex(m.group()) in COOL_GRAYS:
            add("error", "coolgray", path, m.start(), text, m.group(),
                f"冷灰 {m.group()} 在 print 下偏蓝；"
                "替换为 #87867f / #5e5d59 / #4d4c48 / #3d3d3a")


def rule_pure_white(path: Path, text: str) -> None:
    """约束 1：画布/背景禁纯白（#fff / #ffffff）"""
    patterns = [
        (re.compile(r"background(?:-color)?\s*:\s*(#[fF]{6}|#[fF]{3})\b"), "css"),
        (re.compile(r'\bfill\s*:\s*rgb\(\s*"(#[fF]{6}|#[fF]{3})"\s*\)'), "typst"),
        (re.compile(r'\bpage\s*\([^)]*fill\s*:\s*rgb\(\s*"(#[fF]{6}|#[fF]{3})"\s*\)'), "typst-page"),
    ]
    for pat, _ in patterns:
        for m in pat.finditer(text):
            add("warning", "white", path, m.start(), text, m.group(),
                "画布/背景禁纯白；改米纸 #f5f4ed 或象牙 #faf9f5")


def rule_line_height(path: Path, text: str) -> None:
    """约束 5：line-height 禁 ≥1.6"""
    if path.suffix not in {".html", ".css", ".md", ".py"}:
        return
    for m in re.finditer(r"line-height\s*:\s*([\d.]+)", text):
        try:
            val = float(m.group(1))
        except ValueError:
            continue
        if val >= 1.6:
            add("error", "lineheight", path, m.start(), text, m.group(),
                f"line-height {val} ≥ 1.6 违反编辑级密度（上限 1.55）")


def rule_bold_serif(path: Path, text: str) -> None:
    """约束 4：serif 字重锁 500，禁 bold / ≥700"""
    if path.name in WHITELISTED_FILES:
        return
    for m in re.finditer(r"font-weight\s*:\s*(bold|[7-9]00)\b", text, re.I):
        # 同一行/上方最近 200 字符提及 sans 则豁免（sans UI 允许更重）
        neighborhood = text[max(0, m.start() - 200): m.end() + 50].lower()
        if "sans" in neighborhood:
            continue
        add("warning", "boldserif", path, m.start(), text, m.group(),
            "font-weight ≥700 在 serif 上违反单字重签名（锁 500）")


def rule_hard_shadow(path: Path, text: str) -> None:
    """约束 6：禁 hard drop shadow（只允许 ring / whisper）"""
    pat = re.compile(r"box-shadow\s*:\s*([^;{}]+)", re.I)
    for m in pat.finditer(text):
        val = m.group(1)
        hard = False

        # rgba() alpha > 0.1 且有 ≥2px 偏移
        for r in re.finditer(
            r"rgba\s*\(\s*\d+\s*,\s*\d+\s*,\s*\d+\s*,\s*([\d.]+)\s*\)", val
        ):
            try:
                alpha = float(r.group(1))
            except ValueError:
                continue
            if alpha > 0.1 and re.search(r"\b([2-9]|\d{2,})\s*px", val):
                hard = True
                break

        # 纯 hex shadow + offset（没有 rgba 包装的通常都是 hard）
        if not hard and re.search(r"\b[2-9]\s*px[^,;]+#[0-9a-fA-F]{3,6}", val):
            hard = True

        if hard:
            add("warning", "hardshadow", path, m.start(), text, val.strip()[:80],
                "hard drop shadow 观感廉价；改 ring (0 0 0 1px rgba…,.08) "
                "或 whisper (0 1px 2px rgba…,.04)")


def rule_thin_border_radius(path: Path, text: str) -> None:
    """约束 8：border <1pt/px + border-radius → 双圈"""
    block_pat = re.compile(r"\{([^{}]*)\}", re.S)
    for bm in block_pat.finditer(text):
        block = bm.group(1)
        if "border-radius" not in block:
            continue
        thin = re.search(
            r"border(?:-(?:top|right|bottom|left))?\s*:\s*0?\.\d+\s*(?:pt|px)",
            block,
        )
        if thin:
            offset = bm.start(1) + thin.start()
            add("warning", "thinborder", path, offset, text, thin.group(),
                "border <1pt + border-radius 会出双圈；"
                "改 ≥1pt 或换用 ring shadow")


def rule_vh_in_page(path: Path, text: str) -> None:
    """约束 9：@page 下 height: 100vh 不准"""
    if "100vh" not in text or not re.search(r"@page\b", text):
        return
    for m in re.finditer(r"height\s*:\s*100vh\b", text):
        add("warning", "vh", path, m.start(), text, "100vh",
            "@page 上下文 height: 100vh 不准；改 mm 显式值（例 261mm = A4 − 2×18mm）")


def rule_flex_break_inside(path: Path, text: str) -> None:
    """约束 9：display:flex + break-inside:avoid 同块内历史上在 WeasyPrint 失效，
    需在外层 block wrapper 上声明。但 WeasyPrint 68+ 实测已修复此行为，
    故降级为 warning（提醒但不 block）。低版本部署环境需注意。"""
    block_pat = re.compile(r"\{([^{}]*)\}", re.S)
    for bm in block_pat.finditer(text):
        block = bm.group(1)
        has_flex = re.search(r"display\s*:\s*(?:inline-)?flex\b", block)
        has_break = re.search(r"break-inside\s*:\s*avoid\b", block)
        if has_flex and has_break:
            offset = bm.start(1) + has_break.start()
            add("warning", "flexbreak", path, offset, text,
                "break-inside+flex",
                "break-inside 在 flex 里 WeasyPrint <68 会失效；"
                "若部署用旧版请在外层 block wrapper 上声明 break-inside")


# ── 规则注册表 ──────────────────────────────────────────────────────────

RULES: dict[str, Callable[[Path, str], None]] = {
    "rgba":       rule_rgba_in_tag,
    "coolgray":   rule_cool_gray,
    "white":      rule_pure_white,
    "lineheight": rule_line_height,
    "boldserif":  rule_bold_serif,
    "hardshadow": rule_hard_shadow,
    "thinborder": rule_thin_border_radius,
    "vh":         rule_vh_in_page,
    "flexbreak":  rule_flex_break_inside,
}


# ── 扫描 ────────────────────────────────────────────────────────────────

def iter_files(targets: list[str], include_extended: bool) -> Iterable[Path]:
    globs = EXTENDED_GLOBS if include_extended else DEFAULT_GLOBS
    if not targets:
        for pat in globs:
            yield from ROOT.glob(pat)
        return
    for t in targets:
        p = Path(t)
        if not p.is_absolute():
            p = ROOT / p
        if p.is_file():
            yield p
        elif p.is_dir():
            for pat in globs:
                yield from p.rglob(pat.rsplit("/", 1)[-1])


# ── 输出 ────────────────────────────────────────────────────────────────

C_RED = "\033[31m"
C_YELLOW = "\033[33m"
C_GREEN = "\033[32m"
C_DIM = "\033[2m"
C_BOLD = "\033[1m"
C_RESET = "\033[0m"


def _supports_color() -> bool:
    return sys.stdout.isatty()


def print_text(verbose: bool, files_scanned: int) -> int:
    use_color = _supports_color()

    def c(code: str) -> str:
        return code if use_color else ""

    if not ISSUES:
        print(f"{c(C_GREEN)}✓ kami 约束扫描通过（{files_scanned} 文件）{c(C_RESET)}")
        return 0

    errors = [i for i in ISSUES if i.severity == "error"]
    warnings = [i for i in ISSUES if i.severity == "warning"]

    by_file: dict[str, list[Issue]] = {}
    for i in ISSUES:
        by_file.setdefault(i.file, []).append(i)

    for f, items in sorted(by_file.items()):
        try:
            rel = Path(f).relative_to(ROOT)
        except ValueError:
            rel = Path(f)
        print(f"\n{c(C_BOLD)}{rel}{c(C_RESET)}")
        for i in sorted(items, key=lambda x: (x.line, x.col)):
            color = C_RED if i.severity == "error" else C_YELLOW
            marker = "✗" if i.severity == "error" else "⚠"
            print(f"  {c(color)}{marker} {i.rule:11s}{c(C_RESET)} "
                  f"L{i.line}:{i.col}  {i.message}")
            if verbose:
                if i.context:
                    print(f"    {c(C_DIM)}{i.context[:120]}{c(C_RESET)}")
                if i.match and i.match != i.context:
                    print(f"    {c(C_DIM)}→ {i.match[:120]}{c(C_RESET)}")

    print(
        f"\n{c(C_BOLD)}汇总{c(C_RESET)}: "
        f"{c(C_RED)}{len(errors)} error{c(C_RESET)}, "
        f"{c(C_YELLOW)}{len(warnings)} warning{c(C_RESET)} "
        f"跨 {len(by_file)} 文件 / 扫描 {files_scanned} 文件"
    )
    return 1 if errors else 0


def print_json(files_scanned: int) -> int:
    errors = [i for i in ISSUES if i.severity == "error"]
    payload = {
        "files_scanned": files_scanned,
        "total": len(ISSUES),
        "errors": len(errors),
        "warnings": len(ISSUES) - len(errors),
        "issues": [asdict(i) for i in ISSUES],
    }
    json.dump(payload, sys.stdout, ensure_ascii=False, indent=2)
    print()
    return 1 if errors else 0


# ── 入口 ────────────────────────────────────────────────────────────────

def main() -> int:
    ap = argparse.ArgumentParser(
        description="Kami 美学宪法扫描器（typeset-engine）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    ap.add_argument("targets", nargs="*",
                    help="文件或目录（缺省扫 templates/ 和 scripts/）")
    ap.add_argument("-v", "--verbose", action="store_true",
                    help="每个违规输出上下文")
    ap.add_argument("--format", choices=["text", "json"], default="text",
                    help="输出格式")
    ap.add_argument("--only", default="",
                    help="逗号分隔规则子集，可选: " + ",".join(RULES))
    ap.add_argument("--all", action="store_true",
                    help="同时扫描 styles/*.md（AI 插画风格，默认跳过）")
    args = ap.parse_args()

    rules_to_run = (
        [r.strip() for r in args.only.split(",") if r.strip()]
        if args.only else list(RULES)
    )
    for r in rules_to_run:
        if r not in RULES:
            print(f"未知规则 '{r}'。可选: {', '.join(RULES)}", file=sys.stderr)
            return 2

    files_scanned = 0
    for path in iter_files(args.targets, include_extended=args.all):
        if not path.is_file():
            continue
        if path.name in SELF_SKIP:
            continue
        path_str = str(path.resolve()).replace("\\", "/") + "/"
        if any(seg in path_str for seg in SKIP_PATH_SEGMENTS):
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError as e:
            print(f"[skip] 读取失败 {path}: {e}", file=sys.stderr)
            continue
        for r in rules_to_run:
            try:
                RULES[r](path, text)
            except Exception as e:  # noqa: BLE001
                print(f"[internal] 规则 {r} 在 {path} 崩: {e}", file=sys.stderr)
        files_scanned += 1

    if args.format == "json":
        return print_json(files_scanned)
    return print_text(args.verbose, files_scanned)


if __name__ == "__main__":
    sys.exit(main())
