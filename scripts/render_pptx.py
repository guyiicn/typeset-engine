#!/usr/bin/env python3
"""
PPTX 渲染引擎 — 支持多种投行/券商风格模板。

模板:
  default        — 简洁商务蓝
  cicc           — 中金红
  goldman        — 高盛蓝灰
  morgan         — 摩根深蓝
  dark           — 深色主题
  minimal        — 极简白

数据格式 (JSON):
{
  "title": "贵州茅台 研究报告",
  "subtitle": "600519 | 白酒/消费",
  "author": "FinRobot",
  "date": "2026-04-07",
  "slides": [
    {
      "layout": "title",          # title / section / content / two_column / chart / table / summary
      "title": "公司概况",
      "content": "正文内容...",
      "bullets": ["要点1", "要点2"],
      "image": "/path/to/chart.png",
      "table": {"headers": [...], "rows": [...]},
      "notes": "演讲者备注"
    }
  ]
}
"""

import os
from pathlib import Path
from typing import Dict, List, Optional

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

# ═══════════════════════════════════════════
# 主题配置
# ═══════════════════════════════════════════

THEMES = {
    'default': {
        'name': 'Business Blue',
        'primary': RGBColor(0x1a, 0x36, 0x5d),      # 深蓝
        'secondary': RGBColor(0xc9, 0xa2, 0x27),     # 金色
        'text_dark': RGBColor(0x2d, 0x37, 0x48),
        'text_light': RGBColor(0xff, 0xff, 0xff),
        'bg_color': RGBColor(0xff, 0xff, 0xff),
        'accent_bg': RGBColor(0x1a, 0x36, 0x5d),
        'table_header': RGBColor(0x1a, 0x36, 0x5d),
        'table_alt': RGBColor(0xf0, 0xf4, 0xf8),
        'font_title': 'Noto Sans CJK SC',
        'font_body': 'Noto Sans CJK SC',
        'font_title_fallback': 'Arial',
        'font_body_fallback': 'Arial',
    },
    'cicc': {
        'name': '中金研究',
        'primary': RGBColor(0xC4, 0x1E, 0x3A),      # 中金红
        'secondary': RGBColor(0x8B, 0x00, 0x00),     # 深红
        'text_dark': RGBColor(0x33, 0x33, 0x33),
        'text_light': RGBColor(0xff, 0xff, 0xff),
        'bg_color': RGBColor(0xff, 0xff, 0xff),
        'accent_bg': RGBColor(0xC4, 0x1E, 0x3A),
        'table_header': RGBColor(0xf5, 0xf5, 0xf5),
        'table_alt': RGBColor(0xfa, 0xfa, 0xfa),
        'font_title': 'Noto Sans CJK SC',
        'font_body': 'Noto Sans CJK SC',
        'font_title_fallback': 'Microsoft YaHei',
        'font_body_fallback': 'Microsoft YaHei',
    },
    'goldman': {
        'name': 'Goldman Sachs',
        'primary': RGBColor(0x00, 0x3A, 0x70),      # GS深蓝
        'secondary': RGBColor(0x6B, 0x8E, 0x23),     # 橄榄绿
        'text_dark': RGBColor(0x33, 0x33, 0x33),
        'text_light': RGBColor(0xff, 0xff, 0xff),
        'bg_color': RGBColor(0xff, 0xff, 0xff),
        'accent_bg': RGBColor(0x00, 0x3A, 0x70),
        'table_header': RGBColor(0x00, 0x3A, 0x70),
        'table_alt': RGBColor(0xf0, 0xf5, 0xfa),
        'font_title': 'Arial',
        'font_body': 'Arial',
        'font_title_fallback': 'Helvetica',
        'font_body_fallback': 'Helvetica',
    },
    'morgan': {
        'name': 'Morgan Stanley',
        'primary': RGBColor(0x00, 0x1E, 0x62),      # MS深蓝
        'secondary': RGBColor(0x00, 0x7A, 0xB8),     # 亮蓝
        'text_dark': RGBColor(0x33, 0x33, 0x33),
        'text_light': RGBColor(0xff, 0xff, 0xff),
        'bg_color': RGBColor(0xff, 0xff, 0xff),
        'accent_bg': RGBColor(0x00, 0x1E, 0x62),
        'table_header': RGBColor(0x00, 0x1E, 0x62),
        'table_alt': RGBColor(0xf0, 0xf0, 0xf8),
        'font_title': 'Arial',
        'font_body': 'Arial',
        'font_title_fallback': 'Helvetica',
        'font_body_fallback': 'Helvetica',
    },
    'dark': {
        'name': 'Dark Theme',
        'primary': RGBColor(0x00, 0xd4, 0xaa),      # 青绿
        'secondary': RGBColor(0xff, 0x6b, 0x6b),     # 珊瑚红
        'text_dark': RGBColor(0xe0, 0xe0, 0xe0),
        'text_light': RGBColor(0xff, 0xff, 0xff),
        'bg_color': RGBColor(0x1a, 0x1a, 0x2e),
        'accent_bg': RGBColor(0x16, 0x21, 0x3e),
        'table_header': RGBColor(0x16, 0x21, 0x3e),
        'table_alt': RGBColor(0x20, 0x2a, 0x44),
        'font_title': 'Noto Sans CJK SC',
        'font_body': 'Noto Sans CJK SC',
        'font_title_fallback': 'Arial',
        'font_body_fallback': 'Arial',
    },
    'minimal': {
        'name': 'Minimal White',
        'primary': RGBColor(0x33, 0x33, 0x33),
        'secondary': RGBColor(0x99, 0x99, 0x99),
        'text_dark': RGBColor(0x33, 0x33, 0x33),
        'text_light': RGBColor(0xff, 0xff, 0xff),
        'bg_color': RGBColor(0xff, 0xff, 0xff),
        'accent_bg': RGBColor(0x33, 0x33, 0x33),
        'table_header': RGBColor(0xf5, 0xf5, 0xf5),
        'table_alt': RGBColor(0xfa, 0xfa, 0xfa),
        'font_title': 'Noto Sans CJK SC',
        'font_body': 'Noto Sans CJK SC',
        'font_title_fallback': 'Arial',
        'font_body_fallback': 'Arial',
    },
}


