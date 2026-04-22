#!/usr/bin/env python3
"""validate_kami.py 回归测试

覆盖 kami 9 条约束的每条规则 + 豁免逻辑 + 输出格式。

运行:
    python3 tests/test_validate_kami.py            # 直接跑，打印 pass/fail
    pytest tests/test_validate_kami.py -q          # 用 pytest 跑
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Iterable

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "validate_kami.py"


# ── 工具 ────────────────────────────────────────────────────────────────

def scan(content: str, filename: str = "case.html",
         only: Iterable[str] | None = None) -> dict:
    """把 content 写到临时文件，用 validate_kami.py --format json 扫描，返回解析后的 dict。"""
    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / filename
        path.write_text(content, encoding="utf-8")
        args = [sys.executable, str(SCRIPT), "--format", "json", str(path)]
        if only:
            args += ["--only", ",".join(only)]
        result = subprocess.run(args, capture_output=True, text=True, timeout=30)
        # 退出码 0 = 干净，1 = 有 error，2 = 内部错。JSON 模式都应正常 JSON
        assert result.returncode in (0, 1), (
            f"validate_kami exit={result.returncode}\nstderr={result.stderr}"
        )
        return json.loads(result.stdout)


def rules_hit(report: dict) -> list[str]:
    return sorted({i["rule"] for i in report["issues"]})


# ── 测试用例 ────────────────────────────────────────────────────────────

def test_clean_template_has_no_issues() -> None:
    html = """
    <style>
      @page { size: 210mm 297mm; margin: 18mm 16mm; }
      body { background: #f5f4ed; color: #3d3d3a; font-weight: 500; line-height: 1.5; }
      .card { background: #faf9f5; box-shadow: 0 1px 2px rgba(20, 20, 19, 0.04); }
      .tag { background: #e8e6df; color: #4d4c48; }
    </style>
    <div>hello</div>
    """
    report = scan(html)
    assert report["total"] == 0, report


def test_rgba_in_tag_selector_is_error() -> None:
    html = """
    <style>.tag { background: rgba(20, 20, 19, 0.08); }</style>
    """
    report = scan(html, only=["rgba"])
    assert report["errors"] == 1
    assert rules_hit(report) == ["rgba"]


def test_cool_gray_is_error() -> None:
    css = ".x { color: #8C8C8C; background: #e5e7eb; border-color: #6b7280; }"
    report = scan(css, filename="case.css", only=["coolgray"])
    assert report["errors"] == 3
    # 所有三个都应命中
    matched = {i["match"].lower() for i in report["issues"]}
    assert matched == {"#8c8c8c", "#e5e7eb", "#6b7280"}


def test_warm_gray_is_ok() -> None:
    """#87867f / #5e5d59 / #4d4c48 / #3d3d3a 是推荐暖灰，不应告警"""
    css = ".x { color: #87867f; background: #3d3d3a; border: 1pt solid #5e5d59; }"
    report = scan(css, filename="case.css", only=["coolgray"])
    assert report["total"] == 0, report


def test_pure_white_background_is_warning() -> None:
    css = "body { background: #ffffff; }"
    report = scan(css, filename="case.css", only=["white"])
    assert report["warnings"] == 1
    assert report["errors"] == 0


def test_line_height_too_loose_is_error() -> None:
    css = ".paragraph { line-height: 1.8; }"
    report = scan(css, filename="case.css", only=["lineheight"])
    assert report["errors"] == 1
    assert "1.8" in report["issues"][0]["message"]


def test_line_height_1_55_is_ok() -> None:
    css = ".paragraph { line-height: 1.55; }"
    report = scan(css, filename="case.css", only=["lineheight"])
    assert report["total"] == 0


def test_bold_serif_is_warning() -> None:
    css = "h1 { font-family: 'Newsreader', serif; font-weight: bold; }"
    report = scan(css, filename="case.css", only=["boldserif"])
    assert report["warnings"] == 1


def test_bold_sans_is_ok() -> None:
    """sans 元素允许更重字重（cover 大标题例外）"""
    css = ".label { font-family: 'Inter', sans-serif; font-weight: 700; }"
    report = scan(css, filename="case.css", only=["boldserif"])
    assert report["total"] == 0, report


def test_hard_drop_shadow_is_warning() -> None:
    css = ".card { box-shadow: 4px 4px 8px rgba(0, 0, 0, 0.3); }"
    report = scan(css, filename="case.css", only=["hardshadow"])
    assert report["warnings"] == 1


def test_whisper_shadow_is_ok() -> None:
    css = ".card { box-shadow: 0 1px 2px rgba(20, 20, 19, 0.04); }"
    report = scan(css, filename="case.css", only=["hardshadow"])
    assert report["total"] == 0


def test_ring_shadow_is_ok() -> None:
    css = ".card { box-shadow: 0 0 0 1px rgba(20, 20, 19, 0.08); }"
    report = scan(css, filename="case.css", only=["hardshadow"])
    assert report["total"] == 0


def test_thin_border_with_radius_is_warning() -> None:
    css = ".card { border: 0.5px solid #ddd; border-radius: 8px; }"
    report = scan(css, filename="case.css", only=["thinborder"])
    assert report["warnings"] == 1


def test_thick_border_with_radius_is_ok() -> None:
    css = ".card { border: 1pt solid #e0ddd4; border-radius: 8px; }"
    report = scan(css, filename="case.css", only=["thinborder"])
    assert report["total"] == 0


def test_100vh_in_page_context_is_warning() -> None:
    css = """
    @page { size: A4; }
    .page { height: 100vh; }
    """
    report = scan(css, filename="case.css", only=["vh"])
    assert report["warnings"] == 1


def test_100vh_without_page_context_is_ok() -> None:
    css = ".app { height: 100vh; }"
    report = scan(css, filename="case.css", only=["vh"])
    assert report["total"] == 0


def test_flex_with_break_inside_is_warning() -> None:
    """WeasyPrint 68+ 已修复此行为，降级为 warning"""
    css = ".row { display: flex; break-inside: avoid; }"
    report = scan(css, filename="case.css", only=["flexbreak"])
    assert report["warnings"] == 1
    assert report["errors"] == 0


def test_doc_context_is_skipped() -> None:
    """注释中讨论禁用颜色不应被 flag"""
    css = """
    /* 禁用 #8c8c8c 因为太冷 */
    .x { color: #3d3d3a; }
    """
    report = scan(css, filename="case.css")
    assert report["total"] == 0


def test_legacy_themes_typ_coolgray_exempt() -> None:
    """themes.typ 是现有 9 主题的源头，按 2026-04-22 决定走 legacy 豁免。
    新加的 kami theme 不在此豁免名单。"""
    content = 'text-primary: rgb("#333333"), text-secondary: rgb("#666666")'
    report = scan(content, filename="themes.typ", only=["coolgray"])
    assert report["total"] == 0


def test_new_kami_theme_not_exempt() -> None:
    """同样的冷灰如果出现在新模板里，必须被 flag（没豁免）"""
    content = '.card { color: #333333; }'
    report = scan(content, filename="kami-one-pager.html", only=["coolgray"])
    assert report["errors"] == 1


def test_render_pdf_coolgray_exempt() -> None:
    """render_pdf.py 内联 CSS 继承 themes 风格，豁免"""
    content = 'STYLE = "body { color: #333333; }"'
    report = scan(content, filename="render_pdf.py", only=["coolgray"])
    assert report["total"] == 0


def test_gongwen_typ_is_whitelisted() -> None:
    """公文模板走国标，bold 豁免（其他规则仍生效）"""
    content = """
    #set text(font: "方正小标宋", weight: "bold")
    #let accent = rgb("#8c8c8c")
    """
    report = scan(content, filename="gongwen.typ")
    # boldserif 豁免，但 coolgray 不豁免
    rules = rules_hit(report)
    assert "boldserif" not in rules
    assert "coolgray" in rules


def test_self_skip_validate_kami() -> None:
    """validate_kami.py 自身不被扫（避免 COOL_GRAYS 字面量自命中）"""
    content = """COOL_GRAYS = {"#8c8c8c", "#999999"}"""
    report = scan(content, filename="validate_kami.py")
    assert report["total"] == 0


def test_only_filter_respected() -> None:
    """--only rgba 不应报 coolgray"""
    css = ".tag { background: rgba(0,0,0,.1); } .x { color: #999999; }"
    report = scan(css, filename="case.css", only=["rgba"])
    assert all(i["rule"] == "rgba" for i in report["issues"])


def test_typst_rgb_pure_white_warned() -> None:
    """Typst 语法 rgb(\"#fff\") 在 page fill 也应被 white 规则捕获"""
    content = '#set page(fill: rgb("#ffffff"))'
    report = scan(content, filename="theme.typ", only=["white"])
    assert report["warnings"] >= 1


def test_exit_code_1_on_errors() -> None:
    """有 error 时退出码应为 1（非 JSON 模式）"""
    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / "case.css"
        path.write_text(".x { color: #8C8C8C; }")
        result = subprocess.run(
            [sys.executable, str(SCRIPT), str(path)],
            capture_output=True, text=True, timeout=10,
        )
        assert result.returncode == 1


def test_exit_code_0_on_clean() -> None:
    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / "case.css"
        path.write_text(".x { color: #3d3d3a; }")
        result = subprocess.run(
            [sys.executable, str(SCRIPT), str(path)],
            capture_output=True, text=True, timeout=10,
        )
        assert result.returncode == 0


# ── 直接执行入口 ────────────────────────────────────────────────────────

def _collect_tests():
    return [(name, obj) for name, obj in sorted(globals().items())
            if name.startswith("test_") and callable(obj)]


def main() -> int:
    tests = _collect_tests()
    passed, failed = 0, []
    for name, fn in tests:
        try:
            fn()
            print(f"  ✓ {name}")
            passed += 1
        except AssertionError as e:
            print(f"  ✗ {name}  — {e}")
            failed.append(name)
        except Exception as e:  # noqa: BLE001
            print(f"  ✗ {name}  — [{type(e).__name__}] {e}")
            failed.append(name)

    print(f"\n{passed}/{len(tests)} passed, {len(failed)} failed")
    if failed:
        print("Failed:", ", ".join(failed))
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
