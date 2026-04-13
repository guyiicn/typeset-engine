# typeset-engine

统一文档渲染引擎 v3。输入 JSON，输出 PDF / DOCX / PPTX / 图表 / 技术图 / AI幻灯片 / AI配图。

Docker 容器化，HTTP API（端口 9090），15 种 PDF 主题 + 20 种 PPTX slide layout。

---

## 快速开始

```bash
# 启动
docker run -d --name typeset-engine \
  -p 9091:9090 \
  -e GEMINI_API_KEY=你的key \
  -v /tmp/typeset-output:/app/output \
  typeset-engine:v3

# 验证
curl http://localhost:9091/health

# 生成 PDF（中金风格）
curl -X POST http://localhost:9091/render/pdf?theme=cicc \
  -H "Content-Type: application/json" \
  -d @report.json -o report.pdf

# 生成 PPTX（Goldman Sachs 风格）
curl -X POST http://localhost:9091/render/pptx \
  -H "Content-Type: application/json" \
  -d '{"theme":"goldman","title":"Report","slides":[...]}' -o deck.pptx

# 生成技术架构图（SVG → PNG）
curl -X POST http://localhost:9091/render/diagram \
  -H "Content-Type: application/json" \
  -d '{"svg":"<svg>...</svg>","width":1920}' -o diagram.png
```

> GEMINI_API_KEY 仅 pptx-ai / illustrate 需要，其他命令可不传。

---

## HTTP API 端点

| 端点 | 方法 | 输入 | 输出 | API Key |
|------|:----:|------|------|:-------:|
| `/render/pdf` | POST | 报告 JSON + `?theme=xxx` | PDF | 否 |
| `/render/docx` | POST | 报告 JSON + `?theme=xxx` | DOCX | 否 |
| `/render/pptx` | POST | 幻灯片 JSON | PPTX | 否 |
| `/render/chart` | POST | 图表 JSON | PNG | 否 |
| `/render/diagram` | POST | SVG 字符串 | PNG | 否 |
| `/render/pptx-ai` | POST | slides_plan JSON | ZIP | 是 |
| `/render/illustrate` | POST | 文本+风格 | PNG | 是 |
| `/styles` | GET | — | 风格列表 | 否 |
| `/capabilities` | GET | — | 全部能力描述 | 否 |
| `/health` | GET | — | 状态 | 否 |
| `/fonts` | GET | — | 字体列表 | 否 |

---

## PDF 主题（15 种）

### 金融投研（7 种）

| 主题 | 说明 | 配色 |
|------|------|------|
| `cicc` | 中金公司 CICC | 深蓝 #1a1a2e + 红 #c41e3a |
| `ms` | 摩根斯坦利 Morgan Stanley | 深蓝 #002D72 |
| `cms` | 招商证券 CMS | 红 #C1002A |
| `dachen` | 达晨财智 Fortune Capital | 暗红 #b8141d |
| `goldman` | Goldman Sachs | 深蓝 #003A70 + 浅蓝 #6CACE4 |
| `ubs` | UBS | 红 #E60000 |
| `whitepaper` | 技术白皮书（通用） | 灰蓝 #2C3E50 + 蓝 #3498DB |

### 咨询 MBB（3 种）

| 主题 | 说明 | 配色 |
|------|------|------|
| `mckinsey` | 麦肯锡 McKinsey | 深蓝 #00205B + 浅蓝 #009FDA |
| `bcg` | 波士顿咨询 BCG | 深绿 #00645A + 浅绿 #6CC24A |
| `bain` | 贝恩咨询 Bain | 红 #CC0000 + 金 #D4A843 |

### 公文（2 种）

| 主题 | 说明 | 字体 |
|------|------|------|
| `gongwen` | GB/T 9704 党政公文 | 方正小标宋 + 仿宋 + 黑体 |
| `tbs` | 电广传媒企业公文 | 预设 organ=湖南电广传媒股份有限公司 |

### 学术论文（3 种）

| 主题 | 说明 | 格式 |
|------|------|------|
| `ieee` | IEEE 双栏学术论文 | Liberation Serif, 10pt |
| `cn-paper` | 中文学术论文 | 宋体/黑体/楷体, 五号 |
| `working-paper` | SSRN 工作论文 | 英文通用学术 |

---

## PPTX Slide Layout（20 种）

### 通用（12 种）

