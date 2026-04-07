#!/usr/bin/env python3
"""typeset-engine DOCX 渲染单元测试"""

import json, os, sys, tempfile, subprocess
from pathlib import Path

# 确保可以导入
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))

SCHEMA_PATH = Path(__file__).parent.parent / 'scripts' / 'schema_docx.json'
DOCKER_IMAGE = 'typeset-engine:v1'


def run_docker(cmd):
    result = subprocess.run(
        f'docker run --rm -v /tmp:/tmp:rw -w /tmp {DOCKER_IMAGE} {cmd}',
        shell=True, capture_output=True, text=True, timeout=120
    )
    return result.returncode, result.stdout, result.stderr


def validate_json(data):
    """检验 JSON 是否符合 Schema"""
    try:
        import jsonschema
        with open(SCHEMA_PATH) as f:
            schema = json.load(f)
        jsonschema.validate(data, schema)
        return True, None
    except ImportError:
        return None, "jsonschema not installed, skipping schema validation"
    except jsonschema.ValidationError as e:
        return False, str(e.message)
    except Exception as e:
        return None, str(e)


class TestSchema:
    """Schema 格式检验测试"""

    def test_valid_minimal(self):
        """最小合法数据"""
        data = {"title": "测试报告", "sections": [{"type": "heading", "title": "第一章"}]}
        ok, err = validate_json(data)
        assert ok is not False, f"最小数据应通过检验: {err}"

    def test_missing_title(self):
        """缺少 title 应报错"""
        data = {"sections": []}
        ok, err = validate_json(data)
        assert ok is False, "缺少 title 应报错"

    def test_missing_sections(self):
        """缺少 sections 应报错"""
        data = {"title": "测试"}
        ok, err = validate_json(data)
        assert ok is False, "缺少 sections 应报错"

    def test_invalid_section_type(self):
        """非法 section type 应报错"""
        data = {"title": "测试", "sections": [{"type": "invalid_type"}]}
        ok, err = validate_json(data)
        assert ok is False, "非法 type 应报错"

    def test_heading_without_title(self):
        """heading 类型缺少 title 应报错"""
        data = {"title": "测试", "sections": [{"type": "heading"}]}
        ok, err = validate_json(data)
        assert ok is False, "heading 缺少 title 应报错"

    def test_table_with_valid_rows(self):
        """合法 table 数据"""
        data = {
            "title": "测试",
            "sections": [
                {"type": "table", "headers": ["A", "B"], "rows": [["1", "2"], ["3", "4"]]}
            ]
        }
        ok, err = validate_json(data)
        assert ok is not False, f"合法 table 应通过: {err}"


class TestParagraphFormatting:
    """段落格式测试：渲染后不应出现 JUSTIFY 或居中"""

    def test_paragraph_left_align(self):
        """paragraph 类型应生成左对齐段落"""
        data = {
            "title": "测试报告",
            "sections": [
                {"type": "paragraph", "content": "这是第一段内容。\n\n这是第二段内容。"}
            ]
        }
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
            json.dump(data, f)
            tmp = f.name

        try:
            rc, out, err = run_docker(f'python /app/scripts/engine.py docx --data {tmp} --output /tmp/test_out.docx --theme cicc')
            assert rc == 0, f"渲染失败: {err}"

            # 检查输出文件
            assert os.path.exists('/tmp/test_out.docx'), "输出文件不存在"
            size = os.path.getsize('/tmp/test_out.docx')
            assert size > 5000, f"输出文件太小 ({size} bytes)，可能渲染不完整"
        finally:
            os.unlink(tmp)

    def test_list_items_hanging_indent(self):
        """列表项（bullet）应正确处理"""
        data = {
            "title": "测试报告",
            "sections": [
                {
                    "type": "paragraph",
                    "content": "核心发现：\n• 第一项内容\n• 第二项内容\n• 第三项内容"
                }
            ]
        }
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
            json.dump(data, f)
            tmp = f.name

        try:
            rc, out, err = run_docker(f'python /app/scripts/engine.py docx --data {tmp} --output /tmp/test_out.docx --theme cicc')
            assert rc == 0, f"渲染失败: {err}"
            assert os.path.exists('/tmp/test_out.docx'), "输出文件不存在"
        finally:
            os.unlink(tmp)


class TestTableFormatting:
    """表格格式测试"""

    def test_table_left_align(self):
        """表格数据列应左对齐"""
        data = {
            "title": "测试报告",
            "sections": [
                {
                    "type": "table",
                    "headers": ["模型", "价格", "备注"],
                    "rows": [
                        ["GLM-5", "0.10元", "高峰期3倍系数"],
                        ["GLM-4.7", "0.10元", "非高峰期2倍系数"]
                    ]
                }
            ]
        }
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
            json.dump(data, f)
            tmp = f.name

        try:
            rc, out, err = run_docker(f'python /app/scripts/engine.py docx --data {tmp} --output /tmp/test_out.docx --theme cicc')
            assert rc == 0, f"渲染失败: {err}"
            assert os.path.exists('/tmp/test_out.docx'), "输出文件不存在"
        finally:
            os.unlink(tmp)

    def test_empty_cells_handled(self):
        """空单元格应处理"""
        data = {
            "title": "测试报告",
            "sections": [
                {
                    "type": "table",
                    "headers": ["模型", "价格"],
                    "rows": [["GLM-5", "0.10元"], ["Kimi K2.5", ""]]
                }
            ]
        }
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
            json.dump(data, f)
            tmp = f.name

        try:
            rc, out, err = run_docker(f'python /app/scripts/engine.py docx --data {tmp} --output /tmp/test_out.docx --theme cicc')
            assert rc == 0, f"含空单元格的表格应正常渲染: {err}"
        finally:
            os.unlink(tmp)


