# 创始人指南 (Founders Playbook) PDF 模板

## 实现状态
已完成并集成到 `render_kami.py`。

## 功能
- **模板**: `templates/kami/founders-playbook.html`（骨架模板，含 CSS 定义）
- **渲染逻辑**: `render_kami.py` 中的 `_build_fpb_html()` 数据驱动函数
- **测试**: `tests/test_fpb.py` ✅
- **实际测试**: `hbr_2026_official_zh-only.epub` → `/tmp/hbr-fpb-v10.pdf`（39 页，内容完整，颜色轮换正常）

## 输入格式
```python
render_template(
    doc_type="founders-playbook",
    language="zh",
    slots={
        "title": "创始人指南",
        "subtitle": "打造原生 AI 初创企业",
        "mode": "full",  # 全局默认: "full" | "minimal" | "plain"
        "chapters": [
            {"number": 1, "title": "第一章", "mode": "full", "body": "<p>...</p>"},
            {"number": 2, "title": "第二章", "mode": "minimal", "body": "<p>...</p>"},
            {"number": 3, "title": "第三章", "mode": "plain", "body": "<p>...</p>"},
        ],
    },
)
```

## 页面组成
1. **封面** (1 页): Coral 背景，左上标题，左下 Logo
2. **目录** (1 页): 双栏
3. **章节扉页** (N 页): 可选，7 色循环（Coral→Teal→Purple→Mint→Lavender→Peach→Warm Gray）
4. **章节正文** (N 页): 思源宋体 CN 9pt，段落级绝对定位
5. **封底** (1 页): Coral 背景，"claude.ai"

## 模式
- `full`: 扉页 + 正文（彩色扉页）
- `minimal`: 只有标题页（白色背景）
- `plain`: 只有正文（无扉页）

## 字体
- 中文: `Source Han Serif CN` Regular
- 中文 Sans: `Noto Sans CJK SC`
- 英文: Georgia

## 关键 CSS
```css
@page { size: 8.5in 11in; margin: 0; }
```
