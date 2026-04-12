#!/usr/bin/env python3
"""
PDF 渲染引擎 — 基于 Typst 排版 + Plotly 图表。

流程: JSON data → 生成图表 PNG → 生成 .typ 源文件 → typst compile → PDF

支持主题: cicc / ms / cms / dachen
支持章节: cover, toc, heading, paragraph, table, chart, quote, kpi, disclaimer

用法:
  python render_pdf.py --data input.json --output report.pdf --theme cicc
"""

import json
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Any, Optional

# 图表引擎复用
try:
    from scripts.render_charts import render_chart, CHART_TYPES
except ImportError:
    from render_charts import render_chart, CHART_TYPES


# ═══════════════════════════════════════════
# 主题配置（与 themes.typ 对应）
# ═══════════════════════════════════════════

THEMES = {
    'cicc': {
        'accent': '#c41e3a',
        'heading': '#1a1a2e',
        'serif_body': True,
        'label': '中金公司 CICC',
    },
    'ms': {
        'accent': '#0078C8',
        'heading': '#002D72',
        'serif_body': False,
        'label': 'Morgan Stanley',
    },
    'cms': {
        'accent': '#E60033',
        'heading': '#333333',
        'serif_body': True,
        'label': '招商证券 CMS',
    },
    'dachen': {
        'accent': '#b8141d',
        'heading': '#333333',
        'serif_body': True,
        'label': '达晨财智 Fortune Capital',
    },
    'gongwen': {
        'accent': '#e60012',
        'heading': '#000000',
        'serif_body': True,
        'label': '党政公文 GB/T 9704',
    },
    'tbs': {
        'accent': '#e60012',
        'heading': '#000000',
        'serif_body': True,
        'label': '电广传媒 TBS',
        # 预设：organ=湖南电广传媒股份有限公司, doc_type="", redhead_size=36
    },
    'ieee': {
        'accent': '#000000',
        'heading': '#000000',
        'serif_body': True,
        'label': 'IEEE Conference/Journal',
    },
    'cn-paper': {
        'accent': '#000000',
        'heading': '#000000',
        'serif_body': True,
        'label': '中文学术论文',
    },
    'working-paper': {
        'accent': '#333333',
        'heading': '#000000',
        'serif_body': True,
        'label': 'Working Paper (SSRN)',
    },
}


def _escape_typst(text: str) -> str:
    """转义 Typst 特殊字符"""
    if not isinstance(text, str):
        text = str(text)
    # < > 在 typst 中是 label 语法，需转义
    text = text.replace('<', '\\<').replace('>', '\\>')
    # // 是注释，URL 中需转义
    text = text.replace('://', ':\\/\\/')
    # # 是函数/标题前缀，在正文中需转义
    # 但我们在生成模板时主动用 #，所以只转义内容中的
    return text


def _generate_charts(data: Dict, work_dir: str, theme_name: str) -> Dict[str, str]:
    """生成报告中引用的所有图表，返回 {chart_id: png_path}"""
    chart_paths = {}
    charts = data.get('charts', [])
    for i, chart_def in enumerate(charts):
        chart_id = chart_def.get('id', f'chart_{i}')
        chart_type = chart_def.get('type', 'bar')
        chart_data = chart_def.get('data', {})
        # 确保图表有标题
        if 'title' not in chart_data:
            chart_data['title'] = chart_def.get('title', '')

        out_path = os.path.join(work_dir, f'{chart_id}.png')
        try:
            # 映射主题：cicc/ms/cms/dachen → 图表引擎主题
            chart_theme = 'default'
            if theme_name == 'cicc':
                chart_theme = 'cicc'
            elif theme_name in ('ms', 'cms'):
                chart_theme = 'goldman'
            elif theme_name == 'dachen':
                chart_theme = 'default'

            render_chart(chart_type, chart_data, out_path, chart_theme)
            chart_paths[chart_id] = out_path
        except Exception as e:
            print(f"  WARNING: Chart '{chart_id}' ({chart_type}) failed: {e}")
    return chart_paths


