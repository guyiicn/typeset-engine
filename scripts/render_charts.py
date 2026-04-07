#!/usr/bin/env python3
"""
商业图表引擎 — 基于 Plotly + Kaleido，支持主题配色和中文。

图表类型:
  bar          — 柱状图（单/多系列）
  line         — 折线图
  area         — 面积图
  pie          — 饼图 / 环形图
  waterfall    — 瀑布图（收入分解）
  scatter      — 散点图
  heatmap      — 热力图（相关性矩阵）
  radar        — 雷达图（多维对比）
  funnel       — 漏斗图
  gauge        — 仪表盘（KPI）
  treemap      — 矩形树图（市值占比）
  candlestick  — K线图
  combo        — 组合图（柱+线）

用法:
  docker exec typeset-engine python scripts/render_charts.py \\
    --type bar --data input.json --output chart.png --theme cicc
"""

import json
import os
from typing import Dict, List, Optional, Any

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

# ═══════════════════════════════════════════
# 主题配色
# ═══════════════════════════════════════════

CHART_THEMES = {
    'default': {
        'colors': ['#1a365d', '#c9a227', '#4a5568', '#2b6cb0', '#e53e3e', '#38a169'],
        'bg': 'white',
        'grid': '#e2e8f0',
        'text': '#2d3748',
        'font': 'Noto Sans CJK SC, Arial',
        'template': 'plotly_white',
    },
    'cicc': {
        'colors': ['#C41E3A', '#8B0000', '#333333', '#666666', '#999999', '#CC6666'],
        'bg': 'white',
        'grid': '#f0f0f0',
        'text': '#333333',
        'font': 'Noto Sans CJK SC, Arial',
        'template': 'plotly_white',
    },
    'goldman': {
        'colors': ['#003A70', '#6B8E23', '#4A90D9', '#2E5090', '#7EB26D', '#EAB839'],
        'bg': 'white',
        'grid': '#e8e8e8',
        'text': '#333333',
        'font': 'Arial',
        'template': 'plotly_white',
    },
    'dark': {
        'colors': ['#00d4aa', '#ff6b6b', '#4ecdc4', '#45b7d1', '#f9ca24', '#a29bfe'],
        'bg': '#1a1a2e',
        'grid': '#2a2a4e',
        'text': '#e0e0e0',
        'font': 'Noto Sans CJK SC, Arial',
        'template': 'plotly_dark',
    },
}


def _get_theme(name: str) -> Dict:
    return CHART_THEMES.get(name, CHART_THEMES['default'])


def _base_layout(title: str, theme: Dict, width: int = 900, height: int = 500) -> Dict:
    return dict(
        title=dict(text=title, font=dict(size=16, color=theme['text'])),
        font=dict(family=theme['font'], color=theme['text']),
        template=theme['template'],
        paper_bgcolor=theme['bg'],
        plot_bgcolor=theme['bg'],
        width=width,
        height=height,
        margin=dict(l=60, r=40, t=60, b=50),
    )


# ═══════════════════════════════════════════
# 图表类型实现
# ═══════════════════════════════════════════

def chart_bar(data: Dict, output: str, theme_name: str = 'default') -> str:
    """柱状图 — 支持多系列、堆叠、水平"""
    theme = _get_theme(theme_name)
    fig = go.Figure()

    series_list = data.get('series', [{'name': '', 'values': data.get('values', [])}])
    categories = data.get('categories', data.get('x', []))
    stacked = data.get('stacked', False)

    for i, s in enumerate(series_list):
        color = theme['colors'][i % len(theme['colors'])]
        orientation = 'h' if data.get('horizontal') else 'v'
        if orientation == 'h':
            fig.add_trace(go.Bar(y=categories, x=s['values'], name=s.get('name', ''),
                                  marker_color=color, orientation='h'))
        else:
            fig.add_trace(go.Bar(x=categories, y=s['values'], name=s.get('name', ''),
                                  marker_color=color))

    layout = _base_layout(data.get('title', ''), theme,
                           data.get('width', 900), data.get('height', 500))
    if stacked:
        layout['barmode'] = 'stack'
    fig.update_layout(**layout)
    fig.write_image(output)
    return output


