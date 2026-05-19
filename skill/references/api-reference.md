# typeset-engine API 全量参考

T1+ 任务必读。本文档是严格的 API 契约参考。

**Base URL**: `http://localhost:9091`

---

## 端点总览

| 端点 | 方法 | 用途 | 输出 | 需 Gemini |
|---|---|---|---|:---:|
| `/health` | GET | 健康检查 | JSON | 否 |
| `/capabilities` | GET | 全部能力描述 | JSON | 否 |
| `/styles` | GET | 所有 theme / style | JSON | 否 |
| `/render/pdf` | POST | PDF 报告 | PDF | 否 |
| `/render/docx` | POST | Word 文档 | DOCX | 否 |
| `/render/pptx` | POST | 幻灯片（手工） | PPTX | 否 |
| `/render/chart` | POST | 单个图表 | PNG | 否 |
| `/render/pptx-ai` | POST | AI 生成全套 PPT | ZIP（含 PPTX + 图片） | **是** |
| `/render/illustrate` | POST | AI 插画 | PNG | **是** |

---

## 1. `/render/pdf` 和 `/render/docx`（共用 JSON）

### 顶层字段

| 字段 | 类型 | 必需 | 说明 | 默认 |
|---|---|:---:|---|---|
| `title` | string | ✓ | 主标题 | — |
| `title_en` | string | | 英文副标题 | — |
| `author` | string | | 作者 / 单位 | — |
| `date` | string | | 日期（推荐 `YYYY-MM-DD`） | 当天 |
| `theme` | enum | | `cicc` / `ms` / `cms` / `dachen` | `cicc` |
| `toc` | bool | | 目录开关 | `true` |
| `charts` | array | | 图表预定义，见 § 1.1 | `[]` |
| `illustrations` | array | | AI 配图预定义，见 § 1.2 | `[]` |
| `sections` | array | ✓ | 主体内容，见 § 1.3 | — |
| `disclaimer` | string | | 免责声明 | — |

### 1.1 `charts` 数组项

```json
{
  "id": "c1",
  "type": "bar",
  "data": {
    "title": "Q1-Q3 营收",
    "categories": ["Q1", "Q2", "Q3"],
    "series": [
      {"name": "收入", "values": [100, 120, 150]},
      {"name": "利润", "values": [20, 28, 35]}
    ]
  }
}
```

`type` 支持：
```
bar  line  area  pie  waterfall  scatter  heatmap
radar  funnel  gauge  treemap  candlestick  combo
```

`combo` 需要 `series[].chart_type` 字段（例：`"chart_type": "bar"` 或 `"line"`）。

`candlestick` 的 `values` 每项是 `[open, high, low, close]` 四元组。

### 1.2 `illustrations` 数组项

```json
{
  "id": "img1",
  "content": "多智能体协作架构图",
  "style": "vector-illustration",
  "title": "Architecture"
}
```

`style` 支持：`gradient-glass` / `vector-illustration` / `ticket`

需要容器启动时传入 `GEMINI_API_KEY`。

### 1.3 `sections` 数组项（section type 表）

| type | 必需字段 | 可选字段 | 用途 |
|---|---|---|---|
| `heading` | `title` | `content`, `children`, `level` | H1/H2/H3，`children` 实现嵌套 |
| `paragraph` | `content` | `align` | 正文段落 |
| `quote` | `content` | `attribution` | 引用框 |
| `table` | `headers`, `rows` | `caption`, `highlight_col` | 数据表格 |
| `chart` | `chart_id`, `caption` | `width_pct` | 嵌入 § 1.1 中定义的图表 |
| `ai-image` | `image_id`, `caption` | `width_pct` | 嵌入 § 1.2 中定义的 AI 图 |
| `kpi` | `metrics` | `columns` | KPI 卡片组（见 § 1.4） |
| `pagebreak` | — | — | 强制分页 |
| `callout` | `content` | `kind` (`info`/`warn`/`success`) | 侧栏提示框 |

### 1.4 `kpi` 的 `metrics`

