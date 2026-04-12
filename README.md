# typeset-engine

统一文档渲染引擎。输入 JSON，输出 PDF / DOCX / PPTX / 图表 / AI幻灯片 / AI配图 / 视频。

Docker 容器化，提供 HTTP API（端口 9090）和 CLI 两种调用方式。

---

## 启动服务

```bash
# HTTP API 模式（推荐）
docker run -d --name typeset-engine \
  -p 9090:9090 \
  -e GEMINI_API_KEY=你的key \
  -v /data/output:/app/output \
  typeset-engine:v1

# 验证
curl http://localhost:9090/health
# {"status": "ok", "engine": "typeset-engine", "version": "1.0"}
```

> GEMINI_API_KEY 仅 pptx-ai / illustrate 命令需要，其他命令可不传。

---

## 能力总览

| 命令 | HTTP 端点 | 输入 | 输出 | 需要 API Key |
|------|----------|------|------|:---:|
| **pdf** | `POST /render/pdf` | 报告 JSON | PDF 文件 | 否 |
| **docx** | `POST /render/docx` | 报告 JSON | DOCX 文件 | 否 |
| **pptx** | `POST /render/pptx` | 幻灯片 JSON | PPTX 文件 | 否 |
| **chart** | `POST /render/chart` | 图表 JSON | PNG 图片 | 否 |
| **pptx-ai** | `POST /render/pptx-ai` | slides_plan JSON | ZIP（图片+HTML+MP4） | 是 |
| **diagram** | `POST /render/diagram` | SVG 字符串 | PNG 图片 | 否 |
| **illustrate** | `POST /render/illustrate` | 文本+风格 | PNG 图片 | 是 |
| **styles** | `GET /styles` | — | 风格列表 JSON | 否 |
| **capabilities** | `GET /capabilities` | — | 全部命令描述 JSON | 否 |
| **health** | `GET /health` | — | 状态 JSON | 否 |

---

## HTTP API 调用（curl）

### 生成 PDF

```bash
curl -X POST http://localhost:9090/render/pdf \
  -H "Content-Type: application/json" \
  -d @report.json \
  -o report.pdf
```

### 生成 DOCX

```bash
curl -X POST http://localhost:9090/render/docx \
  -H "Content-Type: application/json" \
  -d @report.json \
  -o report.docx
```

### 生成图表

```bash
curl -X POST http://localhost:9090/render/chart \
  -H "Content-Type: application/json" \
  -d '{"type":"bar","theme":"cicc","data":{"title":"营收","categories":["Q1","Q2","Q3"],"series":[{"name":"收入","values":[100,120,150]}]}}' \
  -o chart.png
```

### 渲染技术架构图（SVG → PNG）

```bash
# 基本用法：SVG 字符串 → 1920px PNG
curl -X POST http://localhost:9090/render/diagram \
  -H "Content-Type: application/json" \
  -d '{"svg": "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 960 600\"><rect width=\"960\" height=\"600\" fill=\"#fff\"/><text x=\"480\" y=\"300\" text-anchor=\"middle\" font-size=\"24\">Hello Diagram</text></svg>", "width": 1920}' \
  -o diagram.png

# 仅校验 SVG 语法
curl -X POST http://localhost:9090/render/diagram \
  -H "Content-Type: application/json" \
  -d '{"svg": "<svg>...</svg>", "validate": true}'

# 同时输出 SVG + PNG
curl -X POST http://localhost:9090/render/diagram \
  -H "Content-Type: application/json" \
  -d '{"svg": "...", "format": "both"}' \
  -o diagram.png
```

参数：`svg`（必填）、`width`（默认 1920）、`format`（png/svg/both）、`validate`（true=仅校验）

### 生成 AI 配图

```bash
curl -X POST http://localhost:9090/render/illustrate \
  -H "Content-Type: application/json" \
  -d '{"content":"多智能体协作架构","style":"ticket","title":"Multi-Agent"}' \
  -o illustration.png
```

### 生成 AI PPT

```bash
curl -X POST http://localhost:9090/render/pptx-ai \
  -H "Content-Type: application/json" \
  -d '{"title":"AI趋势","style":"gradient-glass","slides":[{"type":"cover","content":"AI 2026"},{"type":"content","content":"要点内容"}]}' \
  -o ppt.zip
```

---

## CLI 调用（docker exec）

如果容器已启动，也可以用 docker exec 直接调用 CLI：

```bash
# PDF
docker exec typeset-engine python scripts/engine.py pdf \
  --data /app/output/report.json --output /app/output/report.pdf --theme cicc

# DOCX
docker exec typeset-engine python scripts/engine.py docx \
  --data /app/output/report.json --output /app/output/report.docx --theme cicc

# 图表
docker exec typeset-engine python scripts/engine.py chart \
  --type bar --data /app/output/chart.json --output /app/output/chart.png --theme cicc

# AI 配图
docker exec typeset-engine python scripts/engine.py illustrate \
  --content "量子计算原理" --style gradient-glass --output /app/output/img.png

# AI PPT
docker exec typeset-engine python scripts/engine.py pptx-ai \
  --data /app/output/plan.json --style gradient-glass --output /app/output/ai_ppt/

# 列出风格
docker exec typeset-engine python scripts/engine.py styles
```

