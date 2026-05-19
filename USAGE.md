# typeset-engine 使用指南 (HTTP API)

统一文档渲染引擎 — 输入 JSON，输出 PDF / DOCX / PPTX / PNG / SVG / ZIP。

> ℹ️ Docker 路线已在 transition (commit `97cfb58`)，**新接入请走 native 部署**
> (`deploy/native` 分支)。本指南只覆盖 HTTP API，不再描述 docker CLI 用法。

---

## 部署/调用基础

| 节点 | URL | 备注 |
|---|---|---|
| sg2 公网 | `http://sg2.guyii.net:9090` | 验收通过，待加 nginx 反代 |
| 本机 docker (过渡) | `http://localhost:9091` | bind-mount 本地 `deploy/native` 代码 |
| 本机 native (规划) | `http://localhost:9092` | TBD |

约定：

- 所有端点 **无认证**（内网/受信网络部署），生产环境请在前端加 nginx + basic auth
- POST 端点接受 `Content-Type: application/json`；响应文件直接 stream 二进制
- 错误统一返回 `{"error": "..."}` + HTTP 4xx/5xx
- 输出文件**不落盘**，传完即清理

---

## 端点速查

| 端点 | 方法 | 输出 | GEMINI key |
|---|---|---|---|
| `/health` | GET | JSON | — |
| `/capabilities` | GET | JSON | — |
| `/styles` | GET | JSON | — |
| `/fonts` | GET | JSON | — |
| `/kami/templates` | GET | JSON | — |
| `/kami/template/{doc_type}?lang=zh\|en` | GET | HTML | — |
| `/render/pdf` | POST | PDF | — |
| `/render/docx` | POST | DOCX | — |
| `/render/pptx` | POST | PPTX | — |
| `/render/pptx-ai` | POST | ZIP (PNG + HTML + MP4) | ✅ billing |
| `/render/chart` | POST | PNG | — |
| `/render/diagram` | POST | PNG/SVG | — |
| `/render/illustrate` | POST | PNG | ✅ billing |
| `/render/kami` | POST | PDF | — |
| `/validate/css` | POST | JSON | — |

> ⚠️ **GEMINI_API_KEY 必须来自 billing-enabled GCP 项目** — Google 对图像生成模型
> (`gemini-2.5-flash-image`) free tier 配额为 0，free key 调 illustrate / pptx-ai
> 会得到 `429 RESOURCE_EXHAUSTED`。

---

## GET 端点

### GET /health
liveness 探针。
```bash
curl http://localhost:9090/health
# {"status":"ok","engine":"typeset-engine","version":"1.0"}
```

### GET /capabilities
返回所有可用端点 + 各自支持的 theme / type / language 等元数据。
```bash
curl http://localhost:9090/capabilities
```

### GET /styles
列出 AI 配图风格（gradient-glass / vector-illustration / ticket）。
```bash
curl http://localhost:9090/styles
```

### GET /fonts
列出 matplotlib 注册的所有可用字体。
```bash
curl http://localhost:9090/fonts
# {"count": 74, "fonts": ["Arial", "Source Han Serif CN", ...]}
```

### GET /kami/templates
列出 kami 引擎所有可用模板（doc_type × language 矩阵）。
```bash
curl http://localhost:9090/kami/templates
```

### GET /kami/template/{doc_type}?lang=zh|en
返回指定模板的 HTML 源码（用于客户端按 schema 拼装 body 再 POST 回 `/render/kami`）。
```bash
curl 'http://localhost:9090/kami/template/resume?lang=en'
```

---

## POST 渲染端点

### POST /render/pdf
Typst 引擎渲染投研报告级 PDF。

**请求**:
```json
{
  "theme": "cicc",
  "title": "贵州茅台 研究报告",
  "subtitle": "600519 | 白酒/消费",
  "author": "DeerFlow",
  "date": "2026-05-19",
  "toc": true,
  "charts": [
    {"id": "rev", "type": "bar", "data": {"categories": ["22","23","24"],
                                          "series": [{"name":"营收","values":[100,120,150]}]}}
  ],
  "sections": [
    {"type": "heading", "title": "公司概况",
     "children": [
       {"type": "paragraph", "content": "..."},
       {"type": "kpi", "metrics": [
         {"label": "目标价", "value": "¥2,200", "change": "+15%"},
         {"label": "评级", "value": "买入"}
       ]},
       {"type": "chart", "chart_id": "rev", "caption": "图1：营收"},
       {"type": "table", "headers": ["指标","2024"], "rows": [["营收","150"]]}
     ]}
  ],
  "disclaimer": "免责声明..."
}
```

