# typeset-engine

统一文档渲染引擎。输入 JSON，输出 PDF / DOCX / PPTX / 图表 / 技术图 / AI幻灯片 / AI配图。

HTTP API（端口 9090），15 种 PDF 主题 + 20 种 PPTX slide layout + 14 种 kami HTML 模板。

---

## 🚨 已部署过 docker 版的请先读这里

**2026-05-19 起 `master` 已切换为 native 部署（systemd + .venv），原 docker 路线归档到
`legacy-docker` 分支。** 如果你之前 `docker run typeset-engine:v1`~`v4`，按下面读：

→ **完整迁移指引**：[`docs/MIGRATION-docker-to-native.md`](docs/MIGRATION-docker-to-native.md)
（含老 docker 用户怎么识别状态 / 5 分钟升级步骤 / 配置迁移表 / 端口差异 9090 vs 9091 /
回退方案 / 删 docker 资产的命令）

**TL;DR**（已部署 docker 的）：
```bash
git pull origin master
sudo -E bash deploy/native/install.sh   # 自动从 ~/.env 注入 GEMINI key
sudo systemctl enable --now typeset
curl http://localhost:9090/health
docker stop typeset-engine              # 观察 1-3 天没问题再 docker rm
```

---

## 分支状态

| 分支 | 角色 |
|---|---|
| **`master`** | ✅ **canonical**（GitHub default）— native 部署，所有 fix / 新特性都到这边 |
| `legacy-docker` | 🗄️ **frozen archive** — 老 master force push 前的备份，包含 `Dockerfile` / `docker-compose.yaml` 历史。仅用于查阅，不再有新 commit |

> 📌 `deploy/native` 分支已删除（2026-05-19）— 它指向跟 master 相同 HEAD，已合并完毕。
> 老 clone 用 `git checkout master && git pull` 切回主线。目录 `deploy/native/` 仍保留
> （安装脚本和 systemd unit 在那里，跟分支名是巧合同名）。

部署详见：[`deploy/native/README.md`](deploy/native/README.md)（native 安装步骤）

---

## 快速开始（新装机器）

```bash
# 1. 装 native (5 分钟)
git clone https://github.com/guyiicn/typeset-engine.git
cd typeset-engine
echo 'GEMINI_API_KEY=AIza...' >> ~/.env   # billing-enabled GCP 项目的 key
sudo -E bash deploy/native/install.sh
sudo systemctl enable --now typeset

# 2. 验证
curl http://localhost:9090/health
# 期望: {"status":"ok","engine":"typeset-engine","version":"1.0"}

# 3. 生成 PDF (中金风格)
curl -X POST http://localhost:9090/render/pdf \
  -H "Content-Type: application/json" \
  -d '{"theme":"cicc","title":"测试","sections":[{"type":"heading","title":"内容"}]}' \
  -o report.pdf

# 4. 生成 PPTX (高盛风格)
curl -X POST http://localhost:9090/render/pptx \
  -H "Content-Type: application/json" \
  -d '{"template":"goldman","title":"Report","slides":[{"layout":"section","title":"...","subtitle":"..."}]}' \
  -o deck.pptx

# 5. 生成技术架构图 (SVG → PNG)
curl -X POST http://localhost:9090/render/diagram \
  -H "Content-Type: application/json" \
  -d '{"svg":"<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"400\" height=\"200\">...</svg>","width":1920}' \
  -o diagram.png
```

完整 API 文档：[`USAGE.md`](USAGE.md)（**16 端点** schema + 15 PDF 主题 + 20 PPTX layout +
14 kami 模板 + 错误处理 + 5 条常见坑）

> **GEMINI_API_KEY** 仅 `pptx-ai` / `illustrate` 需要，其他命令可不传。
>
> ⚠️ **必须是 billing-enabled GCP 项目的 key** — Google 对图像生成模型
> (`gemini-2.5-flash-image`) 的 free tier 配额为 0，free key 调 illustrate
> 会得到 `429 RESOURCE_EXHAUSTED` (报错里 model 显示成 `-preview-image`
> 是 Google 服务端配额计费名，跟代码里实际传的不同，别被迷惑)。

---

## HTTP API 端点（16 个）