def _generate_ai_images(data: Dict, work_dir: str) -> Dict[str, str]:
    """生成 AI 配图（ai-image section type 引用的图片），返回 {image_id: png_path}"""
    ai_images = data.get('illustrations', [])
    if not ai_images:
        return {}

    try:
        from render_illustrate import generate_illustration
    except ImportError:
        try:
            from scripts.render_illustrate import generate_illustration
        except ImportError:
            print("  WARNING: render_illustrate not available, skipping AI images")
            return {}

    paths = {}
    for i, img_def in enumerate(ai_images):
        img_id = img_def.get('id', f'ai_img_{i}')
        content = img_def.get('content', '')
        style = img_def.get('style', 'gradient-glass')
        title = img_def.get('title', '')
        out_path = os.path.join(work_dir, f'{img_id}.png')
        try:
            result = generate_illustration(content, out_path, style, title)
            if result:
                paths[img_id] = out_path
        except Exception as e:
            print(f"  WARNING: AI image '{img_id}' failed: {e}")
    return paths


def _build_cover(data: Dict, theme: Dict) -> str:
    """生成封面 Typst 代码"""
    title_zh = _escape_typst(data.get('title', '研究报告'))
    title_en = _escape_typst(data.get('title_en', ''))
    author = _escape_typst(data.get('author', ''))
    date = _escape_typst(data.get('date', ''))
    version = _escape_typst(data.get('version', ''))

    return f"""#cover-page(
  title-zh: "{title_zh}",
  title-en: "{title_en}",
  author: "{author}",
  date: "{date}",
  version: "{version}",
)
"""


def _build_section(section: Dict, chart_paths: Dict, depth: int = 1) -> str:
    """递归生成章节内容"""
    lines = []
    sec_type = section.get('type', 'heading')

    if sec_type == 'heading':
        prefix = '=' * depth
        title = _escape_typst(section.get('title', ''))
        lines.append(f'\n{prefix} {title}\n')
        # 首段取消缩进
        content = section.get('content', '')
        if content:
            lines.append(f'#par(first-line-indent: 0em)[{_escape_typst(content)}]\n')

    elif sec_type == 'paragraph':
        content = _escape_typst(section.get('content', ''))
        lines.append(f'\n{content}\n')

    elif sec_type == 'quote':
        content = _escape_typst(section.get('content', ''))
        lines.append(f'\n#quote[{content}]\n')

    elif sec_type == 'table':
        lines.append(_build_table(section))

    elif sec_type == 'chart':
        chart_id = section.get('chart_id', '')
        caption = _escape_typst(section.get('caption', ''))
        width = section.get('width', '85%')
        if chart_id in chart_paths:
            # Typst 需要相对路径（相对于 .typ 文件所在目录）
            png_filename = os.path.basename(chart_paths[chart_id])
            lines.append(f'\n#align(center)[\n  #image("{png_filename}", width: {width})\n]\n')
            if caption:
                lines.append(f'#align(center)[#text(size: 9pt, fill: rgb("#666666"))[{caption}]]\n')

    elif sec_type == 'ai-image':
        # AI 配图：渲染时由外部预生成，这里只嵌入图片
        img_id = section.get('image_id', '')
        caption = _escape_typst(section.get('caption', ''))
        width = section.get('width', '85%')
        if img_id in chart_paths:
            png_filename = os.path.basename(chart_paths[img_id])
            lines.append(f'\n#align(center)[\n  #image("{png_filename}", width: {width})\n]\n')
            if caption:
                lines.append(f'#align(center)[#text(size: 9pt, fill: rgb("#666666"))[{caption}]]\n')

    elif sec_type == 'kpi':
        lines.append(_build_kpi(section))

    elif sec_type == 'pagebreak':
        lines.append('\n#pagebreak()\n')

    # 递归处理子章节
    for child in section.get('children', []):
        lines.append(_build_section(child, chart_paths, depth + 1))

    return '\n'.join(lines)


