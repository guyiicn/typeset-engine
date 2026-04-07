#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
typeset-engine 主入口 — 文档渲染引擎。

用法（通过 docker exec）:
  # PDF
  python engine.py pdf --template cicc --data input.json --output report.pdf

  # PPTX
  python engine.py pptx --template equity_research --data input.json --output report.pptx

  # DOCX
  python engine.py docx --template report --data input.json --output report.docx

  # 字体列表
  python engine.py fonts --lang zh

  # 文件对比
  python engine.py diff --old v1.pdf --new v2.pdf --output diff_report.png
  python engine.py diff --old v1.pdf --new v2.pdf --mode text
"""

import click
import json
import os
import sys
from pathlib import Path

TEMPLATES_DIR = Path(__file__).parent.parent / 'templates'
OUTPUT_DIR = Path('/app/output')


@click.group()
def cli():
    """Typeset Engine — PDF/PPTX/DOCX 渲染引擎"""
    pass


# ═══════════════════════════════════════════
# 字体管理
# ═══════════════════════════════════════════
@cli.command()
@click.option('--lang', default=None, help='Filter by language (zh/ja/ko)')
@click.option('--family', default=None, help='Filter by family name')
def fonts(lang, family):
    """列出可用字体"""
    import matplotlib.font_manager as fm

    all_fonts = sorted(set(f.name for f in fm.fontManager.ttflist))

    if lang == 'zh':
        keywords = ['CJK', 'SC', 'CN', 'GB', 'Hei', 'Song', 'Kai', 'Ming',
                     'WenQuanYi', 'FZ', 'HarmonyOS', 'Droid']
        all_fonts = [f for f in all_fonts if any(k.lower() in f.lower() for k in keywords)]
    if family:
        all_fonts = [f for f in all_fonts if family.lower() in f.lower()]

    click.echo(f"Available fonts ({len(all_fonts)}):")
    for f in all_fonts:
        click.echo(f"  {f}")


# ═══════════════════════════════════════════
# PDF 渲染
# ═══════════════════════════════════════════
@cli.command()
@click.option('--template', default='default', help='Template name')
@click.option('--data', required=True, help='Input JSON data file')
@click.option('--output', required=True, help='Output PDF path')
@click.option('--theme', default='default', help='Theme: default/cicc')
def pdf(template, data, output, theme):
    """渲染 PDF 文档"""
    from scripts.render_pdf import render_pdf
    with open(data) as f:
        data_dict = json.load(f)
    render_pdf(data_dict, output, template=template, theme=theme)
    click.echo(f"✅ PDF: {output}")


# ═══════════════════════════════════════════
# PPTX 渲染
# ═══════════════════════════════════════════
@cli.command()
@click.option('--template', default='default', help='Template name')
@click.option('--data', required=True, help='Input JSON data file')
@click.option('--output', required=True, help='Output PPTX path')
def pptx(template, data, output):
    """渲染 PPTX 演示文稿"""
    from scripts.render_pptx import render_pptx
    with open(data) as f:
        data_dict = json.load(f)
    render_pptx(data_dict, output, template=template)
    click.echo(f"✅ PPTX: {output}")


# ═══════════════════════════════════════════
# DOCX 渲染
# ═══════════════════════════════════════════
@cli.command()
@click.option('--template', default='default', help='Template name')
@click.option('--data', required=True, help='Input JSON data file')
@click.option('--output', required=True, help='Output DOCX path')
@click.option('--theme', default='cicc', help='Theme: cicc/ms/cms/dachen')
def docx(template, data, output, theme):
    """渲染 DOCX 文档"""
    from scripts.render_docx import render_docx
    with open(data) as f:
        data_dict = json.load(f)
    render_docx(data_dict, output, template=template, theme=theme)
    click.echo(f"✅ DOCX: {output}")


# ═══════════════════════════════════════════
# 文件对比
# ═══════════════════════════════════════════
# ═══════════════════════════════════════════
# 图表渲染
# ═══════════════════════════════════════════
@cli.command()
@click.option('--type', 'chart_type', required=True,
               type=click.Choice(['bar', 'line', 'area', 'pie', 'waterfall', 'scatter',
                                   'heatmap', 'radar', 'funnel', 'gauge', 'treemap',
                                   'candlestick', 'combo']),
               help='Chart type')
@click.option('--data', required=True, help='Input JSON data file')
@click.option('--output', required=True, help='Output image path (.png/.svg)')
@click.option('--theme', default='default', help='Theme: default/cicc/goldman/dark')
def chart(chart_type, data, output, theme):
    """渲染商业图表"""
    from scripts.render_charts import render_chart
    with open(data) as f:
        data_dict = json.load(f)
    render_chart(chart_type, data_dict, output, theme)
    click.echo(f"✅ Chart ({chart_type}): {output}")


# ═══════════════════════════════════════════
# AI PPT（Gemini 图片生成 + FFmpeg 视频）
# ═══════════════════════════════════════════
@cli.command('pptx-ai')
@click.option('--data', required=True, help='Input slides_plan JSON file')
@click.option('--output', required=True, help='Output directory')
@click.option('--style', default='gradient-glass',
              help='Style: gradient-glass / vector-illustration / custom .md name')
@click.option('--resolution', default='2K', type=click.Choice(['2K', '4K']))
@click.option('--video/--no-video', default=True, help='Generate MP4 video')
@click.option('--duration', default=3.0, help='Seconds per slide in video')
@click.option('--transition', default='fade',
              help='Video transition: fade/dissolve/wipeleft/slideright/none')
def pptx_ai(data, output, style, resolution, video, duration, transition):
    """AI 风格 PPT — Gemini 生成精美幻灯片 + HTML 播放器 + MP4 视频"""
    from scripts.render_pptx_ai import render_pptx_ai
    with open(data) as f:
        data_dict = json.load(f)
    result = render_pptx_ai(data_dict, output, style, resolution, video, duration, transition)
    click.echo(f"✅ AI PPT: {len(result['images'])} slides → {output}")


@cli.command('styles')
def styles():
    """列出可用的 AI PPT 风格"""
    from scripts.render_pptx_ai import list_styles
    for s in list_styles():
        click.echo(f"  {s['id']:25s} — {s['name']}")


# ═══════════════════════════════════════════
# AI 配图（Gemini 生成文档插图）
# ═══════════════════════════════════════════
@cli.command()
@click.option('--content', required=True, help='Text content to illustrate')
@click.option('--output', required=True, help='Output image path (.png)')
@click.option('--style', default='gradient-glass',
              help='Style: gradient-glass / vector-illustration / ticket')
@click.option('--title', default='', help='Optional title overlay')
@click.option('--ratio', default='16:9', help='Aspect ratio: 16:9 / 3:4 / 1:1')
@click.option('--cover', is_flag=True, help='Generate as cover image')
def illustrate(content, output, style, title, ratio, cover):
    """AI 配图 — Gemini 生成文档插图"""
    from scripts.render_illustrate import generate_illustration
    result = generate_illustration(content, output, style, title, ratio, cover)
    if result:
        click.echo(f"✅ Illustration: {result}")
    else:
        click.echo("❌ Generation failed", err=True)


# ═══════════════════════════════════════════
# 文件对比
# ═══════════════════════════════════════════
@cli.command()
@click.option('--old', 'old_file', required=True, help='Old file path')
@click.option('--new', 'new_file', required=True, help='New file path')
@click.option('--output', default=None, help='Output diff report path')
@click.option('--mode', default='visual', type=click.Choice(['visual', 'text', 'both']),
              help='Diff mode: visual (screenshot diff), text (content diff), both')
def diff(old_file, new_file, output, mode):
    """对比两个文档版本"""
    from scripts.file_diff import compare_files
    result = compare_files(old_file, new_file, output, mode)
    click.echo(result)


if __name__ == '__main__':
    cli()