| Layout | 说明 |
|--------|------|
| `title` | 封面 |
| `section` | 章节分隔页 |
| `content` | 正文（文字 + 可选图片 + bullet points） |
| `two_column` | 双栏（左文右图或左右文字） |
| `table` | 表格页 |
| `summary` | 总结页（深色底 + 要点） |
| `kpi` | KPI 指标卡片（3-6 个大数字） |
| `chart` | 全幅图表页 |
| `comparison` | 对比页（左右两栏） |
| `timeline` | 时间线（水平里程碑） |
| `quote` | 引用页 |
| `end` | 结束页 |

### 投行 Pitch Book（8 种）

| Layout | 说明 | 信息密度 |
|--------|------|:--------:|
| `comparable_companies` | 可比公司分析（宽表格 10-15 列 + Median/Mean 汇总） | 极高 |
| `football_field` | 估值区间图（横向条形 + 当前价格线） | 中 |
| `sources_uses` | 资金来源与用途（双栏对称表格） | 高 |
| `sensitivity_matrix` | 敏感性分析（WACC×TGR 二维矩阵 + base case 高亮） | 高 |
| `transaction_overview` | 交易概览（左侧要点 + 右侧条款表格） | 高 |
| `disclaimer` | 免责声明（小字体法律文本） | 低 |
| `waterfall` | 瀑布图/桥接分析（收入分解） | 中 |
| `org_chart` | 组织架构图（3 层树状） | 中 |

### PPTX 主题（6 种）

`default` / `cicc` / `goldman` / `morgan` / `dark` / `minimal`

---

## 技术架构图（7 种视觉风格）

通过 `/render/diagram` 端点，接收 SVG 字符串，用 `rsvg-convert` 导出 1920px PNG。

| # | 风格 | 背景 | 适用场景 |
|---|------|------|---------|
| 1 | Flat Icon 扁平 | 白底 | 文档、博客 |
| 2 | Dark Terminal 暗黑 | #0f0f1a | GitHub README |
| 3 | Blueprint 蓝图 | #0a1628 | 架构设计 |
| 4 | Notion Clean 极简 | 白底 | Wiki、Notion |
| 5 | Glassmorphism 玻璃态 | 深色渐变 | Keynote、官网 |
| 6 | Claude Official | #f8f6f3 | Anthropic 风格 |
| 7 | OpenAI Official | 白底 | OpenAI 风格 |

参考文件：`references/diagram/style-*.md`
SVG 模板：`references/diagram-templates/*.svg`（10 种图类型）
示例数据：`references/diagram-fixtures/*.json`（7 种风格示例）

---

## 公文 JSON 格式

```json
{
  "title": "关于XX的通知",
  "recipient": "各部门",
  "organ": "XX机关",
  "doc_type": "文件",
  "number": "XX发〔2026〕1号",
  "redhead_size": 30,
  "sections": [
    {"type": "paragraph", "content": "正文内容"},
    {"type": "heading", "title": "一、标题", "children": [
      {"type": "paragraph", "content": "子内容"}
    ]}
  ],
  "attachments": ["附件名称"],
  "signature_organ": "XX机关",
  "signature_date": "2026年4月13日",
  "cc": "抄送单位",
  "printer": "印发单位",
  "print_date": "2026年4月13日印发"
}
```

`tbs` 主题自动预设 `organ=湖南电广传媒股份有限公司`，只需传 `title` + `sections` + `signature_date`。

---

## 投行 PPTX JSON 示例

```json
{
  "title": "Project Alpha",
  "subtitle": "Strictly Confidential",
  "theme": "goldman",
  "slides": [
    {
      "layout": "comparable_companies",
      "title": "Comparable Companies Analysis",
      "headers": ["Company", "Mkt Cap", "EV/EBITDA", "P/E"],
      "rows": [["Co A", "$85bn", "11.2x", "18.5x"]],
      "summary_rows": [{"label": "Median", "values": ["$55bn", "10.3x", "16.2x"]}],
      "source": "Bloomberg"
    },
    {
      "layout": "football_field",
      "title": "Valuation Summary",
      "ranges": [
        {"method": "DCF", "low": 35.0, "high": 50.0},
        {"method": "Comps", "low": 32.0, "high": 42.0}
      ],
      "current_price": 38.5,
      "currency": "$"
    },
    {
      "layout": "sources_uses",
      "title": "Sources & Uses",
      "sources": [{"item": "Term Loan", "amount": 500}],
      "uses": [{"item": "Equity Purchase", "amount": 500}],
      "currency": "$m"
    }
  ]
}
```

---

