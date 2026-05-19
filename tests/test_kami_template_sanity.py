"""Kami 模板源文件合法性检查 — 防止模板被意外破坏.

历史 bug: long-doc-starwars.html 所有起始 tag 被 corrupted 成 <<TAGTAG
(e.g. <<htmlhtml, <<headhead, <<stylestyle, <<bodybody). 因为 <style>
不再合法, WeasyPrint 把整个 CSS 块当成普通文本渲染, PDF 前 4 页全是
CSS 源码而不是装饰过的星战风正文.

这个测试扫所有 templates/kami/*.html 锁定:
  - 没有 <<xxx 重复 tag 模式
  - 关键 tag (<html, <head, <body, <style) 都存在且只出现一次
"""
import os
import re
import pathlib

KAMI_DIR = pathlib.Path(__file__).resolve().parent.parent / "templates" / "kami"

# 重复 tag 的特征: <<xxxxxx (两个 < + tag 名 + 同名 tag 名重复)
DOUBLED_TAG_RE = re.compile(r"<<([a-z]+)\1")

# 任何 <<xxx 形式都可疑 (合法 HTML 不会有连续两个 <)
SUSPICIOUS_LT_RE = re.compile(r"<<[a-z]")

REQUIRED_TAGS = ["<html", "<head", "<body", "<style", "<title"]


def test_no_doubled_tags():
    """所有 kami 模板都不应有 <<xxxxxx 重复 tag 损坏"""
    bad = {}
    for f in sorted(KAMI_DIR.glob("*.html")):
        text = f.read_text(encoding="utf-8")
        matches = DOUBLED_TAG_RE.findall(text)
        if matches:
            bad[f.name] = matches[:5]  # 只显示前 5 个
    assert not bad, f"模板有重复 tag 损坏: {bad}"


def test_no_suspicious_double_lt():
    """连续 << + 小写字母 这种模式都可疑 (合法 HTML 不会有)"""
    bad = {}
    for f in sorted(KAMI_DIR.glob("*.html")):
        text = f.read_text(encoding="utf-8")
        count = len(SUSPICIOUS_LT_RE.findall(text))
        if count:
            bad[f.name] = count
    assert not bad, f"模板有可疑的 <<x 模式: {bad}"


def test_required_tags_present():
    """每个模板都应有 html/head/body/style/title"""
    missing = {}
    for f in sorted(KAMI_DIR.glob("*.html")):
        text = f.read_text(encoding="utf-8")
        for tag in REQUIRED_TAGS:
            if tag not in text:
                missing.setdefault(f.name, []).append(tag)
    assert not missing, f"模板缺关键 tag: {missing}"


def test_balanced_style_tags():
    """每个模板的 <style> 和 </style> 数量应相等"""
    bad = {}
    for f in sorted(KAMI_DIR.glob("*.html")):
        text = f.read_text(encoding="utf-8")
        # 用 re 而非 count 避免匹配 <style ...>
        open_n = len(re.findall(r"<style\b", text))
        close_n = len(re.findall(r"</style>", text))
        if open_n != close_n:
            bad[f.name] = f"open={open_n} close={close_n}"
    assert not bad, f"<style> 标签不平衡: {bad}"


if __name__ == "__main__":
    tests = [
        test_no_doubled_tags,
        test_no_suspicious_double_lt,
        test_required_tags_present,
        test_balanced_style_tags,
    ]
    passed = 0
    for t in tests:
        try:
            t()
            print(f"✅ {t.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"❌ {t.__name__}:\n   {e}")
    print(f"\n{passed}/{len(tests)} 通过")
