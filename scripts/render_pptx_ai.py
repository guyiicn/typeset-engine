#!/usr/bin/env python3
"""
AI PPT 渲染引擎 — 基于 Gemini 图片生成 + FFmpeg 视频合成。

将 NanoBanana PPT Skills 整合为 typeset-engine 的 pptx-ai 命令。
生成 AI 风格精美幻灯片图片 + HTML5 播放器 + MP4 视频。

风格:
  gradient-glass       — 渐变拟物玻璃卡片风格（科技感）
  vector-illustration  — 矢量插画风格（温暖教育风）
  自定义               — styles/ 目录下的 .md 文件

用法:
  python engine.py pptx-ai --data slides_plan.json --style gradient-glass --output ./output/
  python engine.py pptx-ai --data slides_plan.json --style vector-illustration --resolution 4K

环境变量:
  GEMINI_API_KEY       — Google Gemini API key（必需）
  KLING_ACCESS_KEY     — Kling AI key（可选，用于 AI 转场视频）
  KLING_SECRET_KEY     — Kling AI secret（可选）

slides_plan.json 格式:
{
  "title": "演示标题",
  "slides": [
    {"type": "cover", "content": "标题文本"},
    {"type": "content", "content": "要点内容..."},
    {"type": "data", "content": "数据和结论..."}
  ]
}
"""

import json
import os
import sys
import shutil
import base64
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime


# ═══════════════════════════════════════════
# 常量
# ═══════════════════════════════════════════

STYLES_DIR = Path(__file__).parent.parent / 'styles'
TEMPLATES_DIR = Path(__file__).parent.parent / 'templates' / 'html'

RESOLUTIONS = {
    '2K': (2752, 1536),
    '4K': (5504, 3072),
}

PAGE_TYPES = ('cover', 'content', 'data')


# ═══════════════════════════════════════════
# 风格模板
# ═══════════════════════════════════════════

def list_styles() -> List[Dict[str, str]]:
    """列出所有可用风格"""
    styles = []
    if STYLES_DIR.exists():
        for md_file in sorted(STYLES_DIR.glob('*.md')):
            name = md_file.stem
            # 读取第一行作为描述
            with open(md_file, 'r', encoding='utf-8') as f:
                first_line = f.readline().strip().lstrip('# ')
            styles.append({'id': name, 'name': first_line, 'path': str(md_file)})
    return styles