## 学术论文 JSON 示例

```json
{
  "title": "Paper Title",
  "authors": [{"name": "Author", "organization": "University"}],
  "abstract": "Abstract text...",
  "keywords": ["AI", "NLP"],
  "sections": [
    {"type": "heading", "title": "Introduction", "children": [
      {"type": "paragraph", "content": "Content..."}
    ]}
  ]
}
```

使用 `?theme=ieee` / `?theme=cn-paper` / `?theme=working-paper`。

学位论文模板（SJTU/PKU/HUST）需直接编写 Typst 源码 import，不走 JSON API。

---

## 字体

Docker 镜像内置以下字体：

| 字体 | 用途 |
|------|------|
| 方正小标宋 (FZXiaoBiaoSong-B05) | 公文红头/标题 |
| SimHei 黑体 | 公文一级标题 |
| FangSong 仿宋 | 公文正文 |
| 方正仿宋 (FZFangSong-Z02) | 公文正文备选 |
| Noto Sans/Serif CJK SC | 通用中文 |
| AR PL UKai CN | 楷体 |
| cwTeX 系列 | 仿宋/黑体/楷体/明体 |
| Liberation Serif/Sans/Mono | Times/Arial/Courier 替代 |

---

## 图表（13 种）

`bar` / `line` / `area` / `pie` / `waterfall` / `scatter` / `heatmap` / `radar` / `funnel` / `gauge` / `treemap` / `candlestick` / `combo`

图表主题：`default` / `cicc` / `goldman` / `dark`

---

## 项目结构

```
typeset-engine/
├── Dockerfile                        # Docker 构建文件
├── README.md                         # 本文件
├── USAGE.md                          # CLI 详细用法
├── DOCS_INPUT_FORMAT.md              # DOCX 格式规范
│
├── scripts/                          # 渲染引擎
│   ├── server.py                     # HTTP API 服务器（端口 9090）
│   ├── render_pdf.py                 # PDF 渲染（Typst，15 主题）
│   ├── render_docx.py                # DOCX 渲染（python-docx）
│   ├── render_pptx.py                # PPTX 渲染（python-pptx，20 layout）
│   ├── render_pptx_ai.py             # AI PPT（Gemini + FFmpeg）
│   ├── render_charts.py              # 图表渲染（Plotly，13 种）
│   ├── render_diagram.py             # 技术图渲染（SVG → PNG，rsvg-convert）
│   ├── render_illustrate.py          # AI 配图（Gemini）
│   ├── validate_docx.py              # DOCX JSON 校验
│   └── file_diff.py                  # 文件对比
│
├── templates/                        # 排版模板
│   ├── cicc-report.typ               # 投研报告 Typst 主模板
│   ├── themes.typ                    # 15 个 PDF 主题配色定义
│   ├── gongwen.typ                   # GB/T 9704 公文模板
│   └── academic/                     # 学术论文模板
│       ├── ieee/lib.typ              # IEEE 双栏论文
│       ├── cn-paper/lib.typ          # 中文学术论文
│       ├── working-paper/lib.typ     # SSRN 工作论文
│       ├── sjtu-thesis/              # 上海交大学位论文（19 文件）
│       ├── pku-thesis/               # 北京大学学位论文（7 文件）
│       └── hust-thesis/              # 华中科大学位论文（25 文件）
│
├── references/                       # 技术图参考资料
│   ├── diagram/                      # 7 种风格参考 + icons + 布局规范
│   ├── diagram-templates/            # 10 种图类型 SVG 模板
│   └── diagram-fixtures/             # 7 种风格 JSON 示例数据
│
├── fonts/                            # 公文字体
│   ├── 方正小标宋GBK.TTF
│   ├── SIMHEI.TTF
│   ├── SIMFANG.TTF
│   └── FZFS_GBK.ttf
│
├── styles/                           # AI PPT 风格定义
│   ├── gradient-glass.md
│   ├── vector-illustration.md
│   └── ticket.md
│
└── tests/                            # 单元测试
```

---

## 依赖

Docker 镜像包含：

- **Typst 0.14.0** — PDF 排版引擎
- **python-pptx** — PPTX 生成
- **python-docx** — DOCX 生成
- **Plotly + Kaleido + Chrome** — 图表渲染
- **librsvg2 (rsvg-convert)** — SVG → PNG
- **FFmpeg** — 视频合成
- **ImageMagick** — 图片处理
- **Google Gemini SDK** — AI 图片/PPT 生成

---

## License

MIT