```json
{
  "type": "kpi",
  "columns": 4,
  "metrics": [
    {"label": "目标价", "value": "¥200", "change": "+15%", "direction": "up"},
    {"label": "P/E", "value": "18.5x", "change": "-2.1", "direction": "down"},
    {"label": "ROE", "value": "35%", "change": null},
    {"label": "评级", "value": "买入", "change": null}
  ]
}
```

`direction`: `up` / `down` / `flat`，影响箭头和颜色。省略时按 `change` 符号推断。

### 完整示例

```bash
cat > /tmp/report.json << 'EOF'
{
  "title": "特斯拉公司深度报告",
  "title_en": "Tesla Inc. Deep Dive",
  "author": "投研一部",
  "date": "2026-04-22",
  "theme": "cicc",
  "toc": true,
  "charts": [
    {"id": "c_rev", "type": "line",
     "data": {"title": "营收趋势（亿美元）",
              "categories": ["2022","2023","2024","2025"],
              "series": [{"name": "营收", "values": [814, 967, 1082, 1230]}]}}
  ],
  "sections": [
    {"type": "heading", "title": "核心观点",
     "children": [
       {"type": "quote", "content": "自动驾驶 L4 落地将在 2027 年成为业绩拐点"},
       {"type": "kpi", "columns": 4, "metrics": [
         {"label": "目标价", "value": "$380", "change": "+18%"},
         {"label": "评级", "value": "买入"},
         {"label": "P/E", "value": "62x", "change": "-5x"},
         {"label": "FCF", "value": "$8.4B", "change": "+22%"}
       ]}
     ]},
    {"type": "heading", "title": "业绩回顾",
     "content": "2025 年营收同比增长 13.7%，主要来自能源和服务业务。",
     "children": [
       {"type": "chart", "chart_id": "c_rev", "caption": "图1：2022-2025 年营收"}
     ]},
    {"type": "pagebreak"},
    {"type": "heading", "title": "风险提示",
     "content": "1. 中国市场竞争加剧\n2. 美国市场需求放缓\n3. FSD 监管不确定"}
  ],
  "disclaimer": "本报告仅供参考，不构成投资建议。"
}
EOF

curl -s -X POST http://localhost:9091/render/pdf \
  -H "Content-Type: application/json" -d @/tmp/report.json \
  -o /tmp/tesla_report.pdf
```

---

## 2. `/render/pptx`（手工 PPT）

### 最小示例

```bash
curl -s -X POST http://localhost:9091/render/pptx \
  -H "Content-Type: application/json" \
  -d '{
    "theme": "goldman",
    "title": "Q1 业绩发布",
    "slides": [
      {"layout": "cover", "title": "Q1 Results", "subtitle": "2026-04"},
      {"layout": "kpi-4", "title": "关键指标",
       "kpis": [
         {"label": "营收", "value": "$12.3B", "change": "+14%"},
         {"label": "毛利率", "value": "42%", "change": "+1.2pp"},
         {"label": "运营利润", "value": "$3.1B", "change": "+22%"},
         {"label": "员工", "value": "52,000", "change": "+3%"}
       ]},
      {"layout": "content", "title": "业务分部",
       "bullets": ["核心业务 +15%", "新兴业务 +48%", "成本 +8%"]},
      {"layout": "chart", "title": "营收趋势",
       "chart": {"type": "bar", "data": {...}}}
    ]
  }' -o /tmp/deck.pptx
```

### slide layout 列表

| layout | 用途 |
|---|---|
| `cover` | 封面（标题 + 副标题 + 日期） |
| `section` | 章节分隔页 |
| `content` | 标题 + 5 点以内 bullets |
| `content-2col` | 两栏正文 |
| `kpi-2` / `kpi-3` / `kpi-4` / `kpi-6` | KPI 卡组 |
| `chart` | 大图表 |
| `chart-text` | 图表 + 右侧要点 |
| `table` | 数据表 |
| `quote` | 全屏引用 |
| `comparison` | 左右对比 |
| `timeline` | 时间线（3-6 节点） |
| `image` | 全幅图 |
| `end` | 结尾页 |

完整 20 种 layout 查：`curl http://localhost:9091/capabilities`

### PPT 主题