| 端点 | 方法 | 输入 | 输出 | API Key |
|------|:----:|------|------|:-------:|
| `/render/pdf` | POST | 报告 JSON + `theme` | PDF | 否 |
| `/render/pdf-md` | POST | `{markdown, title, theme?}` | PDF | 否 |
| `/render/docx` | POST | 报告 JSON + `theme` | DOCX | 否 |
| `/render/docx-md` | POST | `{markdown, title, theme?}` | DOCX | 否 |
| `/render/pptx` | POST | 幻灯片 JSON | PPTX | 否 |
| `/render/chart` | POST | 图表 JSON | PNG | 否 |
| `/render/diagram` | POST | SVG 字符串 | PNG/SVG | 否 |
| `/render/kami` | POST | HTML / body_html / slots | PDF | 否 |
| `/render/pptx-ai` | POST | slides_plan JSON | ZIP | **billing** |
| `/render/illustrate` | POST | 文本 + 风格 | PNG | **billing** |
| `/validate/css` | POST | `{content, filename?, only?}` | JSON | 否 |
| `/styles` | GET | — | AI 配图风格列表 | 否 |
| `/capabilities` | GET | — | 全部能力描述 | 否 |
| `/health` | GET | — | liveness | 否 |
| `/fonts` | GET | — | 系统字体列表 | 否 |
| `/kami/templates` | GET | — | kami 14 模板矩阵 | 否 |
| `/kami/template/{doc_type}` | GET | `?lang=zh\|en` | HTML 模板源码 | 否 |

> `-md` 后缀的两个端点是 markdown shortcut（commit a39794a 加）—— 直接传 markdown 字符串，
> 服务端用 `scripts/md_to_typeset.py` 转 sections JSON 后走 `/render/pdf` 或 `/render/docx`，
> 兼容所有 `theme`。适合调用方已经有 markdown 内容时省去构造 sections JSON 的麻烦。

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

## Kami HTML 模板（14 种）

`/render/kami` 端点用 WeasyPrint 把 HTML 渲染成 PDF，模板放在 `templates/kami/`。

### 标准模板（5 类型 × zh/en = 10 个）

| 模板 | 中文 / 英文 | 页数约束 | 适用 |
|------|:---:|:---:|------|
| `one-pager` | ✓ / ✓ | 1 | 一页纸总结 / 招股说明摘要 |
| `letter` | ✓ / ✓ | 1 | 正式商务信件 |
| `resume` | ✓ / ✓ | 1-2 | 个人简历 |
| `portfolio` | ✓ / ✓ | 4-8 | 作品集 / 个人介绍 |
| `long-doc` | ✓ / ✓ | 5-9 | 商务长文 / 战略推演（深蓝 #1B365D 强调）|

### 长文变体（仅 zh, 4 个）

| 模板 | 强调色 / 风格 | 页数约束 | 适用 |
|------|------|:---:|------|
| `long-doc-claude` | **烧橙 #d97757 + 鼠尾草绿 #788c5d** | 5-80 | Anthropic Claude 风格管理稿 |
| `long-doc-openai` | OpenAI 黑白调 | 5-100 | OpenAI 风格大体量长报告 |
| `long-doc-starwars` | Star Wars 黄 #FFE81F + 深空蓝 + EPISODE 罗马数字章节扉页 | 5-80 | 内部 / 创意 only（非外发客户）|
| `founders-playbook` | 7 色循环扉页（Coral/Teal/Purple/Mint/Lavender/Peach/Warm Gray）+ Claude 太阳花 logo | 10-40 | 创始人指南 / 数据驱动长文 |

> `founders-playbook` 是**数据驱动模式**（不走模板替换）：必须传 `slots = {title, subtitle, chapters: [{number, title, mode, body}]}`，
> 每个 chapter `mode` 取 `full`/`minimal`/`plain` 控制扉页类型。详见 `scripts/render_kami.py:_build_fpb_html`。

### 3 种调用模式