def _build_table(section: Dict) -> str:
    """生成 Typst 表格"""
    headers = section.get('headers', [])
    rows = section.get('rows', [])
    cols = len(headers) if headers else (len(rows[0]) if rows else 2)

    lines = [f'\n#table(']
    lines.append(f'  columns: {cols},')
    lines.append(f'  align: ({"center, " * cols}),')

    # 表头
    if headers:
        for h in headers:
            lines.append(f'  table.cell(fill: heading-color)[#text(fill: white)[{_escape_typst(h)}]],')

    # 数据行
    for row in rows:
        for cell in row:
            lines.append(f'  [{_escape_typst(cell)}],')

    lines.append(')\n')
    return '\n'.join(lines)


def _build_kpi(section: Dict) -> str:
    """生成 KPI 指标卡片"""
    metrics = section.get('metrics', [])
    cols = len(metrics)
    if cols == 0:
        return ''

    lines = ['\n#grid(']
    lines.append(f'  columns: ({", ".join(["1fr"] * cols)}),')
    lines.append('  gutter: 12pt,')
    for m in metrics:
        label = _escape_typst(m.get('label', ''))
        value = _escape_typst(m.get('value', ''))
        change = m.get('change', '')
        change_color = '#38a169' if str(change).startswith('+') else '#e53e3e' if str(change).startswith('-') else '#666666'
        lines.append(f'  align(center)[')
        lines.append(f'    #text(size: 9pt, fill: rgb("#888888"))[{label}]')
        lines.append(f'    #linebreak()')
        lines.append(f'    #text(size: 20pt, weight: "bold", fill: heading-color)[{value}]')
        if change:
            lines.append(f'    #linebreak()')
            lines.append(f'    #text(size: 9pt, fill: rgb("{change_color}"))[{_escape_typst(str(change))}]')
        lines.append(f'  ],')
    lines.append(')\n')
    return '\n'.join(lines)


def _build_disclaimer(data: Dict) -> str:
    """免责声明"""
    text = data.get('disclaimer', '')
    if not text:
        return ''
    return f"""
#pagebreak()
= 免责声明

#set text(size: 8pt, fill: rgb("#888888"))
#par(first-line-indent: 0em)[{_escape_typst(text)}]
"""