def load_style(style_name: str) -> str:
    """加载风格模板，返回基础提示词"""
    style_path = STYLES_DIR / f'{style_name}.md'
    if not style_path.exists():
        available = [s['id'] for s in list_styles()]
        raise FileNotFoundError(
            f"Style '{style_name}' not found. Available: {', '.join(available)}"
        )

    with open(style_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 提取 "## 基础提示词模板" 到下一个 "## " 之间的内容
    marker = '## 基础提示词模板'
    start = content.find(marker)
    if start == -1:
        # fallback: 取 "## " 之后的全部内容
        return content

    start += len(marker)
    end = content.find('\n## ', start)
    if end == -1:
        return content[start:].strip()
    return content[start:end].strip()


# ═══════════════════════════════════════════
# Prompt 构建
# ═══════════════════════════════════════════

def build_prompt(style_template: str, page_type: str, content: str,
                 slide_num: int, total: int) -> str:
    """为单张幻灯片构建完整 prompt"""
    parts = [style_template, '\n\n']

    is_cover = page_type == 'cover' or slide_num == 1
    is_data = page_type == 'data' or slide_num == total

    if is_cover:
        parts.append(
            f'请根据视觉平衡美学，生成封面页。'
            f'在中心放置一个巨大的复杂3D玻璃物体，并覆盖粗体大字：\n\n'
            f'{content}\n\n背景有延伸的极光波浪。'
        )
    elif is_data:
        parts.append(
            f'请生成数据页或总结页。使用分屏设计，'
            f'左侧排版以下文字，右侧悬浮巨大的发光3D数据可视化图表：\n\n'
            f'{content}'
        )
    else:
        parts.append(
            f'请生成内容页。使用Bento网格布局，'
            f'将以下内容组织在模块化的圆角矩形容器中，'
            f'容器材质必须是带有模糊效果的磨砂玻璃：\n\n'
            f'{content}'
        )

    return ''.join(parts)


# ═══════════════════════════════════════════
# Gemini 图片生成
# ═══════════════════════════════════════════

def get_gemini_client():
    """获取 Gemini API 客户端"""
    try:
        from google import genai
    except ImportError:
        raise ImportError(
            "google-genai not installed. Run: pip install google-genai"
        )

    api_key = os.environ.get('GEMINI_API_KEY')
    if not api_key:
        raise ValueError(
            "GEMINI_API_KEY not set. Export it or pass via --gemini-key"
        )

    return genai.Client(api_key=api_key)


def generate_slide_image(client, prompt: str, slide_num: int,
                         output_dir: str, resolution: str = '2K') -> Optional[str]:
    """用 Gemini generate_content 生成单张幻灯片图片"""
    from google.genai import types

    # 强制 16:9 比例提示
    full_prompt = f'{prompt}\n\nIMPORTANT: Output a single 16:9 widescreen image, no text explanation needed.'

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
                    filename = f'slide_{slide_num:03d}.png'
                    filepath = os.path.join(output_dir, filename)
                    with open(filepath, 'wb') as f:
                        f.write(part.inline_data.data)
                    size = os.path.getsize(filepath)
                    print(f"  OK  slide_{slide_num:03d}.png ({size:,} bytes)")
                    return filepath

        print(f"  WARNING: No image in response for slide {slide_num}")
        return None

    except Exception as e:
        print(f"  FAIL slide {slide_num}: {e}")
        return None


# ═══════════════════════════════════════════
# HTML 播放器
# ═══════════════════════════════════════════

def generate_html_viewer(image_paths: List[str], output_path: str,
                         title: str = 'PPT Viewer') -> str:
    """生成自包含的 HTML5 播放器（图片 base64 内嵌）"""
    template_path = TEMPLATES_DIR / 'viewer.html'

    if template_path.exists():
        with open(template_path, 'r', encoding='utf-8') as f:
            html_template = f.read()
    else:
        # 内置精简模板
        html_template = _minimal_viewer_template()

    # 图片转 base64
    slides_data = []
    for img_path in image_paths:
        with open(img_path, 'rb') as f:
            b64 = base64.b64encode(f.read()).decode('utf-8')
        slides_data.append(f'data:image/png;base64,{b64}')

    # 注入图片数据（替换模板中的占位符，或直接生成完整页面）
    slides_js = json.dumps(slides_data)
    final_html = _build_viewer_html(slides_js, title, len(image_paths))

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(final_html)

    print(f"  HTML viewer: {output_path} ({os.path.getsize(output_path):,} bytes)")
    return output_path


def _build_viewer_html(slides_js: str, title: str, count: int) -> str:
    """构建完整的 HTML 播放器"""
    return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ overflow: hidden; background: #000; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }}
.container {{ width: 100vw; height: 100vh; display: flex; justify-content: center; align-items: center; position: relative; }}
.slide {{ width: 100%; height: 100%; object-fit: contain; display: none; }}
.slide.active {{ display: block; }}
.controls {{
  position: fixed; bottom: 20px; left: 50%; transform: translateX(-50%);
  background: rgba(0,0,0,0.7); backdrop-filter: blur(10px);
  padding: 12px 24px; border-radius: 25px; color: white; font-size: 14px;
  display: flex; align-items: center; gap: 16px; z-index: 100;
  opacity: 0; transition: opacity 0.3s;
}}
.controls:hover, body:hover .controls {{ opacity: 1; }}
.btn {{
  background: rgba(255,255,255,0.15); border: none; color: white;
  width: 36px; height: 36px; border-radius: 50%; cursor: pointer;
  display: flex; align-items: center; justify-content: center; font-size: 16px;
  transition: background 0.2s;
}}
.btn:hover {{ background: rgba(255,255,255,0.3); }}
.progress {{ flex: 1; min-width: 120px; height: 4px; background: rgba(255,255,255,0.2); border-radius: 2px; cursor: pointer; }}
.progress-bar {{ height: 100%; background: #4ecdc4; border-radius: 2px; transition: width 0.3s; }}
.counter {{ white-space: nowrap; }}
</style>
</head>
<body>
<div class="container" id="slideContainer"></div>
<div class="controls">
  <button class="btn" onclick="prevSlide()">&#9664;</button>
  <div class="progress" onclick="clickProgress(event)">
    <div class="progress-bar" id="progressBar"></div>
  </div>
  <button class="btn" onclick="nextSlide()">&#9654;</button>
  <span class="counter" id="counter">1 / {count}</span>
  <button class="btn" onclick="toggleFullscreen()">&#9974;</button>
</div>
<script>
const slides = {slides_js};
let current = 0;
const container = document.getElementById("slideContainer");

slides.forEach((src, i) => {{
  const img = document.createElement("img");
  img.src = src; img.className = "slide" + (i === 0 ? " active" : "");
  container.appendChild(img);
}});

function showSlide(n) {{
  const els = document.querySelectorAll(".slide");
  els[current].classList.remove("active");
  current = ((n % slides.length) + slides.length) % slides.length;
  els[current].classList.add("active");
  document.getElementById("counter").textContent = (current+1) + " / " + slides.length;
  document.getElementById("progressBar").style.width = ((current+1)/slides.length*100) + "%";
}}
function nextSlide() {{ showSlide(current + 1); }}
function prevSlide() {{ showSlide(current - 1); }}
function clickProgress(e) {{ const r = e.target.getBoundingClientRect(); showSlide(Math.floor(((e.clientX-r.left)/r.width)*slides.length)); }}
function toggleFullscreen() {{ document.fullscreenElement ? document.exitFullscreen() : document.documentElement.requestFullscreen(); }}

document.addEventListener("keydown", e => {{
  if (e.key === "ArrowRight" || e.key === " ") nextSlide();
  else if (e.key === "ArrowLeft") prevSlide();
  else if (e.key === "Home") showSlide(0);
  else if (e.key === "End") showSlide(slides.length - 1);
  else if (e.key === "f" || e.key === "F") toggleFullscreen();
  else if (e.key === "Escape" && document.fullscreenElement) document.exitFullscreen();
}});
</script>
</body>
</html>'''


def _minimal_viewer_template() -> str:
    return ''


# ═══════════════════════════════════════════
# FFmpeg 视频合成
# ═══════════════════════════════════════════

def generate_video(image_paths: List[str], output_path: str,
                   duration: float = 3.0, transition: str = 'fade',
                   transition_duration: float = 0.5) -> Optional[str]:
    """将幻灯片图片合成为 MP4 视频（FFmpeg，不依赖外部 AI）"""
    if not shutil.which('ffmpeg'):
        print("  WARNING: ffmpeg not found, skipping video generation")
        return None

    import subprocess
    import tempfile

    with tempfile.TemporaryDirectory(prefix='typeset_video_') as tmp:
        # 1. 每张图片转为固定时长的视频片段
        clips = []
        for i, img in enumerate(image_paths):
            clip_path = os.path.join(tmp, f'clip_{i:03d}.mp4')
            cmd = [
                'ffmpeg', '-y', '-loop', '1', '-i', img,
                '-c:v', 'libx264', '-t', str(duration),
                '-pix_fmt', 'yuv420p', '-vf', 'scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2',
                '-r', '24', clip_path,
            ]
            result = subprocess.run(cmd, capture_output=True, timeout=60)
            if result.returncode == 0:
                clips.append(clip_path)

        if not clips:
            print("  WARNING: No video clips generated")
            return None

        # 2. 如果有转场，用 xfade 拼接；否则直接 concat
        if transition != 'none' and len(clips) > 1:
            # 用 xfade 逐步拼接
            current = clips[0]
            for i in range(1, len(clips)):
                merged = os.path.join(tmp, f'merged_{i:03d}.mp4')
                offset = duration - transition_duration
                cmd = [
                    'ffmpeg', '-y', '-i', current, '-i', clips[i],
                    '-filter_complex',
                    f'xfade=transition={transition}:duration={transition_duration}:offset={offset}',
                    '-c:v', 'libx264', '-pix_fmt', 'yuv420p', merged,
                ]
                result = subprocess.run(cmd, capture_output=True, timeout=120)
                if result.returncode == 0:
                    current = merged
                else:
                    # fallback: 直接 concat
                    current = clips[i]

            shutil.copy2(current, output_path)
        else:
            # 简单拼接
            list_file = os.path.join(tmp, 'filelist.txt')
            with open(list_file, 'w') as f:
                for c in clips:
                    f.write(f"file '{c}'\n")
            cmd = [
                'ffmpeg', '-y', '-f', 'concat', '-safe', '0',
                '-i', list_file, '-c', 'copy', output_path,
            ]
            subprocess.run(cmd, capture_output=True, timeout=120)

    if os.path.exists(output_path):
        print(f"  Video: {output_path} ({os.path.getsize(output_path):,} bytes)")
        return output_path
    return None


# ═══════════════════════════════════════════
# 主入口
# ═══════════════════════════════════════════

def render_pptx_ai(data: Dict, output_dir: str, style: str = 'gradient-glass',
                   resolution: str = '2K', video: bool = True,
                   slide_duration: float = 3.0,
                   transition: str = 'fade') -> Dict[str, Any]:
    """
    AI PPT 渲染主入口。

    Args:
        data: slides_plan 字典，格式见模块文档
        output_dir: 输出目录
        style: 风格名（gradient-glass / vector-illustration / 自定义）
        resolution: 图片分辨率 (2K / 4K)
        video: 是否生成 MP4 视频
        slide_duration: 每页停留秒数
        transition: 转场效果 (fade/dissolve/wipeleft/slideright/none)

    Returns:
        {'images': [...], 'html': '...', 'video': '...', 'prompts': [...]}
    """
    os.makedirs(output_dir, exist_ok=True)
    images_dir = os.path.join(output_dir, 'slides')
    os.makedirs(images_dir, exist_ok=True)

    # 1. 加载风格
    style_template = load_style(style)
    print(f"  Style: {style}")
    print(f"  Resolution: {resolution}")

    # 2. 构建 prompts
    slides = data.get('slides', [])
    title = data.get('title', 'Presentation')
    total = len(slides)
    prompts = []

    for i, slide in enumerate(slides):
        page_type = slide.get('type', 'content')
        content = slide.get('content', '')
        prompt = build_prompt(style_template, page_type, content, i + 1, total)
        prompts.append({
            'slide': i + 1,
            'type': page_type,
            'prompt': prompt,
        })

    # 保存 prompts
    prompts_path = os.path.join(output_dir, 'prompts.json')
    with open(prompts_path, 'w', encoding='utf-8') as f:
        json.dump(prompts, f, ensure_ascii=False, indent=2)
    print(f"  Prompts saved: {prompts_path}")

    # 3. 生成图片
    client = get_gemini_client()
    image_paths = []

    for p in prompts:
        path = generate_slide_image(
            client, p['prompt'], p['slide'], images_dir, resolution
        )
        if path:
            image_paths.append(path)

    print(f"  Images generated: {len(image_paths)} / {total}")

    result = {
        'images': image_paths,
        'prompts': prompts,
        'html': None,
        'video': None,
    }

    if not image_paths:
        return result

    # 4. HTML 播放器
    html_path = os.path.join(output_dir, 'index.html')
    generate_html_viewer(image_paths, html_path, title)
    result['html'] = html_path

    # 5. 视频
    if video:
        video_path = os.path.join(output_dir, 'presentation.mp4')
        generate_video(image_paths, video_path, slide_duration, transition)
        result['video'] = video_path

    return result


if __name__ == '__main__':
    import click

    @click.command()
    @click.option('--data', required=True, help='Input slides_plan JSON file')
    @click.option('--output', required=True, help='Output directory')
    @click.option('--style', default='gradient-glass',
                  help='Style name (gradient-glass / vector-illustration / custom)')
    @click.option('--resolution', default='2K', type=click.Choice(['2K', '4K']))
    @click.option('--video/--no-video', default=True, help='Generate MP4 video')
    @click.option('--duration', default=3.0, help='Seconds per slide in video')
    @click.option('--transition', default='fade',
                  help='Video transition (fade/dissolve/wipeleft/slideright/none)')
    @click.option('--list-styles', is_flag=True, help='List available styles')
    def main(data, output, style, resolution, video, duration, transition, list_styles):
        if list_styles:
            for s in list_styles():
                click.echo(f"  {s['id']:25s} — {s['name']}")
            return

        with open(data) as f:
            d = json.load(f)
        result = render_pptx_ai(d, output, style, resolution, video, duration, transition)
        click.echo(f"\nDone! {len(result['images'])} slides generated.")
        if result['html']:
            click.echo(f"  HTML: {result['html']}")
        if result['video']:
            click.echo(f"  Video: {result['video']}")

    main()