```bash
# 模式 1: 整 HTML 自己拼 (最灵活)
curl -X POST http://localhost:9091/render/kami -H 'Content-Type: application/json' \
  -d '{"html": "<!DOCTYPE html><html>...</html>"}' -o output.pdf

# 模式 2: 模板 + body_html 替换 (保留模板 CSS, 换 body)
curl -X POST http://localhost:9091/render/kami -H 'Content-Type: application/json' \
  -d '{"doc_type":"resume","language":"en","body_html":"<h1>Name</h1>..."}' -o resume.pdf

# 模式 3: 模板 + slots 替换 ({{key}} 占位符替换, 支持中文 key)
curl -X POST http://localhost:9091/render/kami -H 'Content-Type: application/json' \
  -d '{"doc_type":"one-pager","language":"zh","slots":{"文档标题":"...","作者":"..."}}' -o brief.pdf
```

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

native 部署用宿主机系统字体（`fc-list` 看到的）。install.sh 不另装字体；公文模板专用的方正字体打包在仓库 `fonts/` 目录。

### 仓库自带（公文专用，install.sh 会注册到 fontconfig）

| 字体 | 用途 |
|------|------|
| 方正小标宋 (FZXiaoBiaoSong-B05) | 公文红头/标题 |
| SimHei 黑体 (SIMHEI.TTF) | 公文一级标题 |
| FangSong 仿宋 (SIMFANG.TTF) | 公文正文 |
| 方正仿宋 (FZFangSong-Z02 / FZFS_GBK) | 公文正文备选 |

### 系统应有（apt 装 `fonts-noto-cjk fonts-noto-cjk-extra`）

| 字体 | 用途 |
|------|------|
| Noto Sans / Serif CJK SC | 通用中文（fallback 链首选）|
| Source Han Serif SC | kami / founders-playbook 中文正文 |
| Liberation Serif / Sans / Mono | Times / Arial / Courier 通用替代 |
| AnthropicSerif / AnthropicSans | kami `long-doc-claude` 英文（变量字体）|

> 系统没装中文字体会让中文文本 fallback 出乱码 / 方框。装：
> `sudo apt install fonts-noto-cjk fonts-noto-cjk-extra`

---

## 图表（13 种）

`bar` / `line` / `area` / `pie` / `waterfall` / `scatter` / `heatmap` / `radar` / `funnel` / `gauge` / `treemap` / `candlestick` / `combo`

图表主题：`default` / `cicc` / `goldman` / `dark`

---

## 项目结构

