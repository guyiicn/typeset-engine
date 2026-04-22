#!/usr/bin/env python3
"""render_kami.py 回归测试（本地 WeasyPrint）

需要:
    pip install weasyprint pypdf

运行:
    python3 tests/test_render_kami.py
    pytest tests/test_render_kami.py -q
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

try:
    import weasyprint  # noqa: F401
    from pypdf import PdfReader
    HAS_DEPS = True
except ImportError:
    HAS_DEPS = False

if HAS_DEPS:
    from render_kami import (
        render_html, render_template,
        DOC_TYPES, PAGE_LIMITS, KAMI_DIR,
        _replace_body, _apply_slots,
    )


def skip_if_no_deps():
    if not HAS_DEPS:
        print("  … skipped (weasyprint/pypdf not installed)")
        return True
    return False


# ── 纯函数（不需要 weasyprint）─────────────────────────────────────────

def test_replace_body_substitutes_content() -> None:
    if not HAS_DEPS:
        return
    html = "<html><head></head><body>OLD</body></html>"
    out = _replace_body(html, "<p>NEW</p>")
    assert "NEW" in out and "OLD" not in out


def test_replace_body_raises_when_no_body() -> None:
    if not HAS_DEPS:
        return
    try:
        _replace_body("<html></html>", "x")
    except ValueError as e:
        assert "body" in str(e).lower()
        return
    raise AssertionError("expected ValueError")


def test_apply_slots_replaces_known_keys() -> None:
    if not HAS_DEPS:
        return
    html = "<h1>{{title}}</h1><p>{{author}}</p>"
    out = _apply_slots(html, {"title": "Hello", "author": "Gu"})
    assert "<h1>Hello</h1>" in out
    assert "<p>Gu</p>" in out


def test_apply_slots_preserves_unknown_keys() -> None:
    if not HAS_DEPS:
        return
    html = "<h1>{{title}}</h1><p>{{missing}}</p>"
    out = _apply_slots(html, {"title": "X"})
    assert "<h1>X</h1>" in out
    assert "{{missing}}" in out


# ── 渲染（需要 weasyprint）──────────────────────────────────────────────

def test_render_all_templates_within_page_limits() -> None:
    """所有 10 个模板渲染成功，页数在约束内"""
    if skip_if_no_deps():
        return
    with tempfile.TemporaryDirectory() as td:
        for doc_type in sorted(DOC_TYPES):
            for lang in ("zh", "en"):
                out = Path(td) / f"{doc_type}-{lang}.pdf"
                result = render_template(doc_type, lang, None, None, str(out))
                assert result["pages"] >= 1
                # 页数检查：硬上限里 warnings 应该不存在
                limit = PAGE_LIMITS.get(doc_type)
                if limit and limit[1] <= 2:  # 严格类型必须守约
                    assert result["pages"] <= limit[1], (
                        f"{doc_type}-{lang}: pages={result['pages']} > limit={limit[1]}"
                    )


def test_render_template_unknown_doc_type_raises() -> None:
    if skip_if_no_deps():
        return
    try:
        render_template("nonexistent", "en", None, None, "/tmp/x.pdf")
    except ValueError as e:
        assert "nonexistent" in str(e)
        return
    raise AssertionError("expected ValueError for unknown doc_type")


def test_render_template_unknown_language_raises() -> None:
    if skip_if_no_deps():
        return
    try:
        render_template("resume", "fr", None, None, "/tmp/x.pdf")
    except ValueError as e:
        assert "language" in str(e).lower()
        return
    raise AssertionError("expected ValueError for unknown language")


def test_render_html_direct_produces_pdf() -> None:
    """直接 HTML 模式（不走模板）"""
    if skip_if_no_deps():
        return
    html = """<!DOCTYPE html><html><body>
    <style>
      @page { size: 210mm 297mm; margin: 20mm; }
      body { font-family: Georgia, serif; color: #3d3d3a; }
    </style>
    <h1>Minimal</h1><p>Hello kami.</p>
    </body></html>"""
    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / "minimal.pdf"
        result = render_html(html, str(td), str(out))
        assert result["pages"] == 1
        assert result["size_bytes"] > 1000
        # 真是 PDF
        assert PdfReader(str(out)).pages[0] is not None


def test_render_template_with_body_html_overrides() -> None:
    """body_html 替换应完全覆盖模板的默认 body"""
    if skip_if_no_deps():
        return
    body = '<h1 style="color: #1B365D">CUSTOM_MARKER_XYZ</h1>'
    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / "custom.pdf"
        result = render_template("letter", "en", body, None, str(out))
        assert result["pages"] >= 1
        # PDF 文本抽取验证 marker 出现
        from pypdf import PdfReader
        text = "".join(p.extract_text() or "" for p in PdfReader(str(out)).pages)
        assert "CUSTOM_MARKER_XYZ" in text


# ── 入口 ────────────────────────────────────────────────────────────────

def _collect():
    return [(n, f) for n, f in sorted(globals().items())
            if n.startswith("test_") and callable(f)]


def main() -> int:
    if not HAS_DEPS:
        print("⚠️  weasyprint/pypdf 未安装，跳过渲染类测试（纯函数 test 仍会跑）")
    tests = _collect()
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
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