def generate_typ(data: Dict, chart_paths: Dict, theme_name: str = 'cicc') -> str:
    """
    从 JSON 数据生成完整的 .typ 源文件。

    data 结构:
    {
        "title": "报告标题",
        "title_en": "English Title",
        "author": "DeerFlow Research",
        "date": "2026-04-07",
        "version": "v1.0",
        "theme": "cicc",
        "sections": [
            {"type": "heading", "title": "章节标题", "content": "正文...", "children": [...]},
            {"type": "table", "headers": [...], "rows": [...]},
            {"type": "chart", "chart_id": "revenue_bar", "caption": "..."},
            {"type": "quote", "content": "核心观点"},
            {"type": "kpi", "metrics": [{"label": "...", "value": "...", "change": "+5%"}]},
        ],
        "charts": [
            {"id": "revenue_bar", "type": "bar", "data": {...}},
        ],
        "disclaimer": "..."
    }
    """
    theme = THEMES.get(theme_name, THEMES['cicc'])

    # Typst 文件头：引入模板参数
    typ_lines = []
    typ_lines.append('// Auto-generated by typeset-engine render_pdf.py')
    typ_lines.append(f'// Theme: {theme_name}\n')

    # 页面设置（从 cicc-report.typ 模板内联，支持主题切换）
    accent = theme['accent']
    heading = theme['heading']
    title_zh = _escape_typst(data.get('title', '研究报告'))
    author = _escape_typst(data.get('author', ''))

    font_stack = (
        '("Noto Serif CJK SC", "Noto Sans CJK SC", "DejaVu Serif")'
        if theme['serif_body']
        else '("Noto Sans CJK SC", "Noto Serif CJK SC", "DejaVu Sans")'
    )

    typ_lines.append(f'#let accent-color = rgb("{accent}")')
    typ_lines.append(f'#let heading-color = rgb("{heading}")')
    typ_lines.append('')

    # 文档 + 页面
    typ_lines.append(f'#set document(title: "{title_zh}", author: "{author}")')
    typ_lines.append(f'''
#set page(
  paper: "a4",
  margin: (top: 2.5cm, bottom: 2.5cm, left: 2.2cm, right: 2.2cm),
  header: context {{
    if counter(page).get().first() > 1 {{
      set text(size: 8pt, fill: rgb("#666666"))
      grid(
        columns: (1fr, 1fr),
        align(left)[{title_zh}],
        align(right)[{author}],
      )
      line(length: 100%, stroke: 0.5pt + rgb("#cccccc"))
    }}
  }},
  footer: context {{
    set text(size: 8pt, fill: rgb("#888888"))
    align(center)[— #counter(page).display() —]
  }},
)
''')

    # 字体 + 段落
    typ_lines.append(f'#set text(font: {font_stack}, size: 10.5pt, lang: "zh", region: "cn")')
    typ_lines.append('#set par(justify: true, leading: 0.85em, first-line-indent: 2em)')
    typ_lines.append('#set heading(numbering: none)')
    typ_lines.append('')

    # 标题样式
    typ_lines.append(f'''
#show heading.where(level: 1): it => {{
  set text(size: 18pt, weight: "bold", fill: heading-color)
  set par(first-line-indent: 0em)
  v(0.8em)
  block(it.body)
  v(0.3em)
  line(length: 100%, stroke: 2pt + accent-color)
  v(0.5em)
}}

#show heading.where(level: 2): it => {{
  set text(size: 14pt, weight: "bold", fill: heading-color)
  set par(first-line-indent: 0em)
  v(0.6em)
  block(it.body)
  v(0.2em)
  line(length: 60%, stroke: 1pt + accent-color)
  v(0.3em)
}}

#show heading.where(level: 3): it => {{
  set text(size: 12pt, weight: "bold", fill: rgb("#2d3436"))
  set par(first-line-indent: 0em)
  v(0.4em)
  block(it.body)
  v(0.2em)
}}
''')

    # 表格样式
    typ_lines.append('''
#set table(stroke: 0.5pt + rgb("#cccccc"), inset: 8pt)
#show table.cell.where(y: 0): set text(weight: "bold", fill: white, size: 9.5pt)
#show table.cell: set text(size: 9.5pt)
''')

    # 引用样式
    typ_lines.append(f'''
#show quote: it => {{
  set par(first-line-indent: 0em)
  block(
    width: 100%,
    inset: (left: 16pt, top: 10pt, bottom: 10pt, right: 12pt),
    stroke: (left: 3pt + accent-color),
    fill: rgb("#fdf2f2"),
    text(style: "italic", weight: "bold", size: 10pt, it.body),
  )
}}
''')

    # 封面函数
    typ_lines.append(f'''
#let cover-page(title-zh: "", title-en: "", author: "", date: "", version: "") = {{
  page(header: none, footer: none, margin: (top: 0cm, bottom: 0cm, left: 0cm, right: 0cm))[
    #block(width: 100%, height: 100%, fill: heading-color)[
      #v(6cm)
      #align(center)[
        #block(width: 80%)[
          #line(length: 100%, stroke: 2pt + accent-color)
          #v(1.5cm)
          #text(size: 32pt, weight: "bold", fill: white, tracking: 2pt)[#title-zh]
          #v(1.5cm)
          #line(length: 100%, stroke: 2pt + accent-color)
          #v(1.2cm)
          #text(size: 14pt, fill: rgb("#aaaaaa"), weight: "regular")[#title-en]
          #v(2cm)
          #text(size: 12pt, fill: rgb("#cccccc"))[#author]
          #v(0.5cm)
          #text(size: 11pt, fill: rgb("#888888"))[#date #if version != "" [· #version]]
        ]
      ]
    ]
  ]
}}
''')

    # ── 封面 ──
    typ_lines.append(_build_cover(data, theme))

    # ── 目录 ──
    if data.get('toc', True):
        typ_lines.append('''
#page(header: none)[
  #v(2cm)
  #align(center)[#text(size: 20pt, weight: "bold", fill: heading-color)[目 录]]
  #v(1cm)
  #outline(title: none, indent: 1.5em, depth: 3)
]
''')

    # ── 正文章节 ──
    for section in data.get('sections', []):
        typ_lines.append(_build_section(section, chart_paths, depth=1))

    # ── 免责声明 ──
    typ_lines.append(_build_disclaimer(data))

    return '\n'.join(typ_lines)


