# typeset-engine 使用指南

统一文档渲染引擎 Docker 容器。输入 JSON 数据，输出 PDF / PPTX / DOCX / 图表 / AI幻灯片 / 视频。

## 快速开始

```bash
# 镜像名
docker run typeset-engine:v1 python scripts/engine.py --help

# 查看所有命令
docker run typeset-engine:v1 python scripts/engine.py --help
```

输出：
```
Commands:
  pptx        结构化 PPTX 演示文稿（可编辑）
  pptx-ai     AI 风格 PPT（Gemini 图片 + HTML 播放器 + MP4 视频）
  pdf          Typst 排版 PDF（投研报告级）
  docx         Word 文档
  chart        13 种商业图表
  illustrate   AI 配图（给任意文本生成精美插图）
  styles       列出可用 AI 风格
  fonts        列出容器内可用字体
  diff         文件版本对比
```

---

## 命令详解

### 1. PDF — 投研报告

```bash
docker run --rm -v $(pwd)/output:/app/output typeset-engine:v1 \
  python scripts/engine.py pdf \
  --data /app/output/report.json \
  --output /app/output/report.pdf \
  --theme cicc
```

**主题**: `cicc`(中金) / `ms`(摩根斯坦利) / `cms`(招商) / `dachen`(达晨)

**引擎**: Typst 排版，自动目录，封面页，页眉页脚，中文字体

### 2. PPTX — 结构化演示文稿

```bash
docker run --rm -v $(pwd)/output:/app/output typeset-engine:v1 \
  python scripts/engine.py pptx \
  --data /app/output/slides.json \
  --output /app/output/report.pptx \
  --template default
```

**能力**: 12 种布局 x 6 种主题 = 72 种幻灯片变体，输出可编辑 .pptx 文件

### 3. DOCX — Word 文档

```bash
docker run --rm -v $(pwd)/output:/app/output typeset-engine:v1 \
  python scripts/engine.py docx \
  --data /app/output/report.json \
  --output /app/output/report.docx \
  --theme cicc
```

**主题**: 与 PDF 相同（cicc / ms / cms / dachen）

**能力**: 封面、目录、表格、图表嵌入、引用框、KPI 卡片、免责声明、页眉页脚页码

### 4. AI PPT — Gemini 生成精美幻灯片

```bash
docker run --rm \
  -e GEMINI_API_KEY=你的key \
  -v $(pwd)/output:/app/output \
  typeset-engine:v1 \
  python scripts/engine.py pptx-ai \
  --data /app/output/slides_plan.json \
  --output /app/output/ai_ppt/ \
  --style gradient-glass \
  --resolution 2K \
  --video \
  --duration 3.0 \
  --transition fade
```

**风格**:
- `gradient-glass` — 渐变拟物玻璃卡片风格（科技感，Apple Keynote 级）
- `vector-illustration` — 矢量插画风格（温暖教育风）
- 自定义风格：在 `styles/` 目录放 `.md` 文件，用文件名引用

**输出**:
- `slides/slide_001.png` ... — 高清幻灯片图片
- `index.html` — 自包含 HTML5 播放器（键盘导航、全屏、自动播放）
- `presentation.mp4` — 带转场效果的视频
- `prompts.json` — 生成用的 prompt 记录

**转场效果**: `fade` / `dissolve` / `wipeleft` / `slideright` / `none`

**环境变量**: `GEMINI_API_KEY`（必需）

### 5. 图表 — 13 种商业图表

```bash
docker run --rm -v $(pwd)/output:/app/output typeset-engine:v1 \
  python scripts/engine.py chart \
  --type bar \
  --data /app/output/chart_data.json \
  --output /app/output/chart.png \
  --theme cicc
```

**图表类型**: `bar` / `line` / `area` / `pie` / `waterfall` / `scatter` / `heatmap` / `radar` / `funnel` / `gauge` / `treemap` / `candlestick` / `combo`

**主题**: `default` / `cicc` / `goldman` / `dark`

### 6. AI 配图 — 给任意文本生成插图

```bash
docker run --rm \
  -e GEMINI_API_KEY=你的key \
  -v $(pwd)/output:/app/output \
  typeset-engine:v1 \
  python scripts/engine.py illustrate \
  --content "AI Agent 多智能体协作架构解析" \
  --style ticket \
  --title "Multi-Agent Architecture" \
  --output /app/output/illustration.png
```

**风格**:
- `gradient-glass` — 科技玻璃风（深色背景，3D 物体，霓虹渐变）
- `vector-illustration` — 矢量插画风（扁平，复古配色，几何简化）
- `ticket` — 数字票券风（黑白对比，网格排版，极简信息图）

**参数**:
- `--content` — 要配图的文本内容（必需）
- `--style` — 风格名
- `--title` — 可选标题（会显示在图中）
- `--ratio` — 宽高比：16:9 / 3:4 / 1:1
- `--cover` — 生成封面图模式

**环境变量**: `GEMINI_API_KEY`（必需）

### 7. 列出 AI 风格

```bash
docker run --rm typeset-engine:v1 python scripts/engine.py styles
```

### 7. 列出字体

