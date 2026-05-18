"""测试 founders-playbook 模板"""
import sys, os, json

# 确保能从项目根目录导入
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))
from render_kami import render_template

def test_fpb_basic():
    """基本渲染测试"""
    out = '/tmp/fpb-test.pdf'
    slots = {
        "title": "创始人指南",
        "subtitle": "打造原生 AI 初创企业",
        "mode": "full",
        "chapters": [
            {
                "number": 1,
                "title": "初创企业生命周期：2026 年重启版",
                "mode": "full",
                "body": "<p>人工智能正在重塑初创企业的构建方式。</p>",
            },
            {
                "number": 2,
                "title": "创始人定义的改变",
                "mode": "minimal",
                "body": "<p>曾经，创始人必须能写代码、懂销售、管运营。</p>",
            },
            {
                "number": 3,
                "title": "创意阶段",
                "mode": "plain",
                "body": "<p>创意阶段的目标是找到真正值得解决的问题。</p>",
            },
        ],
    }

    result = render_template(
        doc_type="founders-playbook",
        language="zh",
        body_html=None,
        slots=slots,
        out_path=out,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))

    # 验证
    assert result["pages"] >= 8, f"页数太少: {result['pages']}"
    assert os.path.exists(out), f"PDF 不存在: {out}"
    assert result["size_bytes"] > 100000, f"文件太小: {result['size_bytes']}"
    print("✅ test_fpb_basic passed")


def test_fpb_chinese():
    """中文内容渲染测试"""
    import fitz
    out = '/tmp/fpb-test-zh.pdf'
    slots = {
        "title": "创始人指南",
        "subtitle": "打造原生 AI 初创企业",
        "mode": "full",
        "chapters": [
            {
                "number": 1,
                "title": "初创企业生命周期：2026 年重启版",
                "mode": "full",
                "body": "<p>人工智能正在重塑初创企业的构建方式。如今，从未写过一行代码的创始人也能推出生产级应用程序；曾经那种十人团队打造独角兽的草根逆袭故事，已转变为精心设计的行业。</p>",
            },
        ],
    }

    result = render_template(
        doc_type="founders-playbook",
        language="zh",
        body_html=None,
        slots=slots,
        out_path=out,
    )

    # 验证中文内容存在
    doc = fitz.open(out)
    page = doc[0]  # 封面
    text = page.get_text()
    assert "创始人指南" in text, f"封面没有中文: {text}"
    print("✅ test_fpb_chinese passed")


if __name__ == "__main__":
    test_fpb_basic()
    test_fpb_chinese()
    print("\n✅ 全部测试通过")