---

## JSON 数据格式

PDF、DOCX、PPTX 共用同一套 JSON 格式。同一份数据可以同时出三种文档。

### 完整示例

```json
{
  "title": "贵州茅台深度研究报告",
  "title_en": "Kweichow Moutai Research",
  "author": "DeerFlow Research",
  "date": "2026-04-07",
  "version": "v1.0",
  "theme": "cicc",
  "toc": true,

  "charts": [
    {
      "id": "revenue_bar",
      "type": "bar",
      "data": {
        "title": "营收对比（亿元）",
        "categories": ["2022", "2023", "2024"],
        "series": [
          {"name": "营收", "values": [1276, 1505, 1738]},
          {"name": "净利润", "values": [627, 747, 862]}
        ]
      }
    }
  ],

  "illustrations": [
    {
      "id": "ai_cover",
      "content": "白酒行业竞争格局与茅台龙头地位",
      "style": "gradient-glass",
      "title": "Industry Landscape"
    }
  ],

  "sections": [
    {
      "type": "heading",
      "title": "核心观点",
      "children": [
        {"type": "quote", "content": "维持买入评级，目标价2200元。"},
        {"type": "kpi", "metrics": [
          {"label": "目标价", "value": "¥2,200", "change": "+15%"},
          {"label": "PE", "value": "28.5x"},
          {"label": "评级", "value": "买入", "change": "维持"}
        ]}
      ]
    },
    {
      "type": "heading",
      "title": "财务分析",
      "content": "茅台近三年营收保持双位数增长。",
      "children": [
        {"type": "chart", "chart_id": "revenue_bar", "caption": "图1：营收趋势"},
        {"type": "table",
         "headers": ["指标", "2022", "2023", "2024"],
         "rows": [
           ["营收(亿)", "1,276", "1,505", "1,738"],
           ["ROE", "31.2%", "33.5%", "34.1%"]
         ]},
        {"type": "ai-image", "image_id": "ai_cover", "caption": "图2：行业格局"}
      ]
    },
    {"type": "pagebreak"},
    {
      "type": "heading",
      "title": "风险提示",
      "content": "宏观经济下行风险；政策监管风险。"
    }
  ],

  "disclaimer": "本报告仅供参考，不构成投资建议。"
}
```

### 顶层字段

| 字段 | 类型 | 必需 | 说明 |
|------|------|:---:|------|
| `title` | string | 是 | 报告标题 |
| `title_en` | string | 否 | 英文副标题 |
| `author` | string | 否 | 作者/机构 |
| `date` | string | 否 | 日期 |
| `version` | string | 否 | 版本号 |
| `theme` | string | 否 | 主题：`cicc` / `ms` / `cms` / `dachen`，默认 `cicc` |
| `toc` | bool | 否 | 是否生成目录，默认 `true` |
| `charts` | array | 否 | 图表定义（见下方） |
| `illustrations` | array | 否 | AI 配图定义（需 GEMINI_API_KEY） |
| `sections` | array | 是 | 文档内容章节 |
| `disclaimer` | string | 否 | 免责声明 |

### section type 速查

| type | 用途 | 必需字段 | 示例 |
|------|------|---------|------|
| `heading` | 标题（H1→H2→H3 嵌套） | `title` | `{"type":"heading","title":"章节","content":"首段","children":[...]}` |
| `paragraph` | 正文段落 | `content` | `{"type":"paragraph","content":"段落文本"}` |
| `quote` | 引用框（彩色左边框） | `content` | `{"type":"quote","content":"核心观点"}` |
| `table` | 数据表格 | `headers`, `rows` | `{"type":"table","headers":["A","B"],"rows":[["1","2"]]}` |
| `chart` | 嵌入图表 | `chart_id` | `{"type":"chart","chart_id":"revenue_bar","caption":"图1"}` |
| `kpi` | KPI 指标卡片 | `metrics` | `{"type":"kpi","metrics":[{"label":"ROE","value":"35%","change":"+2%"}]}` |
| `ai-image` | AI 配图 | `image_id` | `{"type":"ai-image","image_id":"ai_cover","caption":"配图"}` |
| `pagebreak` | 分页符 | — | `{"type":"pagebreak"}` |

### charts 数组

```json
{
  "id": "唯一ID，sections 中用 chart_id 引用",
  "type": "bar",
  "data": {
    "title": "图表标题",
    "categories": ["X1", "X2"],
    "series": [{"name": "系列名", "values": [1, 2]}]
  }
}
```

**图表类型**: `bar` / `line` / `area` / `pie` / `waterfall` / `scatter` / `heatmap` / `radar` / `funnel` / `gauge` / `treemap` / `candlestick` / `combo`

### illustrations 数组