**theme**: `cicc` / `ms` / `cms` / `dachen` (默认 `cicc`)

**section type**: `heading` / `paragraph` / `quote` / `table` / `chart` / `kpi` / `ai-image` / `pagebreak`

**curl**:
```bash
curl -X POST http://localhost:9090/render/pdf \
  -H 'Content-Type: application/json' \
  -d @report.json -o report.pdf
```

---

### POST /render/docx
schema 跟 `/render/pdf` 完全一致（同一份 JSON 可同时出 PDF + DOCX + PPTX）。

**theme**: 与 PDF 相同（cicc / ms / cms / dachen）

**curl**:
```bash
curl -X POST http://localhost:9090/render/docx \
  -H 'Content-Type: application/json' \
  -d @report.json -o report.docx
```

---

### POST /render/pptx
python-pptx 渲染结构化演示文稿，支持 **20 种 layout**。完整 schema 见
`scripts/render_pptx.py` docstring + `tests/test_render_pptx_layouts.py`（21/21 测试覆盖）。

**顶层结构**:
```json
{
  "template": "cicc",
  "title": "封面标题",
  "subtitle": "副标题",
  "author": "作者",
  "date": "2026-05-19",
  "slides": [ {...每页一个 layout 对象...} ]
}
```
顶层 `title` 字段非空时，会自动加一张封面 slide（cover），再追加 `slides[]`。

**template**: `default` / `cicc` / `goldman` / `morgan` / `dark` / `minimal`

#### 通用 12 种 layout

| layout | 主要字段 |
|---|---|
| `title` | `title`, `subtitle` |
| `section` | `title`, `subtitle` |
| `content` | `title`, `content`, `bullets[]`, `image`, `notes` |
| `two_column` | `title`, `left_content`, `right_content`, `image` (替代右栏) |
| `table` | `title`, `headers[]`, `rows[][]`  ← 直接放顶层，**不是嵌在 "table" 对象里** |
| `summary` | `title`, `bullets[]` (或 `points[]`) |
| `chart` | `title`, `image`, `caption` (image 路径不存在则跳过图片，保留 title) |
| `kpi` | `title`, `kpis[{label,value,change}]` |
| `comparison` | `title`, `left_title`, `left_items[]`, `right_title`, `right_items[]` |
| `timeline` | `title`, `events[{date,event}]` |
| `quote` | `quote` (或 `content`), `author`, `source` |
| `end` | `title`, `subtitle`, `contact` |

#### 投行 Pitch Book 专用 8 种 layout

| layout | 主要字段 |
|---|---|
| `comparable_companies` | `headers[]`, `rows[][]`, `summary_rows[][]`, `source` |
| `football_field` | `ranges[{method,low,high}]`, `current_price`, `currency`, `source` |
| `sources_uses` | `sources[{item,amount}]`, `uses[{item,amount}]`, `currency`, `source` |
| `sensitivity_matrix` | `row_label`, `col_label`, `row_values[]`, `col_values[]`, `matrix[][]`, `highlight_row`, `highlight_col`, `source` |
| `transaction_overview` | `key_points[]` (或 `bullets`), `terms[{label,value}]`, `source` |
| `disclaimer` | `content` (或 `text`), `title` |
| `waterfall` | `items[{label,value,type:"total\|positive\|negative"}]`, `currency`, `source` |
| `org_chart` | `root{name,title,children[]}`, `source` |

**curl 示例**:
```bash
curl -X POST http://localhost:9090/render/pptx \
  -H 'Content-Type: application/json' \
  -d '{
    "template": "cicc",
    "title": "公司分析",
    "slides": [
      {"layout": "section", "title": "财务概览"},
      {"layout": "kpi", "title": "核心指标", "kpis": [
        {"label":"营收","value":"¥150亿","change":"+25%"},
        {"label":"利润","value":"¥55亿","change":"+37%"}
      ]},
      {"layout": "table", "title": "对比",
       "headers": ["指标","2023","2024"],
       "rows": [["营收","120","150"],["利润","40","55"]]}
    ]
  }' -o slides.pptx
```

**⚠️ 常见坑**: `table` layout 的 `headers`/`rows` 必须**直接放在 slide 对象顶层**，写成
`"table": {"headers":..., "rows":...}` 嵌套形式会触发 `ZeroDivisionError: cols=0`
(老 docstring 的误导，已在 commit `13953a3` 修正)。

---

### POST /render/pptx-ai
Gemini 生成精美幻灯片图片 + HTML 播放器 + 可选 MP4 视频。
**需要 GEMINI_API_KEY (billing)**，返回 ZIP。