def _generate_gongwen_typ(data: Dict) -> str:
    """生成公文 Typst 源文件（GB/T 9704 格式）。

    公文 JSON 格式：
    {
        "organ": "国务院办公厅",
        "doc_type": "文件",           // 或 "" 表示不显示
        "number": "国办发〔2026〕1号",
        "signer": "",                 // 上行文才需要
        "title": "关于XX的通知",
        "recipient": "各省、自治区、直辖市人民政府",
        "sections": [
            {"type": "paragraph", "content": "正文内容..."},
            {"type": "heading", "title": "一、第一部分", "children": [...]},
        ],
        "signature_organ": "国务院办公厅",
        "signature_date": "2026年4月12日",
        "cc": "各部委",
        "printer": "国务院办公厅秘书局",
        "print_date": "2026年4月12日印发",
        "copies": "200"
    }
    """
    d = data
    lines = []

    # 导入公文模板
    lines.append('#import "/templates/gongwen.typ": *')
    lines.append('')

    # 正文内容先生成
    body_lines = []
    for section in d.get('sections', []):
        stype = section.get('type', 'paragraph')
        if stype == 'paragraph':
            text = _escape_typst(section.get('content', ''))
            # 支持 \n\n 分段
            for para in text.split('\\n\\n'):
                para = para.strip()
                if para:
                    body_lines.append(f'{para}')
                    body_lines.append('')
        elif stype == 'heading':
            title = _escape_typst(section.get('title', ''))
            body_lines.append(f'= {title}')
            body_lines.append('')
            for child in section.get('children', []):
                ctype = child.get('type', 'paragraph')
                if ctype == 'paragraph':
                    text = _escape_typst(child.get('content', ''))
                    body_lines.append(f'{text}')
                    body_lines.append('')
                elif ctype == 'heading':
                    ctitle = _escape_typst(child.get('title', ''))
                    body_lines.append(f'== {ctitle}')
                    body_lines.append('')
                    for gc in child.get('children', []):
                        if gc.get('type') == 'paragraph':
                            body_lines.append(f'{_escape_typst(gc.get("content", ""))}')
                            body_lines.append('')
                        elif gc.get('type') == 'heading':
                            body_lines.append(f'=== {_escape_typst(gc.get("title", ""))}')
                            body_lines.append('')

    body_content = '\n'.join(body_lines)

    # 组装公文函数调用
    lines.append('#show: gongwen.with(')
    lines.append(f'  organ: "{_escape_typst(d.get("organ", "XX机关"))}",')
    lines.append(f'  doc-type: "{_escape_typst(d.get("doc_type", "文件"))}",')
    redhead_size = d.get('redhead_size', 30)
    lines.append(f'  redhead-size: {redhead_size}pt,')
    if d.get('number'):
        lines.append(f'  number: "{_escape_typst(d["number"])}",')
    if d.get('signer'):
        lines.append(f'  signer: "{_escape_typst(d["signer"])}",')
    lines.append(f'  title: "{_escape_typst(d.get("title", ""))}",')
    if d.get('recipient'):
        lines.append(f'  recipient: "{_escape_typst(d["recipient"])}",')
    if d.get('signature_organ'):
        lines.append(f'  signature-organ: "{_escape_typst(d["signature_organ"])}",')
    if d.get('signature_date'):
        lines.append(f'  signature-date: "{_escape_typst(d["signature_date"])}",')
    if d.get('attachments'):
        att_items = ', '.join(f'"{_escape_typst(a)}"' for a in d['attachments'])
        lines.append(f'  attachments: ({att_items}),')
    if d.get('cc'):
        lines.append(f'  cc: "{_escape_typst(d["cc"])}",')
    if d.get('printer'):
        lines.append(f'  printer: "{_escape_typst(d["printer"])}",')
    if d.get('print_date'):
        lines.append(f'  print-date: "{_escape_typst(d["print_date"])}",')
    if d.get('copies'):
        lines.append(f'  copies: "{_escape_typst(d["copies"])}",')
    lines.append(')')
    lines.append('')
    lines.append(body_content)

    return '\n'.join(lines)


