#!/usr/bin/env python3
"""
DOCX 输入数据预检验脚本。

在渲染前检查 JSON 数据是否符合规范，提前报错。
运行：
  python validate_docx.py --data input.json

返回：
  0 = 通过
  1 = 格式错误（输出详细错误信息）
  2 = JSON 语法错误
"""

import json, sys, re
from pathlib import Path

ISSUES = []
WARNINGS = []


def check(data, path="root"):
    if not isinstance(data, dict):
        ISSUES.append(f"{path}: 期望 dict，得到 {type(data).__name__}")
        return

    # 顶层必填字段
    for field in ['title', 'sections']:
        if field not in data:
            ISSUES.append(f"缺少必填字段: {field}")

    # sections
    for i, sec in enumerate(data.get('sections', [])):
        check_section(sec, f"sections[{i}]")

    # JSON 字符串中禁止出现的字符（在渲染时可能引发问题）
    for i, sec in enumerate(data.get('sections', [])):
        check_strings(sec, f"sections[{i}]")


def check_section(sec, path):
    if not isinstance(sec, dict):
        ISSUES.append(f"{path}: 期望 dict，得到 {type(sec).__name__}")
        return

    t = sec.get('type')

    # paragraph 类型：检查内容是否包含未转义的换行问题
    if t == 'paragraph':
        content = sec.get('content', '')
        # 检测：\n\n 在 JSON 字符串中应该用 literal 换行，render_docx 会自动处理
        # 但如果有连续的纯数字或短句被强行换行，给警告
        lines = content.split('\n')
        for li, line in enumerate(lines):
            line = line.strip()
            # 如果一行只有一个百分比或数字片段，给警告
            if re.match(r'^[\+\-]?\d+[\.%]?$', line) and len(line) < 10:
                WARNINGS.append(f"{path} content: 第 {li+1} 行是孤立数字/百分比「{line}」，建议合并到上一行避免格式问题")
        if '\r' in content:
            WARNINGS.append(f"{path} content: 包含 \\r，建议只使用 \\n 换行")

    # table 类型：检查行列数匹配
    if t == 'table':
        headers = sec.get('headers', [])
        rows = sec.get('rows', [])
        if headers:
            for ri, row in enumerate(rows):
                if len(row) != len(headers):
                    ISSUES.append(f"{path} rows[{ri}]: 列数 {len(row)} 与表头列数 {len(headers)} 不匹配")
        # 检查空单元格
        for ri, row in enumerate(rows):
            for ci, cell in enumerate(row):
                if cell == '':
                    WARNINGS.append(f"{path} rows[{ri}][{ci}]: 空单元格，建议填「—」或具体数据")

    # 递归子章节
    for i, child in enumerate(sec.get('children', [])):
        check_section(child, f"{path}.children[{i}]")


def check_strings(obj, path):
    """检查字符串值中是否有渲染问题的模式"""
    if isinstance(obj, dict):
        for k, v in obj.items():
            check_strings(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            check_strings(v, f"{path}[{i}]")
    elif isinstance(obj, str):
        # 检测裸露的引号（中文引号或未转义的英文引号）
        if '"' in obj or '"' in obj or '"' in obj:
            WARNINGS.append(f"{path}: 包含「{obj[:30]}...」— 字符串内的引号可能导致渲染错位，建议使用「」或转义")
        # 检测裸露的反斜杠（可能的未转义字符）
        if '\\n' in obj and '\\n\\n' not in obj:
            WARNINGS.append(f"{path}: 包含单个 \\n（将作为段落内换行处理）；双 \\n\\n 才会分段，请确认意图")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="预检验 DOCX JSON 输入数据")
    parser.add_argument('--data', required=True, help='输入 JSON 文件路径')
    parser.add_argument('--strict', action='store_true', help='将警告也视为错误')
    parser.add_argument('--warn-only', action='store_true', help='仅输出警告，不输出错误")
    args = parser.parse_args()

    # 加载 JSON
    try:
        with open(args.data) as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"[JSON错误] 行{e.lineno} 列{e.colno}: {e.msg}", file=sys.stderr)
        print(f"  上下文: ...{e.doc[max(0,e.pos-20):e.pos+20]}...", file=sys.stderr)
        sys.exit(2)

    # 检验
    check(data)

    has_error = bool(ISSUES)
    has_warn = bool(WARNINGS)

    if has_error:
        print(f"[错误] 发现 {len(ISSUES)} 个问题:", file=sys.stderr)
        for issue in ISSUES:
            print(f"  ✗ {issue}", file=sys.stderr)

    if has_warn:
        print(f"[警告] 发现 {len(WARNINGS)} 个潜在问题:")
        for warn in WARNINGS:
            print(f"  ⚠ {warn}")

    if has_error:
        sys.exit(1)

    if has_warn and args.strict:
        print("[失败] 存在警告，--strict 模式下视为错误", file=sys.stderr)
        sys.exit(1)

    print("✅ 检验通过，数据格式符合规范")
    sys.exit(0)



def validate_docx_data(data_path):
    """
    供 engine.py 调用的检验函数。
    Args:
        data_path: JSON 文件路径
    Returns:
        list of issues (empty = 通过)
    """
    global ISSUES, WARNINGS
    ISSUES = []
    WARNINGS = []

    try:
        with open(data_path) as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        return [f"JSON语法错误: {e.msg} (行{e.lineno})"]

    check(data)
    return ISSUES + WARNINGS


if __name__ == '__main__':
    main()
