#!/usr/bin/env python3
"""
技术架构图渲染器 — SVG → PNG (via rsvg-convert)

接收 SVG 字符串，用 rsvg-convert 导出高清 PNG。
配合 fireworks-tech-graph Skill 使用：Claude 生成 SVG，本模块负责渲染。

用法:
  # HTTP API
  curl -X POST http://localhost:9090/render/diagram \
    -H "Content-Type: application/json" \
    -d '{"svg": "<svg>...</svg>", "width": 1920}' \
    -o diagram.png

  # CLI
  docker exec typeset-engine python scripts/render_diagram.py \
    --input diagram.svg --output diagram.png --width 1920

支持:
  - SVG → PNG（默认 1920px，2x 视网膜）
  - SVG → SVG（原样保存/校验）
  - 自动语法校验（rsvg-convert dry-run）
"""

import os
import subprocess
import sys
import tempfile
from pathlib import Path


def validate_svg(svg_content: str) -> dict:
    """校验 SVG 语法是否能被 rsvg-convert 正确解析"""
    with tempfile.NamedTemporaryFile(suffix='.svg', mode='w', delete=False, encoding='utf-8') as f:
        f.write(svg_content)
        tmp_svg = f.name

    try:
        tmp_png = tmp_svg.rsplit('.', 1)[0] + '.png'
        result = subprocess.run(
            ['rsvg-convert', tmp_svg, '-o', tmp_png],
            capture_output=True, text=True, timeout=10
        )
        if os.path.exists(tmp_png):
            os.unlink(tmp_png)
        if result.returncode == 0:
            return {'valid': True, 'message': 'SVG syntax OK'}
        else:
            return {'valid': False, 'message': result.stderr.strip()}
    except FileNotFoundError:
        return {'valid': False, 'message': 'rsvg-convert not found. Install: apt install librsvg2-bin'}
    except subprocess.TimeoutExpired:
        return {'valid': False, 'message': 'SVG validation timed out (>10s)'}
    finally:
        os.unlink(tmp_svg)


def render_diagram(svg_content: str, output_path: str, width: int = 1920, fmt: str = 'png') -> str:
    """
    将 SVG 字符串渲染为 PNG 或保存为 SVG。

    Args:
        svg_content: SVG 字符串
        output_path: 输出文件路径
        width: PNG 输出宽度（默认 1920px，2x 视网膜分辨率）
        fmt: 输出格式 'png' | 'svg' | 'both'

    Returns:
        输出文件路径（fmt='both' 时返回 PNG 路径）

    Raises:
        ValueError: SVG 语法错误
        RuntimeError: rsvg-convert 执行失败
    """
    # 确保输出目录存在
    os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)

    # 确定输出路径
    base = output_path.rsplit('.', 1)[0] if '.' in os.path.basename(output_path) else output_path
    svg_path = base + '.svg'
    png_path = base + '.png'

    # 写 SVG 文件
    with open(svg_path, 'w', encoding='utf-8') as f:
        f.write(svg_content)

    if fmt == 'svg':
        return svg_path

    # SVG → PNG via rsvg-convert
    cmd = ['rsvg-convert', '-w', str(width), svg_path, '-o', png_path]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    except FileNotFoundError:
        raise RuntimeError('rsvg-convert not found. Install: apt install librsvg2-bin')
    except subprocess.TimeoutExpired:
        raise RuntimeError('rsvg-convert timed out (>30s), SVG may be too complex')

    if result.returncode != 0:
        error_msg = result.stderr.strip()
        raise ValueError(f'SVG render failed: {error_msg}')

    # fmt='both' 保留 SVG + PNG，返回 PNG 路径
    if fmt == 'png':
        # 只要 PNG，删除中间 SVG
        os.unlink(svg_path)

    return png_path


def main():
    """CLI 入口"""
    import argparse

    parser = argparse.ArgumentParser(description='Render SVG to PNG via rsvg-convert')
    parser.add_argument('--input', '-i', required=True, help='Input SVG file path')
    parser.add_argument('--output', '-o', required=True, help='Output file path')
    parser.add_argument('--width', '-w', type=int, default=1920, help='PNG width (default: 1920)')
    parser.add_argument('--format', '-f', choices=['png', 'svg', 'both'], default='png',
                        help='Output format (default: png)')
    parser.add_argument('--validate', action='store_true', help='Validate SVG only, no render')

    args = parser.parse_args()

    with open(args.input, 'r', encoding='utf-8') as f:
        svg_content = f.read()

    if args.validate:
        result = validate_svg(svg_content)
        print(f"{'OK' if result['valid'] else 'FAIL'}: {result['message']}")
        sys.exit(0 if result['valid'] else 1)

    out = render_diagram(svg_content, args.output, width=args.width, fmt=args.format)
    print(f'Output: {out}')


if __name__ == '__main__':
    main()