def chart_line(data: Dict, output: str, theme_name: str = 'default') -> str:
    """折线图"""
    theme = _get_theme(theme_name)
    fig = go.Figure()

    series_list = data.get('series', [{'name': '', 'values': data.get('values', [])}])
    x = data.get('x', data.get('categories', list(range(len(series_list[0].get('values', []))))))

    for i, s in enumerate(series_list):
        color = theme['colors'][i % len(theme['colors'])]
        fig.add_trace(go.Scatter(x=x, y=s['values'], name=s.get('name', ''),
                                  mode='lines+markers', line=dict(color=color, width=2),
                                  marker=dict(size=6)))

    fig.update_layout(**_base_layout(data.get('title', ''), theme,
                                      data.get('width', 900), data.get('height', 500)))
    fig.write_image(output)
    return output


def chart_area(data: Dict, output: str, theme_name: str = 'default') -> str:
    """面积图"""
    theme = _get_theme(theme_name)
    fig = go.Figure()

    series_list = data.get('series', [{'name': '', 'values': data.get('values', [])}])
    x = data.get('x', list(range(len(series_list[0].get('values', [])))))

    for i, s in enumerate(series_list):
        color = theme['colors'][i % len(theme['colors'])]
        fig.add_trace(go.Scatter(x=x, y=s['values'], name=s.get('name', ''),
                                  fill='tozeroy' if i == 0 else 'tonexty',
                                  line=dict(color=color)))

    fig.update_layout(**_base_layout(data.get('title', ''), theme,
                                      data.get('width', 900), data.get('height', 500)))
    fig.write_image(output)
    return output


def chart_pie(data: Dict, output: str, theme_name: str = 'default') -> str:
    """饼图/环形图"""
    theme = _get_theme(theme_name)
    hole = data.get('hole', 0.4) if data.get('donut', True) else 0

    fig = go.Figure(data=[go.Pie(
        labels=data.get('labels', []),
        values=data.get('values', []),
        hole=hole,
        marker=dict(colors=theme['colors'][:len(data.get('labels', []))]),
        textinfo='label+percent',
        textfont=dict(size=12),
    )])

    fig.update_layout(**_base_layout(data.get('title', ''), theme,
                                      data.get('width', 700), data.get('height', 500)))
    fig.write_image(output)
    return output


def chart_waterfall(data: Dict, output: str, theme_name: str = 'default') -> str:
    """瀑布图 — 收入/利润分解"""
    theme = _get_theme(theme_name)

    fig = go.Figure(go.Waterfall(
        x=data.get('categories', []),
        y=data.get('values', []),
        measure=data.get('measures', ['relative'] * len(data.get('values', []))),
        connector=dict(line=dict(color=theme['colors'][1])),
        increasing=dict(marker=dict(color=theme['colors'][0])),
        decreasing=dict(marker=dict(color='#e53e3e')),
        totals=dict(marker=dict(color=theme['colors'][1])),
    ))

    fig.update_layout(**_base_layout(data.get('title', ''), theme,
                                      data.get('width', 900), data.get('height', 500)))
    fig.write_image(output)
    return output


def chart_scatter(data: Dict, output: str, theme_name: str = 'default') -> str:
    """散点图"""
    theme = _get_theme(theme_name)

    fig = go.Figure(go.Scatter(
        x=data.get('x', []),
        y=data.get('y', []),
        mode='markers+text',
        text=data.get('labels', []),
        textposition='top center',
        marker=dict(size=data.get('sizes', 10),
                     color=theme['colors'][0],
                     opacity=0.7),
    ))

    fig.update_layout(**_base_layout(data.get('title', ''), theme,
                                      data.get('width', 800), data.get('height', 600)))
    fig.write_image(output)
    return output