def _generate_academic_typ(data: Dict, template: str) -> str:
    """生成学术论文 Typst 源文件。

    学术论文 JSON 格式：
    {
        "template": "ieee" | "cn-paper" | "working-paper",
        "title": "论文标题",
        "authors": [
            {"name": "张三", "department": "计算机系", "organization": "北京大学", "email": "zhang@pku.edu.cn"}
        ],
        "abstract": "摘要内容",
        "keywords": ["关键词1", "关键词2"],
        "sections": [
            {"type": "heading", "title": "引言", "children": [
                {"type": "paragraph", "content": "正文内容"}
            ]}
        ]
    }
    """
    d = data
    lines = []

    # 导入模板
    template_map = {
        'ieee': '/templates/academic/ieee/lib.typ',
        'cn-paper': '/templates/academic/cn-paper/lib.typ',
        'working-paper': '/templates/academic/working-paper/lib.typ',
    }
    template_path = template_map.get(template, template_map['ieee'])

    if template == 'ieee':
        lines.append(f'#import "{template_path}": ieee')
        lines.append('')
        lines.append('#show: ieee.with(')
        lines.append(f'  title: [{_escape_typst(d.get("title", "Paper Title"))}],')

        # Authors
        authors = d.get('authors', [])
        if authors:
            lines.append('  authors: (')
            for a in authors:
                lines.append('    (')
                lines.append(f'      name: "{_escape_typst(a.get("name", ""))}",')
                if a.get('department'):
                    lines.append(f'      department: [{_escape_typst(a["department"])}],')
                if a.get('organization'):
                    lines.append(f'      organization: [{_escape_typst(a["organization"])}],')
                if a.get('location'):
                    lines.append(f'      location: [{_escape_typst(a["location"])}],')
                if a.get('email'):
                    lines.append(f'      email: "{a["email"]}",')
                lines.append('    ),')
            lines.append('  ),')

        # Abstract
        abstract = d.get('abstract', '')
        if abstract:
            lines.append(f'  abstract: [{_escape_typst(abstract)}],')

        # Index terms / keywords
        keywords = d.get('keywords', [])
        if keywords:
            terms = ', '.join(f'"{_escape_typst(k)}"' for k in keywords)
            lines.append(f'  index-terms: ({terms}),')

        lines.append('  paper-size: "a4",')
        lines.append(')')

    elif template == 'cn-paper':
        lines.append(f'#import "{template_path}": *')
        lines.append('')

        # cn-paper 用 easy-paper 的 show 函数
        title = _escape_typst(d.get('title', '论文标题'))
        lines.append(f'#show: easy-paper.with(')
        lines.append(f'  title: "{title}",')

        authors = d.get('authors', [])
        if authors:
            author_names = ', '.join(f'"{_escape_typst(a.get("name", ""))}"' for a in authors)
            lines.append(f'  author: ({author_names}),')

        abstract = d.get('abstract', '')
        if abstract:
            lines.append(f'  abstract: [{_escape_typst(abstract)}],')

        keywords = d.get('keywords', [])
        if keywords:
            kw_str = ', '.join(f'"{_escape_typst(k)}"' for k in keywords)
            lines.append(f'  keywords: ({kw_str}),')

        lines.append(')')

    elif template == 'working-paper':
        lines.append(f'#import "{template_path}": *')
        lines.append('')
        lines.append('#show: paper.with(')
        lines.append(f'  title: "{_escape_typst(d.get("title", "Working Paper"))}",')

        authors = d.get('authors', [])
        if authors:
            lines.append('  authors: (')
            for a in authors:
                lines.append('    (')
                lines.append(f'      name: "{_escape_typst(a.get("name", ""))}",')
                if a.get('affiliation'):
                    lines.append(f'      affiliation: "{_escape_typst(a["affiliation"])}",')
                if a.get('email'):
                    lines.append(f'      email: "{a["email"]}",')
                lines.append('    ),')
            lines.append('  ),')

        abstract = d.get('abstract', '')
        if abstract:
            lines.append(f'  abstract: [{_escape_typst(abstract)}],')

        keywords = d.get('keywords', [])
        if keywords:
            kw_str = ', '.join(f'"{_escape_typst(k)}"' for k in keywords)
            lines.append(f'  keywords: ({kw_str}),')

        lines.append('  date: datetime.today(),')
        lines.append(')')

    lines.append('')

    # 正文 sections
    for section in d.get('sections', []):
        lines.extend(_render_academic_section(section, level=1))

    return '\n'.join(lines)