```bash
docker run --rm typeset-engine:v1 python scripts/engine.py fonts --lang zh
```

### 8. 文件对比

```bash
docker run --rm -v $(pwd)/output:/app/output typeset-engine:v1 \
  python scripts/engine.py diff \
  --old /app/output/v1.pdf \
  --new /app/output/v2.pdf \
  --output /app/output/diff_report.png \
  --mode visual
```

---

## JSON 数据格式

PDF / DOCX / PPTX 共用同一套 JSON 格式，同一份数据可以同时出三种文档。

```json
{
  "title": "报告标题",
  "title_en": "English Title",
  "author": "DeerFlow Research",
  "date": "2026-04-07",
  "version": "v1.0",
  "toc": true,

  "charts": [
    {
      "id": "revenue_bar",
      "type": "bar",
      "data": {
        "title": "营收对比",
        "categories": ["2022", "2023", "2024"],
        "series": [
          {"name": "营收", "values": [100, 120, 150]},
          {"name": "利润", "values": [30, 40, 55]}
        ]
      }
    }
  ],

  "sections": [
    {
      "type": "heading",
      "title": "章节标题",
      "content": "正文内容（首段）",
      "children": [
        {"type": "quote", "content": "核心观点引用"},
        {"type": "kpi", "metrics": [
          {"label": "目标价", "value": "¥2,200", "change": "+15%"},
          {"label": "PE", "value": "28.5x"},
          {"label": "评级", "value": "买入", "change": "维持"}
        ]},
        {"type": "heading", "title": "子标题", "content": "子章节内容"},
        {"type": "chart", "chart_id": "revenue_bar", "caption": "图1：营收趋势"},
        {"type": "table", "headers": ["指标", "2023", "2024"],
         "rows": [["营收", "120", "150"], ["ROE", "33%", "35%"]]},
        {"type": "ai-image", "image_id": "ai_arch_img", "caption": "图2：多智能体架构"},
        {"type": "paragraph", "content": "更多正文段落..."},
        {"type": "pagebreak"}
      ]
    }
  ],

  "illustrations": [
    {
      "id": "ai_arch_img",
      "content": "多智能体协作架构，包括路由、执行、反馈三个核心模块",
      "style": "ticket",
      "title": "Multi-Agent Architecture"
    }
  ],

  "disclaimer": "免责声明文本..."
}
```

### section type 说明

| type | 作用 | 关键字段 |
|------|------|---------|
| `heading` | 标题（支持多级嵌套 H1→H2→H3） | `title`, `content`, `children` |
| `paragraph` | 正文段落 | `content` |
| `quote` | 引用框（彩色左边框 + 背景） | `content` |
| `table` | 数据表格 | `headers`, `rows` |
| `chart` | 嵌入图表（引用 charts 中的 id） | `chart_id`, `caption` |
| `kpi` | KPI 指标卡片（多列布局） | `metrics[{label, value, change}]` |
| `ai-image` | AI 配图（Gemini 生成，需 API key） | `image_id`, `caption` |
| `pagebreak` | 分页符 | — |

---

## AI PPT 数据格式

`pptx-ai` 命令使用单独的 slides_plan 格式：

```json
{
  "title": "演示标题",
  "slides": [
    {"type": "cover", "content": "封面标题文本"},
    {"type": "content", "content": "要点内容..."},
    {"type": "data", "content": "数据和结论..."}
  ]
}
```

**页面类型**: `cover`(封面) / `content`(内容) / `data`(数据/总结)

---

## 容器内技术栈

| 组件 | 版本 | 用途 |
|------|------|------|
| Typst | 0.14.0 | PDF 排版引擎 |
| Plotly + Kaleido | latest | 图表渲染 |
| Chrome (headless) | latest | Kaleido 图表导出 |
| python-pptx | 1.0.2 | PPTX 生成 |
| python-docx | 1.2.0 | DOCX 生成 |
| google-genai | latest | Gemini AI 图片生成 |
| FFmpeg | system | 视频合成 |
| Noto Sans/Serif CJK | latest | 中文字体 |

## 文件结构

```
/app/
├── scripts/
│   ├── engine.py           # CLI 主入口
│   ├── render_pdf.py       # PDF 渲染（Typst）
│   ├── render_pptx.py      # PPTX 渲染（python-pptx）
│   ├── render_docx.py      # DOCX 渲染（python-docx）
│   ├── render_charts.py    # 图表渲染（Plotly）
│   ├── render_pptx_ai.py   # AI PPT（Gemini + FFmpeg）
│   └── file_diff.py        # 文件对比
├── styles/
│   ├── gradient-glass.md          # AI风格：科技玻璃
│   └── vector-illustration.md     # AI风格：矢量插画
├── templates/
│   ├── cicc-report.typ     # Typst PDF 模板
│   ├── themes.typ          # Typst 主题定义
│   └── html/
│       ├── viewer.html     # HTML5 幻灯片播放器
│       └── video_viewer.html
└── Dockerfile
```

## 构建镜像

```bash
cd /home/guyii/clawd/code/typeset-engine
docker build -t typeset-engine:v1 .
```