def chart_heatmap(data: Dict, output: str, theme_name: str = 'default') -> str:
    """热力图 — 相关性矩阵"""
    theme = _get_theme(theme_name)

    fig = go.Figure(go.Heatmap(
        z=data.get('values', []),
        x=data.get('x_labels', []),
        y=data.get('y_labels', []),
        colorscale='RdBu_r' if theme_name != 'dark' else 'Viridis',
        text=data.get('annotations', None),
        texttemplate='%{text}',
        textfont=dict(size=10),
    ))

    fig.update_layout(**_base_layout(data.get('title', ''), theme,
                                      data.get('width', 700), data.get('height', 600)))
    fig.write_image(output)
    return output


def chart_radar(data: Dict, output: str, theme_name: str = 'default') -> str:
    """雷达图 — 多维对比"""
    theme = _get_theme(theme_name)
    fig = go.Figure()

    categories = data.get('categories', [])
    for i, s in enumerate(data.get('series', [])):
        color = theme['colors'][i % len(theme['colors'])]
        values = s['values'] + [s['values'][0]]  # 闭合
        cats = categories + [categories[0]]
        fig.add_trace(go.Scatterpolar(
            r=values, theta=cats, name=s.get('name', ''),
            fill='toself', fillcolor=f'rgba{tuple(list(int(color.lstrip("#")[j:j+2], 16) for j in (0,2,4)) + [0.1])}',
            line=dict(color=color, width=2),
        ))

    layout = _base_layout(data.get('title', ''), theme,
                           data.get('width', 600), data.get('height', 600))
    layout['polar'] = dict(radialaxis=dict(visible=True, range=[0, max(max(s['values']) for s in data.get('series', [{'values':[100]}]))]))
    fig.update_layout(**layout)
    fig.write_image(output)
    return output


def chart_funnel(data: Dict, output: str, theme_name: str = 'default') -> str:
    """漏斗图"""
    theme = _get_theme(theme_name)

    fig = go.Figure(go.Funnel(
        y=data.get('stages', []),
        x=data.get('values', []),
        textinfo='value+percent initial',
        marker=dict(color=theme['colors'][:len(data.get('stages', []))]),
    ))

    fig.update_layout(**_base_layout(data.get('title', ''), theme,
                                      data.get('width', 700), data.get('height', 500)))
    fig.write_image(output)
    return output


def chart_gauge(data: Dict, output: str, theme_name: str = 'default') -> str:
    """仪表盘 — KPI 指标"""
    theme = _get_theme(theme_name)
    value = data.get('value', 0)
    max_val = data.get('max', 100)

    fig = go.Figure(go.Indicator(
        mode='gauge+number+delta',
        value=value,
        title=dict(text=data.get('label', ''), font=dict(size=18)),
        delta=dict(reference=data.get('reference', value * 0.9)),
        gauge=dict(
            axis=dict(range=[0, max_val]),
            bar=dict(color=theme['colors'][0]),
            steps=[
                dict(range=[0, max_val * 0.33], color='#f0f0f0'),
                dict(range=[max_val * 0.33, max_val * 0.66], color='#e8e8e8'),
                dict(range=[max_val * 0.66, max_val], color='#e0e0e0'),
            ],
            threshold=dict(line=dict(color=theme['colors'][1], width=4),
                           thickness=0.75, value=data.get('target', max_val * 0.8)),
        ),
    ))

    fig.update_layout(**_base_layout(data.get('title', ''), theme,
                                      data.get('width', 500), data.get('height', 400)))
    fig.write_image(output)
    return output


