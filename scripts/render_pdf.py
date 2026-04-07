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
        # 1. 生成图表
        chart_paths = _generate_charts(data, work_dir, theme)
        print(f"  Charts generated: {len(chart_paths)}")

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
                  type=click.Choice(['cicc', 'ms', 'cms', 'dachen']))
    def main(data, output, theme):
        with open(data) as f:
            d = json.load(f)
        render_pdf(d, output, theme=theme)
        click.echo(f"OK: {output}")

    main()