# ═══════════════════════════════════════════
# PPT 生成核心
# ═══════════════════════════════════════════

class PptxBuilder:
    """PPTX 文档构建器"""

    def __init__(self, theme_name: str = 'default'):
        self.prs = Presentation()
        self.prs.slide_width = Inches(13.333)   # 16:9
        self.prs.slide_height = Inches(7.5)
        self.theme = THEMES.get(theme_name, THEMES['default'])
        self.slide_w = self.prs.slide_width
        self.slide_h = self.prs.slide_height

    def _add_bg(self, slide, color=None):
        """设置幻灯片背景色"""
        bg = slide.background
        fill = bg.fill
        fill.solid()
        fill.fore_color.rgb = color or self.theme['bg_color']

    def _add_text(self, slide, text, left, top, width, height,
                   font_size=18, color=None, bold=False, alignment=PP_ALIGN.LEFT,
                   font_name=None):
        """添加文本框"""
        txBox = slide.shapes.add_textbox(left, top, width, height)
        tf = txBox.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = text
        p.font.size = Pt(font_size)
        p.font.color.rgb = color or self.theme['text_dark']
        p.font.bold = bold
        p.font.name = font_name or self.theme['font_title']
        p.alignment = alignment
        return txBox

    def _add_shape(self, slide, shape_type, left, top, width, height, fill_color):
        """添加形状"""
        shape = slide.shapes.add_shape(shape_type, left, top, width, height)
        shape.fill.solid()
        shape.fill.fore_color.rgb = fill_color
        shape.line.fill.background()
        return shape

    # ── 幻灯片布局 ──

    def add_title_slide(self, title: str, subtitle: str = '', author: str = '', date: str = ''):
        """封面页"""
        slide = self.prs.slides.add_slide(self.prs.slide_layouts[6])  # blank
        self._add_bg(slide)

        # 顶部色条
        self._add_shape(slide, MSO_SHAPE.RECTANGLE,
                        Inches(0), Inches(0), self.slide_w, Inches(0.15),
                        self.theme['primary'])

        # 底部色块
        self._add_shape(slide, MSO_SHAPE.RECTANGLE,
                        Inches(0), Inches(4.5), self.slide_w, Inches(3),
                        self.theme['accent_bg'])

        # 标题
        self._add_text(slide, title,
                        Inches(1), Inches(1.5), Inches(11), Inches(1.5),
                        font_size=40, bold=True, color=self.theme['primary'],
                        alignment=PP_ALIGN.LEFT)

        # 副标题
        if subtitle:
            self._add_text(slide, subtitle,
                            Inches(1), Inches(3.2), Inches(11), Inches(0.8),
                            font_size=20, color=self.theme['secondary'])

        # 作者和日期
        info = f"{author}  |  {date}" if author else date
        if info:
            self._add_text(slide, info,
                            Inches(1), Inches(5.5), Inches(11), Inches(0.6),
                            font_size=16, color=self.theme['text_light'],
                            alignment=PP_ALIGN.LEFT)

    def add_section_slide(self, title: str, subtitle: str = ''):
        """章节分隔页"""
        slide = self.prs.slides.add_slide(self.prs.slide_layouts[6])
        self._add_bg(slide, self.theme['accent_bg'])

        # 左侧竖条
        self._add_shape(slide, MSO_SHAPE.RECTANGLE,
                        Inches(0.8), Inches(2), Inches(0.08), Inches(2),
                        self.theme['text_light'])

        self._add_text(slide, title,
                        Inches(1.2), Inches(2.5), Inches(10), Inches(1.2),
                        font_size=36, bold=True, color=self.theme['text_light'])

        if subtitle:
            self._add_text(slide, subtitle,
                            Inches(1.2), Inches(4), Inches(10), Inches(0.8),
                            font_size=18, color=self.theme['secondary'])

    def add_content_slide(self, title: str, content: str = '',
                           bullets: List[str] = None, image: str = None,
                           notes: str = None):
        """正文页"""
        slide = self.prs.slides.add_slide(self.prs.slide_layouts[6])
        self._add_bg(slide)

        # 顶部色条
        self._add_shape(slide, MSO_SHAPE.RECTANGLE,
                        Inches(0), Inches(0), self.slide_w, Inches(0.06),
                        self.theme['primary'])

        # 标题
        self._add_text(slide, title,
                        Inches(0.8), Inches(0.4), Inches(11), Inches(0.7),
                        font_size=28, bold=True, color=self.theme['primary'])

        # 标题下分隔线
        self._add_shape(slide, MSO_SHAPE.RECTANGLE,
                        Inches(0.8), Inches(1.15), Inches(11.5), Inches(0.02),
                        self.theme['primary'])

        content_top = Inches(1.5)
        content_width = Inches(7.5) if image else Inches(11.5)

        # 正文
        if content:
            self._add_text(slide, content,
                            Inches(0.8), content_top, content_width, Inches(4.5),
                            font_size=16, color=self.theme['text_dark'],
                            font_name=self.theme['font_body'])

        # 要点列表
        if bullets:
            txBox = slide.shapes.add_textbox(
                Inches(0.8), content_top + (Inches(1.5) if content else Inches(0)),
                content_width, Inches(4))
            tf = txBox.text_frame
            tf.word_wrap = True
            for i, bullet in enumerate(bullets):
                p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
                p.text = f"  •  {bullet}"
                p.font.size = Pt(15)
                p.font.color.rgb = self.theme['text_dark']
                p.font.name = self.theme['font_body']
                p.space_after = Pt(8)

        # 图片
        if image and os.path.exists(image):
            try:
                slide.shapes.add_picture(image,
                    Inches(8.8), Inches(1.5), Inches(4), Inches(3))
            except:
                pass

        # 演讲者备注
        if notes:
            slide.notes_slide.notes_text_frame.text = notes

    def add_two_column_slide(self, title: str, left_content: str,
                              right_content: str = '', right_image: str = None):
        """双栏页"""
        slide = self.prs.slides.add_slide(self.prs.slide_layouts[6])
        self._add_bg(slide)

        self._add_shape(slide, MSO_SHAPE.RECTANGLE,
                        Inches(0), Inches(0), self.slide_w, Inches(0.06),
                        self.theme['primary'])

        self._add_text(slide, title,
                        Inches(0.8), Inches(0.4), Inches(11), Inches(0.7),
                        font_size=28, bold=True, color=self.theme['primary'])

        self._add_shape(slide, MSO_SHAPE.RECTANGLE,
                        Inches(0.8), Inches(1.15), Inches(11.5), Inches(0.02),
                        self.theme['primary'])

        # 左栏
        self._add_text(slide, left_content,
                        Inches(0.8), Inches(1.5), Inches(5.5), Inches(5),
                        font_size=14, color=self.theme['text_dark'],
                        font_name=self.theme['font_body'])

        # 右栏
        if right_image and os.path.exists(right_image):
            slide.shapes.add_picture(right_image,
                Inches(7), Inches(1.5), Inches(5.5), Inches(4))
        elif right_content:
            self._add_text(slide, right_content,
                            Inches(7), Inches(1.5), Inches(5.5), Inches(5),
                            font_size=14, color=self.theme['text_dark'],
                            font_name=self.theme['font_body'])

    def add_table_slide(self, title: str, headers: List[str], rows: List[List[str]]):
        """表格页"""
        slide = self.prs.slides.add_slide(self.prs.slide_layouts[6])
        self._add_bg(slide)

        self._add_shape(slide, MSO_SHAPE.RECTANGLE,
                        Inches(0), Inches(0), self.slide_w, Inches(0.06),
                        self.theme['primary'])

        self._add_text(slide, title,
                        Inches(0.8), Inches(0.4), Inches(11), Inches(0.7),
                        font_size=28, bold=True, color=self.theme['primary'])

        # 表格
        n_rows = min(len(rows) + 1, 15)  # 最多 15 行
        n_cols = len(headers)
        table_shape = slide.shapes.add_table(
            n_rows, n_cols,
            Inches(0.8), Inches(1.5),
            Inches(11.5), Inches(5)
        )
        table = table_shape.table

        # 表头
        for j, h in enumerate(headers):
            cell = table.cell(0, j)
            cell.text = str(h)
            cell.fill.solid()
            cell.fill.fore_color.rgb = self.theme['table_header']
            for p in cell.text_frame.paragraphs:
                p.font.size = Pt(12)
                p.font.bold = True
                p.font.color.rgb = self.theme['text_light'] if self.theme['table_header'] != self.theme['table_alt'] else self.theme['text_dark']
                p.font.name = self.theme['font_body']

        # 数据行
        for i, row in enumerate(rows[:14]):
            for j, val in enumerate(row):
                cell = table.cell(i + 1, j)
                cell.text = str(val)
                if i % 2 == 1:
                    cell.fill.solid()
                    cell.fill.fore_color.rgb = self.theme['table_alt']
                for p in cell.text_frame.paragraphs:
                    p.font.size = Pt(11)
                    p.font.color.rgb = self.theme['text_dark']
                    p.font.name = self.theme['font_body']

    def add_summary_slide(self, title: str, points: List[str]):
        """总结页"""
        slide = self.prs.slides.add_slide(self.prs.slide_layouts[6])
        self._add_bg(slide, self.theme['accent_bg'])

        self._add_text(slide, title,
                        Inches(1), Inches(0.8), Inches(11), Inches(1),
                        font_size=32, bold=True, color=self.theme['text_light'],
                        alignment=PP_ALIGN.CENTER)

        y = Inches(2.2)
        for point in points:
            self._add_text(slide, f"✓  {point}",
                            Inches(2), y, Inches(9), Inches(0.6),
                            font_size=18, color=self.theme['text_light'])
            y += Inches(0.7)

    def save(self, output_path: str):
        """保存 PPTX"""
        os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
        self.prs.save(output_path)
        print(f"✅ PPTX saved: {output_path} ({os.path.getsize(output_path) / 1024:.0f} KB)")