```
typeset-engine/
├── README.md                         # 本文件
├── USAGE.md                          # HTTP API 详细用法
├── DOCS_INPUT_FORMAT.md              # DOCX JSON 格式规范
│
├── deploy/native/                    # 部署 (canonical 路径)
│   ├── install.sh                    # 一键 native 安装 (systemd + venv)
│   ├── env.example                   # /etc/typeset/typeset.env 模板
│   ├── typeset.service               # systemd unit
│   ├── requirements.txt              # Python 运行时依赖
│   ├── check-drift.sh                # 检查远端 vs 本地 commit drift
│   └── README.md                     # 部署详细步骤
│
├── docs/
│   ├── MIGRATION-docker-to-native.md # 老 docker 用户升级指引 (260 行)
│   ├── founders-playbook.md          # founders-playbook 模板规范
│   └── founders-playbook-plan.md     # 设计文档
│
├── scripts/                          # 渲染引擎
│   ├── server.py                     # HTTP API 服务器
│   ├── render_pdf.py                 # PDF 渲染 (Typst, 15 主题)
│   ├── render_docx.py                # DOCX 渲染 (python-docx)
│   ├── render_pptx.py                # PPTX 渲染 (python-pptx, 20 layout)
│   ├── render_pptx_ai.py             # AI PPT (Gemini + FFmpeg)
│   ├── render_charts.py              # 图表渲染 (Plotly, 13 种)
│   ├── render_diagram.py             # 技术图渲染 (SVG → PNG, rsvg-convert)
│   ├── render_illustrate.py          # AI 配图 (Gemini)
│   ├── render_kami.py                # Kami HTML→PDF (WeasyPrint, 14 模板)
│   ├── md_to_typeset.py              # markdown → typeset JSON 转换器
│   ├── validate_kami.py              # Kami 9 条美学约束扫描
│   ├── validate_docx.py              # DOCX JSON 校验
│   └── file_diff.py                  # 文件对比
│
├── templates/                        # 排版模板
│   ├── themes.typ                    # 15 个 PDF 主题配色定义
│   ├── cicc-report.typ               # 投研报告 Typst 主模板
│   ├── gongwen.typ                   # GB/T 9704 公文模板
│   ├── kami/                         # 14 个 kami HTML 模板
│   │   ├── one-pager.html / one-pager-en.html
│   │   ├── letter.html / letter-en.html
│   │   ├── resume.html / resume-en.html
│   │   ├── portfolio.html / portfolio-en.html
│   │   ├── long-doc.html / long-doc-en.html
│   │   ├── long-doc-claude.html      # 烧橙 Anthropic 风
│   │   ├── long-doc-openai.html      # OpenAI 黑白调
│   │   ├── long-doc-starwars.html    # Star Wars 视觉
│   │   └── founders-playbook.html    # 数据驱动创始人指南
│   └── academic/                     # 学术论文 Typst 模板
│       ├── ieee/lib.typ              # IEEE 双栏论文
│       ├── cn-paper/lib.typ          # 中文学术论文
│       ├── working-paper/lib.typ     # SSRN 工作论文
│       ├── sjtu-thesis/              # 上海交大学位论文 (19 文件)
│       ├── pku-thesis/               # 北京大学学位论文 (7 文件)
│       └── hust-thesis/              # 华中科大学位论文 (25 文件)
│
├── skill/                            # openclaw skill (2026-05-19 从 ~/.openclaw/skills 搬入)
│   ├── SKILL.md                      # 上游调用 agent 的 5 步工作流
│   └── references/                   # api-reference / design-constraints / workflow
│
├── references/                       # 技术图参考资料
│   ├── diagram/                      # 7 种风格参考 + icons + 布局规范
│   ├── diagram-templates/            # 10 种图类型 SVG 模板
│   └── diagram-fixtures/             # 7 种风格 JSON 示例数据
│
├── fonts/                            # 公文专用字体 (install.sh 注册到 fontconfig)
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
└── tests/                            # 单元测试 (pytest 兼容, stdlib-only)
    ├── test_render_pptx_layouts.py   # 20 layout 全覆盖 (21/21 通过)
    ├── test_kami_unicode_slots.py    # _apply_slots 中文 key 支持 (8/8)
    ├── test_kami_template_sanity.py  # 模板 lint (4/4)
    ├── test_render_kami.py           # kami 渲染端到端
    ├── test_validate_kami.py         # 9 美学约束扫描
    ├── test_render_docx.py
    └── test_fpb.py                   # founders-playbook 端到端
```

> 历史 `Dockerfile` / `docker-compose.yaml` 已归档到 `legacy-docker` 分支（2026-05-19），
> master 分支已无 docker 文件。如需查阅 docker 时代代码 `git checkout legacy-docker`。

---

## 运行时依赖

native 部署，`install.sh` 装：

| 组件 | 版本 / 用途 |
|------|------|
| Python | 3.10+ (推荐 system `python3.12`, **不要用 anaconda**, 见 MIGRATION 文档坑 1) |
| **Typst** | 0.14.0 — PDF 排版引擎（install.sh 装到 `~/.local/bin/typst`）|
| **WeasyPrint** 68.1 | Kami HTML→PDF |
| **python-pptx** 1.0.2 | PPTX 生成 |
| **python-docx** 1.2.0 | DOCX 生成 |
| **Plotly** 6.7 + **Kaleido** 1.2 + **Chrome** | 图表渲染（Chrome 从仓库 `native-v1.0` release 下，148MB）|
| **librsvg2 (rsvg-convert)** | SVG → PNG（apt 装 `librsvg2-bin`）|
| **FFmpeg** | 视频合成（仅 `/render/pptx-ai`）|
| **google-genai** 1.73 | Gemini API (illustrate / pptx-ai, **需 billing key**) |
| **libpango/libcairo/libgdk-pixbuf** | WeasyPrint 系统库（apt 装）|

完整 pip 清单见 [`deploy/native/requirements.txt`](deploy/native/requirements.txt)。

---

## License

MIT
