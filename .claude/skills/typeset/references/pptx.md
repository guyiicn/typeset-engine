# pptx reference

`/render/pptx` 用 python-pptx 渲染**可编辑** PowerPoint。

## Theme（root JSON 中的 `theme` 字段，不是 query param）

`default` / `cicc` / `goldman` / `morgan` / `dark` / `minimal`

---

## 顶层 JSON

```json
{
  "title": "演示标题",
  "subtitle": "副标题（可选）",
  "theme": "goldman",
  "slides": [
    {"layout": "title", ...},
    {"layout": "content", ...}
  ]
}
```

---

## Layout（20 种）

### 通用 12 种

| layout | 关键字段 |
|---|---|
| `title` | `title`, `subtitle?` |
| `section` | `title` |
| `content` | `title`, `bullets: [str, ...]`, `image?` |
| `two_column` | `title`, `left: [str,...]`, `right: [str,...]` |
| `table` | `title`, `headers`, `rows` |
| `summary` | `title`, `bullets` |
| `kpi` | `title`, `kpis: [{label, value, change?}]` |
| `chart` | `title`, `chart_type`, `data` |
| `comparison` | `title`, `left_title`, `left`, `right_title`, `right` |
| `timeline` | `title`, `milestones: [{date, label}]` |
| `quote` | `quote`, `author?` |
| `end` | `title?` |

### 投行 Pitch Book 8 种

| layout | 关键字段 | 说明 |
|---|---|---|
| `comparable_companies` | `headers`, `rows`, `summary_rows: [{label, values}]`, `source?` | 可比公司分析（10-15 列宽表 + Median/Mean） |
| `football_field` | `ranges: [{method, low, high}]`, `current_price`, `currency` | 估值区间图 |
| `sources_uses` | `sources: [{item, amount}]`, `uses: [{item, amount}]`, `currency` | 资金来源/用途 |
| `sensitivity_matrix` | `row_label`, `col_label`, `row_values`, `col_values`, `matrix`, `base_case: [r, c]` | WACC×TGR 二维矩阵 |
| `transaction_overview` | `bullets`, `terms: [{key, value}]` | 交易概览 |
| `disclaimer` | `text` | 免责声明小字 |
| `waterfall` | `categories`, `values` | 瀑布图/桥接 |
| `org_chart` | `nodes: [{id, label, parent?}]` | 3 层组织架构 |

---

## 完整示例（投行 PPTX）

```json
{
  "title": "Project Alpha",
  "subtitle": "Strictly Confidential",
  "theme": "goldman",
  "slides": [
    {"layout": "title", "title": "Project Alpha", "subtitle": "Q2 Pitch"},
    {
      "layout": "comparable_companies",
      "title": "Comparable Companies Analysis",
      "headers": ["Company", "Mkt Cap", "EV/EBITDA", "P/E"],
      "rows": [
        ["Co A", "$85bn", "11.2x", "18.5x"],
        ["Co B", "$42bn", "9.8x", "15.1x"]
      ],
      "summary_rows": [
        {"label": "Median", "values": ["$55bn", "10.3x", "16.2x"]}
      ],
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
    }
  ]
}
```

---

## 调用

```bash
bash ~/.claude/skills/typeset/scripts/render.sh \
  /render/pptx /tmp/typeset-output/payload.json \
  /tmp/typeset-output/deck.pptx
```

PPTX endpoint **没有 query param**，theme 写在 root JSON 里。

权威字段定义：`<typeset-engine repo>/scripts/render_pptx.py`