**请求**:
```json
{
  "style": "gradient-glass",
  "resolution": "2K",
  "video": true,
  "title": "公司介绍",
  "slides": [
    {"type": "cover", "content": "公司名"},
    {"type": "content", "content": "我们做..."},
    {"type": "data", "content": "营收 +30%"}
  ]
}
```

**style**: `gradient-glass` (玻璃科技) / `vector-illustration` (矢量插画) / `ticket` (信息票券)
**resolution**: `2K` / `4K`
**video**: `true` → 含 `presentation.mp4`

**返回** (ZIP 内容):
- `slides/slide_001.png` …
- `index.html` 自包含播放器
- `presentation.mp4` (video=true)
- `prompts.json` 调用 Gemini 时的 prompt 记录

```bash
curl -X POST http://localhost:9090/render/pptx-ai \
  -H 'Content-Type: application/json' \
  -d @slides_plan.json -o ai_ppt.zip
```

---

### POST /render/chart
plotly + kaleido 渲染商业图表。

**请求**:
```json
{
  "type": "bar",
  "theme": "cicc",
  "data": {
    "title": "营收对比",
    "categories": ["2022","2023","2024"],
    "series": [{"name":"营收","values":[100,120,150]},
               {"name":"利润","values":[30,40,55]}]
  }
}
```

**type (13)**: `bar` / `line` / `area` / `pie` / `waterfall` / `scatter` / `heatmap` / `radar` / `funnel` / `gauge` / `treemap` / `candlestick` / `combo`

**theme**: `default` / `cicc` / `goldman` / `dark`

```bash
curl -X POST http://localhost:9090/render/chart \
  -H 'Content-Type: application/json' \
  -d @chart.json -o chart.png
```

---

### POST /render/diagram
SVG 技术图 → PNG (via rsvg-convert)。

**请求**:
```json
{
  "svg": "<svg xmlns='http://www.w3.org/2000/svg' width='400' height='300'>...</svg>",
  "width": 1920,
  "format": "png",
  "validate": false
}
```

**format**: `png` / `svg` / `both`
**validate=true**: 仅做 SVG 语法校验，返回 JSON 不渲染

```bash
curl -X POST http://localhost:9090/render/diagram \
  -H 'Content-Type: application/json' \
  -d '{"svg":"<svg ...></svg>","width":1920}' -o diagram.png
```

---

### POST /render/illustrate
Gemini 给文本生成单张配图。**需要 GEMINI_API_KEY (billing)**。

**请求**:
```json
{
  "content": "AI 多智能体协作架构 — 路由/执行/反馈三模块协同",
  "style": "gradient-glass",
  "title": "Multi-Agent Architecture",
  "ratio": "16:9",
  "cover": false
}
```

**style**: `gradient-glass` / `vector-illustration` / `ticket`
**ratio**: `16:9` / `3:4` / `1:1`
**cover=true**: 封面模式 (居中标题强化)

**返回**: PNG (典型 1024×1024，~800KB，9-12s)

```bash
curl -X POST http://localhost:9090/render/illustrate \
  -H 'Content-Type: application/json' \
  -d @illustrate.json -o illustration.png
```

---

### POST /render/kami
WeasyPrint 渲染暖米纸 + 油墨蓝 + serif 风格 PDF（编辑级精排）。

支持 **3 种输入模式**（优先级 `html` > `body_html` > `slots`）：

#### 模式 1: 整 HTML
```json
{"html": "<!doctype html><html>...</html>",
 "base_url": "/path/for/relative/resources"}
```

#### 模式 2: 模板 + body 替换
```json
{"doc_type": "resume", "language": "en",
 "body_html": "<div>resume body...</div>"}
```

#### 模式 3: 模板 + slots
```json
{"doc_type": "one-pager", "language": "zh",
 "slots": {"title": "...", "subtitle": "...", ...}}
```

**doc_type (6)**: `one-pager` / `long-doc` / `letter` / `portfolio` / `resume` / `founders-playbook`

**language**: `zh` / `en`

#### founders-playbook 数据驱动模式 (special slots)

`founders-playbook` doc_type 不走模板替换，而是按 `slots.chapters[]` 动态拼装封面 + 目录 + 章节扉页 + 正文 + 封底：

```json
{
  "doc_type": "founders-playbook",
  "language": "zh",
  "slots": {
    "title": "创始人指南",
    "subtitle": "打造原生 AI 初创企业",
    "mode": "full",
    "chapters": [
      {"number": 1, "title": "缘起", "mode": "full",
       "body": "<p>第一章正文 HTML...</p>"},
      {"number": 2, "title": "实践", "mode": "minimal",
       "body": "<p>第二章正文 HTML...</p>"}
    ]
  }
}
```