| theme | 风格 |
|---|---|
| `goldman` | 高盛深蓝白 |
| `cicc` | 中金深蓝红线 |
| `ms` | 摩根 Blue Paper |
| `apple-keynote` | 留白 + 超大字 |
| `techy-dark` | 深色 + 霓虹 |

---

## 3. `/render/chart`（单图表）

```bash
curl -s -X POST http://localhost:9091/render/chart \
  -H "Content-Type: application/json" \
  -d '{
    "type": "bar",
    "theme": "cicc",
    "width": 800,
    "height": 500,
    "data": {
      "title": "市场份额",
      "categories": ["特斯拉", "比亚迪", "大众", "丰田"],
      "series": [{"name": "份额", "values": [28, 22, 15, 18]}]
    }
  }' -o /tmp/chart.png
```

输出 PNG，默认 800×500，支持 `width` / `height` 参数。

---

## 4. `/render/pptx-ai`（AI 生成完整 PPT）

需要 `GEMINI_API_KEY`。

```bash
curl -s -X POST http://localhost:9091/render/pptx-ai \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "2026 AI 行业趋势",
    "style": "gradient-glass",
    "slide_count": 8,
    "language": "zh",
    "outline": [
      "现状：三大模型阵营",
      "技术：Agent / 多模态 / 推理",
      "市场：B 端 vs C 端分化",
      "投资：二级市场估值变化",
      "风险：监管、算力、人才",
      "建议：关注中上游"
    ]
  }' -o /tmp/ai_deck.zip

unzip -l /tmp/ai_deck.zip
# deck.pptx + images/slide_*.png（配图）
```

输入参数：

| 字段 | 类型 | 必需 | 说明 |
|---|---|:---:|---|
| `topic` | string | ✓ | 主题 |
| `style` | enum | | `gradient-glass` / `vector-illustration` / `ticket` |
| `slide_count` | int | | 目标页数，默认 8 |
| `language` | `zh`/`en` | | 语言，默认 `zh` |
| `outline` | array | | 大纲（推荐给），不给会全 AI 生成 |

---

## 5. `/render/illustrate`（AI 配图）

需要 `GEMINI_API_KEY`。

```bash
curl -s -X POST http://localhost:9091/render/illustrate \
  -H "Content-Type: application/json" \
  -d '{
    "content": "多智能体系统架构：协调器 + 三个专家 Agent + 共享记忆",
    "style": "vector-illustration",
    "title": "Multi-Agent Architecture",
    "width": 1200,
    "height": 800
  }' -o /tmp/illust.png
```

`style`:

| style | 观感 |
|---|---|
| `gradient-glass` | 3D 玻璃 + 霓虹渐变，科技感，适合封面 |
| `vector-illustration` | 扁平矢量 + 复古配色，适合 AI/科技类 |
| `ticket` | 黑白对比 + 网格 + 票券极简，适合年报封面 |

---

## 6. `/styles` 和 `/capabilities`

```bash
# 所有可用主题
curl -s http://localhost:9091/styles | python3 -m json.tool

# 全量能力（包含每个端点的字段、默认值、校验规则）
curl -s http://localhost:9091/capabilities | python3 -m json.tool
```

---

## 7. 常见错误响应

| HTTP | 含义 | 常见原因 |
|---|---|---|
| 400 | JSON schema 错 | 缺必需字段 / `sections` 为空 / `chart_id` 在 `charts` 里找不到 |
| 413 | 请求体太大 | 单次请求 >10MB，拆分或压缩 |
| 500 | AI 功能失败 | `GEMINI_API_KEY` 没传 / Gemini API 超时 |
| 502 | 上游挂 | Gemini / Plotly renderer 崩 |
| 504 | 渲染超时 | 图表太多 / AI PPT 页数太大；拆分请求 |

---

## 8. 性能基线

| 任务 | 典型耗时 |
|---|---|
| PDF 5 页无图表 | 2-3s |
| PDF 10 页 + 5 图表 | 8-12s |
| DOCX 同上 | 4-6s |
| PPTX 10 页无 AI | 5-8s |
| AI PPT 8 页 | 40-90s |
| AI 配图单张 | 15-25s |
| 单图表 PNG | 1-2s |

超过 2× 基线 → 看 `docker logs typeset-engine --tail 100`。