```json
{
  "id": "唯一ID，sections 中用 image_id 引用",
  "content": "要配图的文本描述",
  "style": "gradient-glass",
  "title": "可选标题"
}
```

**风格**: `gradient-glass`(科技玻璃) / `vector-illustration`(矢量插画) / `ticket`(极简票券)

### AI PPT 数据格式（pptx-ai 专用）

```json
{
  "title": "演示标题",
  "style": "gradient-glass",
  "slides": [
    {"type": "cover", "content": "封面标题"},
    {"type": "content", "content": "要点内容..."},
    {"type": "data", "content": "数据和结论..."}
  ]
}
```

**页面类型**: `cover`(封面) / `content`(内容) / `data`(数据/总结)

---

## 主题一览

### PDF / DOCX 主题

| 主题 | 视觉 | 适用场景 |
|------|------|---------|
| `cicc` | 深蓝底+红色装饰线，宋体正文 | 中金风格投研报告 |
| `ms` | 深蓝+亮蓝，无衬线字体 | 摩根斯坦利 Blue Paper |
| `cms` | 招商红+传统券商风 | 招商证券研报 |
| `dachen` | 达晨红+稳重国资风 | 创投/国资报告 |

### 图表主题

| 主题 | 配色 |
|------|------|
| `default` | 深蓝+金色 |
| `cicc` | 中金红+深灰 |
| `goldman` | 蓝绿+金色 |
| `dark` | 暗色底+霓虹色 |

### AI 风格（pptx-ai / illustrate）

| 风格 | 视觉 | 适用场景 |
|------|------|---------|
| `gradient-glass` | 3D 玻璃+霓虹渐变+深色背景 | 科技产品、商业演示 |
| `vector-illustration` | 扁平矢量+复古配色+几何简化 | 教育、创意方案 |
| `ticket` | 黑白对比+网格排版+票券美学 | 信息图、数据可视化 |

---

## 创建调用 typeset-engine 的 Claude Code Skill

以下是一个 SKILL.md 模板，其他 agent 可以用它注册成技能来调用 typeset-engine：

```markdown
---
name: my-report-generator
description: 使用 typeset-engine 生成投研报告 PDF/DOCX
---

# 报告生成技能

## 依赖

- typeset-engine Docker 容器已启动：`docker run -d --name typeset-engine -p 9090:9090 typeset-engine:v1`

## 工作流程

1. 分析用户需求，确定报告结构
2. 构造 JSON 数据（参考 typeset-engine JSON Schema）
3. 调用 HTTP API 生成文档
4. 返回文件给用户

## 生成 PDF

\```bash
# 1. 将 JSON 写入临时文件
cat > /tmp/report.json << 'ENDJSON'
{你构造的JSON}
ENDJSON

# 2. 调用 API
curl -s -X POST http://localhost:9090/render/pdf \
  -H "Content-Type: application/json" \
  -d @/tmp/report.json \
  -o /tmp/report.pdf

# 3. 检查结果
ls -la /tmp/report.pdf
\```

## 生成图表

\```bash
curl -s -X POST http://localhost:9090/render/chart \
  -H "Content-Type: application/json" \
  -d '{"type":"bar","theme":"cicc","data":{"title":"标题","categories":[...],"series":[...]}}' \
  -o /tmp/chart.png
\```

## 查看可用能力

\```bash
curl -s http://localhost:9090/capabilities | python3 -m json.tool
\```
```

---

## 技术栈

| 组件 | 用途 |
|------|------|
| Typst 0.14 | PDF 排版 |
| Plotly + Kaleido + Chrome | 图表渲染 |
| python-pptx | PPTX 生成 |
| python-docx | DOCX 生成 |
| Gemini API | AI 图片生成 |
| FFmpeg | 视频合成 |
| Noto CJK 字体 | 中文支持 |
| http.server | HTTP API |

## 文件结构

```
typeset-engine/
├── Dockerfile
├── README.md              ← 本文件（给 AI agent 的完整指南）
├── USAGE.md               ← CLI 详细用法
├── scripts/
│   ├── server.py          ← HTTP API 服务（端口 9090）
│   ├── engine.py          ← CLI 主入口
│   ├── render_pdf.py      ← PDF（Typst）
│   ├── render_pptx.py     ← PPTX（python-pptx）
│   ├── render_pptx_ai.py  ← AI PPT（Gemini + FFmpeg）
│   ├── render_docx.py     ← DOCX（python-docx）
│   ├── render_charts.py   ← 13 种图表（Plotly）
│   ├── render_illustrate.py ← AI 配图（Gemini）
│   ├── render_diagram.py  ← 技术架构图（SVG→PNG, rsvg-convert）
│   └── file_diff.py       ← 文件对比
├── styles/
│   ├── gradient-glass.md
│   ├── vector-illustration.md
│   └── ticket.md
└── templates/
    ├── cicc-report.typ
    ├── themes.typ
    └── html/
        ├── viewer.html
        └── video_viewer.html
```

## 构建镜像

```bash
cd /home/guyii/clawd/code/typeset-engine
docker build -t typeset-engine:v1 .
```