def _render_academic_section(section: Dict, level: int = 1) -> List[str]:
    """递归渲染学术论文的 section"""
    lines = []
    stype = section.get('type', 'paragraph')

    if stype == 'heading':
        prefix = '=' * level
        title = _escape_typst(section.get('title', ''))
        lines.append(f'{prefix} {title}')
        lines.append('')
        for child in section.get('children', []):
            lines.extend(_render_academic_section(child, level=level + 1))
    elif stype == 'paragraph':
        text = _escape_typst(section.get('content', ''))
        lines.append(text)
        lines.append('')
    elif stype == 'quote':
        text = _escape_typst(section.get('content', ''))
        lines.append(f'#quote[{text}]')
        lines.append('')
    elif stype == 'table':
        headers = section.get('headers', [])
        rows = section.get('rows', [])
        if headers:
            cols = len(headers)
            lines.append(f'#figure(')
            lines.append(f'  table(')
            lines.append(f'    columns: {cols},')
            lines.append(f'    table.header{tuple(_escape_typst(h) for h in headers)},')
            for row in rows:
                cells = ', '.join(f'[{_escape_typst(c)}]' for c in row)
                lines.append(f'    {cells},')
            lines.append(f'  ),')
            caption = section.get('caption', '')
            if caption:
                lines.append(f'  caption: [{_escape_typst(caption)}],')
            lines.append(f')')
            lines.append('')

    return lines


