"""锁定 _apply_slots 支持 Unicode (中文) key 的行为.

历史 bug: _SLOT_RE = r'[a-zA-Z_][a-zA-Z0-9_.-]*' 只匹配 ASCII key.
模板里大量 {{文档标题}} {{中文标题}} {{副标题}} 等中文 key 永远不会被
替换, CSS @page @bottom-left 里的 {{文档标题}} 会以字面值出现在每页页脚.

修复后正则: r'[\\w.-]+?' (\\w 在 Python3 默认 Unicode-aware).

直接跑: python tests/test_kami_unicode_slots.py
"""
import os, sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from render_kami import _apply_slots, _SLOT_RE


def test_ascii_key():
    html = "Hello {{name}}!"
    assert _apply_slots(html, {"name": "world"}) == "Hello world!"


def test_chinese_key():
    """主修复点: 中文 key 必须能替换"""
    html = '<title>{{文档标题}}</title>'
    out = _apply_slots(html, {"文档标题": "投研报告"})
    assert out == '<title>投研报告</title>', f"got: {out!r}"


def test_multiple_chinese_keys():
    html = "标题: {{文档标题}} / 作者: {{作者}} / 日期: {{日期}}"
    out = _apply_slots(html, {
        "文档标题": "AI 多智能体协作",
        "作者": "Claude",
        "日期": "2026-05-19",
    })
    assert "AI 多智能体协作" in out
    assert "Claude" in out
    assert "2026-05-19" in out
    assert "{{" not in out


def test_mixed_ascii_and_chinese():
    html = "{{english_key}} + {{中文 key}} + {{a.b-c}} + {{副标题}}"
    out = _apply_slots(html, {
        "english_key": "EN",
        "副标题": "subtitle",
        "a.b-c": "DOTTED",
    })
    # english_key / a.b-c / 副标题 都应该被替换
    assert "EN" in out
    assert "DOTTED" in out
    assert "subtitle" in out
    # {{中文 key}} 含空格, 不算合法 key, 保留字面
    assert "{{中文 key}}" in out


def test_missing_key_preserved():
    """缺失 key 应该原样保留, 方便 debug"""
    html = "{{found}} {{未找到的}}"
    out = _apply_slots(html, {"found": "X"})
    assert out == "X {{未找到的}}"


def test_template_with_invalid_slot_examples():
    """模板里的注释类示例如 {{EYEBROW · 如 STRATEGIC}} (含空格、中文标点)
    应该保留原样, 不被误识别为 key"""
    html = '<div>{{EYEBROW · 如 "STRATEGIC RESEARCH"}}</div>'
    out = _apply_slots(html, {})
    assert out == html  # 完全保留


def test_css_page_footer_slot():
    """重现原 bug: CSS @page @bottom-left content 里的 {{文档标题}}
    必须能被替换 (这是用户看到 PDF 页脚出现 {{文档标题}} 字面值的根因)"""
    css = '@page { @bottom-left { content: "{{文档标题}}"; } }'
    out = _apply_slots(css, {"文档标题": "实际标题"})
    assert '"实际标题"' in out
    assert "{{" not in out


def test_real_kami_template_starwars():
    """端到端: 真实模板文件里的 {{文档标题}} 也应替换"""
    tpl_path = os.path.join(os.path.dirname(__file__), '..',
                            'templates', 'kami', 'long-doc-starwars.html')
    with open(tpl_path) as f:
        html = f.read()
    out = _apply_slots(html, {
        "文档标题": "STARWARS TEST",
        "中文标题": "ZH TITLE",
        "副标题": "SUB",
        "作者": "AUTHOR",
        "日期": "2026-05-19",
    })
    # 这 5 个 key 在模板里都出现过, 应该被全部替换
    assert "STARWARS TEST" in out
    assert "ZH TITLE" in out
    assert "AUTHOR" in out
    # 已替换的 key 不应再出现
    assert "{{文档标题}}" not in out
    assert "{{中文标题}}" not in out


if __name__ == "__main__":
    tests = [
        test_ascii_key, test_chinese_key, test_multiple_chinese_keys,
        test_mixed_ascii_and_chinese, test_missing_key_preserved,
        test_template_with_invalid_slot_examples,
        test_css_page_footer_slot,
        test_real_kami_template_starwars,
    ]
    passed = 0
    for t in tests:
        try:
            t()
            print(f"✅ {t.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"❌ {t.__name__}: {e}")
    print(f"\n{passed}/{len(tests)} 通过")