# ═══════════════════════════════════════════
# 渲染入口
# ═══════════════════════════════════════════

LAYOUT_MAP = {
    'title': 'add_title_slide',
    'section': 'add_section_slide',
    'content': 'add_content_slide',
    'two_column': 'add_two_column_slide',
    'table': 'add_table_slide',
    'summary': 'add_summary_slide',
}


def render_pptx(data: Dict, output_path: str, template: str = 'default'):
    """
    根据 JSON 数据渲染 PPTX。

    data = {
        "title": "报告标题",
        "subtitle": "副标题",
        "author": "作者",
        "date": "日期",
        "theme": "cicc",  # 可选，覆盖 template 参数
        "slides": [
            {"layout": "title", "title": "...", ...},
            {"layout": "content", "title": "...", "content": "...", "bullets": [...]},
            {"layout": "table", "title": "...", "headers": [...], "rows": [...]},
        ]
    }
    """
    theme = data.get('theme', template)
    builder = PptxBuilder(theme_name=theme)

    # 封面
    if data.get('title'):
        builder.add_title_slide(
            title=data.get('title', ''),
            subtitle=data.get('subtitle', ''),
            author=data.get('author', ''),
            date=data.get('date', ''),
        )

    # 各页
    for slide_data in data.get('slides', []):
        layout = slide_data.get('layout', 'content')

        if layout == 'title':
            builder.add_title_slide(
                title=slide_data.get('title', ''),
                subtitle=slide_data.get('subtitle', ''),
            )
        elif layout == 'section':
            builder.add_section_slide(
                title=slide_data.get('title', ''),
                subtitle=slide_data.get('subtitle', ''),
            )
        elif layout == 'content':
            builder.add_content_slide(
                title=slide_data.get('title', ''),
                content=slide_data.get('content', ''),
                bullets=slide_data.get('bullets'),
                image=slide_data.get('image'),
                notes=slide_data.get('notes'),
            )
        elif layout == 'two_column':
            builder.add_two_column_slide(
                title=slide_data.get('title', ''),
                left_content=slide_data.get('left_content', slide_data.get('content', '')),
                right_content=slide_data.get('right_content', ''),
                right_image=slide_data.get('image'),
            )
        elif layout == 'table':
            builder.add_table_slide(
                title=slide_data.get('title', ''),
                headers=slide_data.get('headers', []),
                rows=slide_data.get('rows', []),
            )
        elif layout == 'summary':
            builder.add_summary_slide(
                title=slide_data.get('title', ''),
                points=slide_data.get('points', slide_data.get('bullets', [])),
            )

    builder.save(output_path)
    return output_path