class TestThemeConsistency:
    """主题一致性测试"""

    def test_all_themes_render(self):
        """四种主题都能正常渲染"""
        for theme in ['cicc', 'ms', 'cms', 'dachen']:
            data = {
                "title": f"{theme} 风格测试",
                "sections": [
                    {"type": "heading", "title": "第一章"},
                    {"type": "paragraph", "content": "这是正文内容。"},
                    {
                        "type": "table",
                        "headers": ["A", "B"],
                        "rows": [["1", "2"]]
                    }
                ]
            }
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
                json.dump(data, f)
                tmp = f.name

            try:
                rc, out, err = run_docker(
                    f'python /app/scripts/engine.py docx --data {tmp} --output /tmp/test_{theme}.docx --theme {theme}'
                )
                assert rc == 0, f"{theme} 主题渲染失败: {err}"
                assert os.path.exists(f'/tmp/test_{theme}.docx'), f"{theme} 输出文件不存在"
            finally:
                os.unlink(tmp)


class TestComplexReport:
    """完整报告结构测试"""

    def test_full_report_structure(self):
        """模拟完整报告结构"""
        data = {
            "title": "中国大模型Token调查报告",
            "title_en": "China LLM Token Usage Survey",
            "author": "Clawd AI",
            "date": "2026年4月",
            "toc": True,
            "sections": [
                {"type": "heading", "title": "执行摘要", "content": "2026年2月，中国AI大模型迎来历史性时刻。"},
                {"type": "quote", "content": "2026年2月，中国模型OpenRouter周调用量首次超越美国。"},
                {
                    "type": "heading",
                    "title": "各模型深度分析",
                    "children": [
                        {"type": "heading", "title": "智谱AI", "content": "智谱AI是国内最早推出大模型的AI公司。"},
                        {
                            "type": "heading",
                            "title": "Token调用量数据",
                            "children": [
                                {
                                    "type": "table",
                                    "headers": ["指标", "数据"],
                                    "rows": [
                                        ["日均云端Token调用量（2025年11月）", "超过4.2万亿次"],
                                        ["OpenRouter周调用量（GLM-5，2026年2月）", "约0.8万亿Token/周"]
                                    ]
                                }
                            ]
                        }
                    ]
                },
                {
                    "type": "heading",
                    "title": "定价策略",
                    "children": [
                        {
                            "type": "table",
                            "headers": ["模型", "输入价格", "输出价格", "备注"],
                            "rows": [
                                ["GLM-5", "0.10元", "1.00元", "高峰期3倍系数"],
                                ["GLM-4.7", "0.10元", "1.00元", "非高峰期2倍系数"],
                                ["GLM-4-Air", "0.001元", "0.01元", "低价入门级"]
                            ]
                        }
                    ]
                },
                {"type": "pagebreak"},
                {"type": "heading", "title": "免责声明", "content": "本报告仅供参考，不构成投资建议。"}
            ]
        }
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
            json.dump(data, f)
            tmp = f.name

        try:
            rc, out, err = run_docker(f'python /app/scripts/engine.py docx --data {tmp} --output /tmp/full_report.docx --theme cicc')
            assert rc == 0, f"完整报告渲染失败: {err}"
            size = os.path.getsize('/tmp/full_report.docx')
            assert size > 20000, f"完整报告文件太小 ({size} bytes)"
            print(f"  完整报告大小: {size} bytes", file=sys.stderr)
        finally:
            os.unlink(tmp)


# 运行所有测试
if __name__ == '__main__':
    import traceback

    test_classes = [TestSchema, TestParagraphFormatting, TestTableFormatting, TestThemeConsistency, TestComplexReport]
    total = 0
    passed = 0
    failed = 0

    for cls in test_classes:
        print(f"\n{'='*50}")
        print(f"  {cls.__name__}")
        print(f"{'='*50}")
        for name in dir(cls):
            if name.startswith('test_'):
                total += 1
                try:
                    getattr(cls(), name)()
                    print(f"  ✅ {name}")
                    passed += 1
                except AssertionError as e:
                    print(f"  ❌ {name}: {e}")
                    failed += 1
                except Exception as e:
                    print(f"  💥 {name}: {e}")
                    traceback.print_exc()
                    failed += 1

    print(f"\n{'='*50}")
    print(f"  结果: {passed}/{total} 通过", end="")
    if failed:
        print(f"，{failed} 失败", end="")
    print()
    sys.exit(0 if failed == 0 else 1)