def chart_treemap(data: Dict, output: str, theme_name: str = 'default') -> str:
    """矩形树图 — 市值/占比可视化"""
    theme = _get_theme(theme_name)

    fig = go.Figure(go.Treemap(
        labels=data.get('labels', []),
        parents=data.get('parents', [''] * len(data.get('labels', []))),
        values=data.get('values', []),
        textinfo='label+value+percent root',
        marker=dict(colors=theme['colors'] * 5),
    ))

    fig.update_layout(**_base_layout(data.get('title', ''), theme,
                                      data.get('width', 800), data.get('height', 600)))
    fig.write_image(output)
    return output


def chart_candlestick(data: Dict, output: str, theme_name: str = 'default') -> str:
    """K线图"""
    theme = _get_theme(theme_name)

    fig = go.Figure(go.Candlestick(
        x=data.get('dates', []),
        open=data.get('open', []),
        high=data.get('high', []),
        low=data.get('low', []),
        close=data.get('close', []),
    ))

    fig.update_layout(**_base_layout(data.get('title', ''), theme,
                                      data.get('width', 1000), data.get('height', 500)))
    fig.update_layout(xaxis_rangeslider_visible=False)
    fig.write_image(output)
    return output


def chart_combo(data: Dict, output: str, theme_name: str = 'default') -> str:
    """组合图 — 柱状图 + 折线图"""
    theme = _get_theme(theme_name)
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    x = data.get('x', data.get('categories', []))
    bar_data = data.get('bar', {})
    line_data = data.get('line', {})

    fig.add_trace(go.Bar(x=x, y=bar_data.get('values', []),
                          name=bar_data.get('name', 'Bar'),
                          marker_color=theme['colors'][0]),
                   secondary_y=False)

    fig.add_trace(go.Scatter(x=x, y=line_data.get('values', []),
                              name=line_data.get('name', 'Line'),
                              mode='lines+markers',
                              line=dict(color=theme['colors'][1], width=3),
                              marker=dict(size=8)),
                   secondary_y=True)

    layout = _base_layout(data.get('title', ''), theme,
                           data.get('width', 900), data.get('height', 500))
    fig.update_layout(**layout)
    fig.update_yaxes(title_text=bar_data.get('name', ''), secondary_y=False)
    fig.update_yaxes(title_text=line_data.get('name', ''), secondary_y=True)
    fig.write_image(output)
    return output


# ═══════════════════════════════════════════
# 统一入口
# ═══════════════════════════════════════════

CHART_TYPES = {
    'bar': chart_bar,
    'line': chart_line,
    'area': chart_area,
    'pie': chart_pie,
    'waterfall': chart_waterfall,
    'scatter': chart_scatter,
    'heatmap': chart_heatmap,
    'radar': chart_radar,
    'funnel': chart_funnel,
    'gauge': chart_gauge,
    'treemap': chart_treemap,
    'candlestick': chart_candlestick,
    'combo': chart_combo,
}


def render_chart(chart_type: str, data: Dict, output: str,
                  theme: str = 'default') -> str:
    """
    统一图表渲染入口。

    Args:
        chart_type: 图表类型（bar/line/pie/waterfall/radar/...）
        data: 图表数据字典
        output: 输出文件路径（.png/.svg/.pdf）
        theme: 主题名

    Returns:
        输出文件路径
    """
    if chart_type not in CHART_TYPES:
        available = ', '.join(CHART_TYPES.keys())
        raise ValueError(f"Unknown chart type '{chart_type}'. Available: {available}")

    os.makedirs(os.path.dirname(output) or '.', exist_ok=True)
    return CHART_TYPES[chart_type](data, output, theme)


if __name__ == '__main__':
    import click

    @click.command()
    @click.option('--type', 'chart_type', required=True,
                   type=click.Choice(list(CHART_TYPES.keys())))
    @click.option('--data', required=True, help='JSON data file')
    @click.option('--output', required=True, help='Output image path')
    @click.option('--theme', default='default')
    def main(chart_type, data, output, theme):
        with open(data) as f:
            d = json.load(f)
        render_chart(chart_type, d, output, theme)
        click.echo(f"✅ {chart_type}: {output}")

    main()