**chapter.mode**:
- `full` — 彩色扉页 + 白底正文页 (2 页)
- `minimal` — 白底标题页 + 白底正文页 (2 页)
- `plain` — 仅正文页 (1 页)

**页数估算**: 封面 1 + 目录 1 + Σ(章节页数) + 封底 1 (PAGE_LIMITS 检查 10-40 页)

**章节配色循环 (7 色)**: Coral / Teal / Purple / Mint / Lavender / Peach / Warm Gray

**响应头**:
- `X-Kami-Pages`: 实际页数
- `X-Kami-Warnings`: 页数超约束时含 JSON 数组

```bash
curl -X POST http://localhost:9090/render/kami \
  -H 'Content-Type: application/json' \
  -d @kami_payload.json -o output.pdf
```

---

### POST /validate/css
Kami 美学宪法扫描 — 9 条约束（rgba / coolgray / white / lineheight / boldserif / hardshadow / thinborder / vh / flexbreak）。

```json
{
  "content": "<style>.x { color: #3d3d3a; line-height: 1.7; }</style>",
  "filename": "sample.css",
  "only": ["coolgray", "lineheight"]
}
```

**filename**: 可选，用文件后缀判别规则适用范围 (.html/.css/.typ/.py/.md)
**only**: 可选，仅跑指定子规则

返回 `validate_kami.py --format json` 原样输出。

---

## 错误处理

所有错误统一格式：
```json
{"error": "错误描述"}
```

| HTTP | 触发场景 |
|---|---|
| 400 | JSON 解析失败 / 缺必填字段 (如 kami 无 `doc_type` 也无 `html`) |
| 404 | 未知端点 / 模板不存在 |
| 500 | 渲染抛异常 (Typst 编译错 / weasyprint 字体缺失 / Gemini 429 等) |

**调试**: 服务端会把完整 traceback 打到 stderr/journal，部署后用：
```bash
journalctl -u typeset -f       # native 部署
docker logs -f typeset-engine  # docker 过渡期
```

---

## 常见坑 (踩过的)

| 症状 | 根因 | 解法 |
|---|---|---|
| `/render/pptx` 报 `ZeroDivisionError: cols=0` | 老 docstring 误导，`table` layout 把 headers/rows 嵌在了 `"table": {}` 对象里 | headers/rows **必须直接放 slide 顶层**，见上面 pptx 章节 |
| `/render/illustrate` 报 `429 RESOURCE_EXHAUSTED` | GEMINI key 所属 GCP 项目对图像生成 free tier 配额 = 0 | 用 **billing-enabled** 项目的 key |
| 429 报错里 model 名是 `-preview-image`，跟代码传的 `-flash-image` 不一样 | Google 服务端配额计费名 vs 代码 API 调用名是两套名字 | **别去改代码**，是 Google 内部行为 |
| PPT cicc 主题中文在 mac PowerPoint 显示空白 | theme 指定 `Noto Sans CJK SC`，本地 PowerPoint 找不到且 fallback 失败 | 改用 kami / founders-playbook PDF 路线 (字体 embed)，或修 cicc theme fallback |
| install 时 `Chrome 路径验证失败` warning | install 脚本 expect 路径跟实际 tarball 解压路径不一致 | 误报，binary 实际在 `…/browser_exe/chrome-linux64/chrome`，可忽略 |

---

## 跟其他模块的契约

- **openclaw skill** (`~/.openclaw/skills/typeset-engine/`) — 上游调用方，端口 / OUTPUT_DIR 改动需同步 SKILL.md
- **输出目录** (`OUTPUT_DIR=/var/lib/typeset/output` native / `/app/output` docker bind) — 调用方默认 `/tmp/typeset-output/`，是上层契约，改动要双向同步
- **GEMINI_API_KEY** 来源 (按优先级)：
  1. install 时传入 `sudo -E GEMINI_API_KEY=... bash install.sh`
  2. `$SUDO_USER` 家目录 `~/.env` 里 `GEMINI_API_KEY=`
  3. 运行后手动编辑 `/etc/typeset/typeset.env`

---

## 相关文档

- `README.md` — 项目主页 + 主题清单 + 快速 curl 示例
- `deploy/native/README.md` — native 部署详细步骤 + 升级 / 重置
- `scripts/render_pptx.py` docstring — 20 种 pptx layout 完整 schema
- `tests/test_render_pptx_layouts.py` — 21 个 layout 测试，每个 layout 对应一份最小 payload
