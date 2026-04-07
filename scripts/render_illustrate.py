#!/usr/bin/env python3
"""
AI 配图引擎 — 给文档内容生成精美插图。

复用 Gemini API，支持 3 种风格 + 自定义风格。
可独立使用，也可被 PDF/DOCX 渲染器内部调用（ai-image section type）。

风格:
  gradient-glass       — 科技玻璃风（深色背景，3D 物体，霓虹渐变）
  vector-illustration  — 矢量插画风（扁平，复古配色，几何简化）
  ticket               — 数字票券风（黑白对比，网格排版，极简信息图）

用法:
  python engine.py illustrate --content "AI Agent 协作架构" --style ticket --output img.png
  python engine.py illustrate --content "量子计算原理" --style gradient-glass --ratio 3:4 --output img.png
"""

import json
import os
from pathlib import Path
from typing import Optional

# 复用已有的 Gemini 客户端和风格加载
from render_pptx_ai import get_gemini_client, load_style, STYLES_DIR


ASPECT_RATIOS = {
    '16:9': '16:9',
    '3:4': '3:4',
    '1:1': '1:1',
}


def generate_illustration(content: str, output: str,
                          style: str = 'gradient-glass',
                          title: str = '',
                          ratio: str = '16:9',
                          cover: bool = False) -> Optional[str]:
    """
    生成单张 AI 配图。

    Args:
        content: 要配图的文本内容
        output: 输出图片路径（.png）
        style: 风格名
        title: 可选标题（加粗显示在图中）
        ratio: 宽高比 (16:9 / 3:4 / 1:1)
        cover: 是否为封面图（影响构图）

    Returns:
        输出路径，失败返回 None
    """
    os.makedirs(os.path.dirname(output) or '.', exist_ok=True)

    # 加载风格
    style_template = load_style(style)

    # 构建 prompt
    parts = [style_template, '\n\n']

    if cover and title:
        parts.append(
            f'请生成一张封面配图。主题是：{title}\n'
            f'用大字突出标题，配以与内容相关的视觉元素。\n\n'
            f'内容概要：{content}'
        )
    elif title:
        parts.append(
            f'请根据以下内容生成一张精美配图。\n'
            f'标题：{title}\n\n'
            f'内容：{content}'
        )
    else:
        parts.append(
            f'请根据以下内容生成一张精美配图：\n\n{content}'
        )

    full_prompt = ''.join(parts)

    # 调 Gemini
    from google.genai import types

    client = get_gemini_client()

    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash-image',
            contents=full_prompt,
            config=types.GenerateContentConfig(
                response_modalities=['IMAGE'],
            ),
        )

        if response and response.candidates:
            for part in response.candidates[0].content.parts:
                if part.inline_data and part.inline_data.data:
                    with open(output, 'wb') as f:
                        f.write(part.inline_data.data)
                    size = os.path.getsize(output)
                    print(f"  OK  {output} ({size:,} bytes)")
                    return output

        print(f"  WARNING: No image returned for '{title or content[:30]}'")
        return None

    except Exception as e:
        print(f"  FAIL: {e}")
        return None


if __name__ == '__main__':
    import click

    @click.command()
    @click.option('--content', required=True, help='Text content to illustrate')
    @click.option('--output', required=True, help='Output image path (.png)')
    @click.option('--style', default='gradient-glass',
                  help='Style: gradient-glass / vector-illustration / ticket')
    @click.option('--title', default='', help='Optional title overlay')
    @click.option('--ratio', default='16:9', help='Aspect ratio: 16:9 / 3:4 / 1:1')
    @click.option('--cover', is_flag=True, help='Generate as cover image')
    def main(content, output, style, title, ratio, cover):
        result = generate_illustration(content, output, style, title, ratio, cover)
        if result:
            click.echo(f"OK: {result}")
        else:
            click.echo("FAILED", err=True)

    main()