def render_pdf(data: Dict, output: str, template: str = 'default',
               theme: str = 'cicc') -> str:
    """
    统一 PDF 渲染入口。

    Args:
        data: 报告数据字典（见 generate_typ 文档）
        output: 输出 PDF 路径
        template: 模板名（预留，暂时只用内联模板）
        theme: 主题名 (cicc/ms/cms/dachen)

    Returns:
        输出 PDF 路径
    """
    os.makedirs(os.path.dirname(output) or '.', exist_ok=True)

    # 使用临时目录存放中间文件
    with tempfile.TemporaryDirectory(prefix='typeset_pdf_') as work_dir:

        if theme in ('ieee', 'cn-paper', 'working-paper'):
            # ── 学术论文模式 ──
            typ_content = _generate_academic_typ(data, theme)
            ac_dir = os.path.join('/app', 'output', '_academic_tmp')
            os.makedirs(ac_dir, exist_ok=True)
            typ_path = os.path.join(ac_dir, 'paper.typ')
            with open(typ_path, 'w', encoding='utf-8') as f:
                f.write(typ_content)

            result = subprocess.run(
                ['typst', 'compile', '--root', '/app', typ_path, output],
                capture_output=True, text=True, timeout=60,
            )
            try:
                os.unlink(typ_path)
            except OSError:
                pass

            if result.returncode != 0:
                raise RuntimeError(f"Typst compile failed:\n{result.stderr}")

            print(f"  Academic PDF ({theme}) generated: {output} ({os.path.getsize(output):,} bytes)")
            return output

        if theme in ('gongwen', 'tbs'):
            # ── 公文模式：使用 gongwen.typ 模板 ──
            if theme == 'tbs':
                # 电广传媒预设
                data.setdefault('organ', '湖南电广传媒股份有限公司')
                data.setdefault('doc_type', '')
                data.setdefault('redhead_size', 36)
                data.setdefault('signature_organ', '湖南电广传媒股份有限公司')
            typ_content = _generate_gongwen_typ(data)
            # 必须在 /app 目录树内，typst --root /app 才能解析 import
            gw_dir = os.path.join('/app', 'output', '_gongwen_tmp')
            os.makedirs(gw_dir, exist_ok=True)
            typ_path = os.path.join(gw_dir, 'report.typ')
            with open(typ_path, 'w', encoding='utf-8') as f:
                f.write(typ_content)

            # typst compile（--root /app 以解析 /app/templates/ 路径）
            result = subprocess.run(
                ['typst', 'compile', '--root', '/app', typ_path, output],
                capture_output=True, text=True, timeout=60,
            )
            # 清理临时文件
            try:
                os.unlink(typ_path)
            except OSError:
                pass

            if result.returncode != 0:
                raise RuntimeError(f"Typst compile failed:\n{result.stderr}")

            print(f"  Gongwen PDF generated: {output} ({os.path.getsize(output):,} bytes)")
            return output

        # ── 研报模式（cicc/ms/cms/dachen）──
        # 1. 生成图表
        chart_paths = _generate_charts(data, work_dir, theme)
        print(f"  Charts generated: {len(chart_paths)}")

        # AI 配图
        ai_paths = _generate_ai_images(data, work_dir)
        if ai_paths:
            print(f"  AI images generated: {len(ai_paths)}")
            chart_paths.update(ai_paths)

        # 2. 生成 .typ 源文件
        typ_content = generate_typ(data, chart_paths, theme)
        typ_path = os.path.join(work_dir, 'report.typ')
        with open(typ_path, 'w', encoding='utf-8') as f:
            f.write(typ_content)

        # 3. typst compile
        result = subprocess.run(
            ['typst', 'compile', typ_path, output],
            capture_output=True, text=True, timeout=60,
        )
        if result.returncode != 0:
            raise RuntimeError(f"Typst compile failed:\n{result.stderr}")

        print(f"  PDF generated: {output} ({os.path.getsize(output):,} bytes)")

    return output


if __name__ == '__main__':
    import click

    @click.command()
    @click.option('--data', required=True, help='Input JSON data file')
    @click.option('--output', required=True, help='Output PDF path')
    @click.option('--theme', default='cicc',
                  type=click.Choice(['cicc', 'ms', 'cms', 'dachen', 'gongwen', 'tbs',
                                     'ieee', 'cn-paper', 'working-paper']))
    def main(data, output, theme):
        with open(data) as f:
            d = json.load(f)
        render_pdf(d, output, theme=theme)
        click.echo(f"OK: {output}")

    main()
