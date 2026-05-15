# pdf / docx reference

PDF (`/render/pdf`) 与 DOCX (`/render/docx`) **共用同一份 JSON schema**。区别只在 endpoint 与可用 theme。

## Theme（query param `?theme=...`）

### 金融投研（7 种）

| theme | 说明 |
|---|---|
| `cicc` | 中金（深蓝 + 红） |
| `ms` | Morgan Stanley（深蓝） |
| `cms` | 招商证券（红） |
| `dachen` | 达晨财智（暗红） |
| `goldman` | Goldman Sachs（深蓝 + 浅蓝） |
| `ubs` | UBS（红） |
| `whitepaper` | 通用技术白皮书（灰蓝 + 蓝） |

### 咨询 MBB（3 种）

| theme | 说明 |
|---|---|
| `mckinsey` | 麦肯锡（深蓝 + 浅蓝） |
| `bcg` | BCG（深绿 + 浅绿） |
| `bain` | Bain（红 + 金） |

### 公文（2 种）

| theme | 说明 |
|---|---|
| `gongwen` | GB/T 9704 党政公文 |
| `tbs` | 电广传媒预设企业公文 |

### 学术（3 种）

| theme | 说明 |
|---|---|
| `ieee` | IEEE 双栏论文 |
| `cn-paper` | 中文学术论文 |
| `working-paper` | SSRN 工作论文 |

> **DOCX 仅支持 `cicc` / `ms` / `cms` / `dachen` 四种**。其他 theme 选择时改用 PDF。

---

## 通用 JSON Schema

```json
{
  "title": "报告标题",
  "title_en": "English Title (可选)",
  "author": "作者",
  "date": "2026-05-15",
  "version": "v1.0",
  "toc": true,
  "charts": [
    {
      "id": "唯一id",
      "type": "bar",
      "data": {
        "title": "图表标题",
        "categories": ["A", "B", "C"],
        "series": [{"name": "系列1", "values": [1, 2, 3]}]
      }
    }
  ],
  "sections": [
    {"type": "heading", "title": "...", "children": [...]}
  ],
  "illustrations": [
    {"id": "img_id", "content": "配图描述文本", "style": "ticket", "title": "可选"}
  ],
  "disclaimer": "免责声明"
}
```

## section type

| type | 必需字段 | 说明 |
|---|---|---|
| `heading` | `title`, `children` | 章节，支持嵌套 H1→H2→H3 |
| `paragraph` | `content` | 正文 |
| `quote` | `content` | 引用框（彩色边框 + 背景） |
| `table` | `headers`, `rows` | 表格 |
| `chart` | `chart_id`, `caption?` | 嵌入图表（引用 root.charts[].id） |
| `kpi` | `metrics: [{label, value, change?}]` | KPI 卡片 |
| `ai-image` | `image_id`, `caption?` | AI 配图（需 GEMINI_API_KEY，引用 root.illustrations[].id） |
| `pagebreak` | — | 分页 |

chart type 选项见 `chart.md`。

---

## 公文专用（theme=gongwen / tbs）

```json
{
  "title": "关于XX的通知",
  "recipient": "各部门",
  "organ": "XX机关",
  "doc_type": "文件",
  "number": "XX发〔2026〕1号",
  "redhead_size": 30,
  "sections": [
    {"type": "paragraph", "content": "..."},
    {"type": "heading", "title": "一、XX", "children": [...]}
  ],
  "attachments": ["附件名"],
  "signature_organ": "XX机关",
  "signature_date": "2026年5月15日",
  "cc": "抄送单位",
  "printer": "印发单位",
  "print_date": "2026年5月15日印发"
}
```

`tbs` 主题自动预设 `organ=湖南电广传媒股份有限公司`，可省略。

## 学术专用（theme=ieee / cn-paper / working-paper）

```json
{
  "title": "Paper Title",
  "authors": [{"name": "Author Name", "organization": "University"}],
  "abstract": "摘要文本...",
  "keywords": ["AI", "NLP"],
  "sections": [
    {"type": "heading", "title": "Introduction", "children": [
      {"type": "paragraph", "content": "..."}
    ]}
  ]
}
```

---

## 调用

```bash
bash ~/.claude/skills/typeset/scripts/render.sh \
  /render/pdf /tmp/typeset-output/payload.json \
  /tmp/typeset-output/report.pdf "theme=cicc"

bash ~/.claude/skills/typeset/scripts/render.sh \
  /render/docx /tmp/typeset-output/payload.json \
  /tmp/typeset-output/report.docx "theme=cicc"
```

权威字段定义：`<typeset-engine repo>/scripts/render_pdf.py` · `render_docx.py`

---

## Gotcha：Typst 把 markup parser 也跑在 table cell 里

`/render/pdf` 用 Typst 编译。Typst 不只解析段落正文，**`table` 单元格内容也走同一套 markup parser**。下面这些字符在 cell 里有特殊语义，会触发 `unclosed delimiter` 等解析错误：

| 字符 | Typst 含义 |
|---|---|
| `*文本*` | 粗体 |
| `_文本_` | 斜体 |
| `[...]` | content block |
| `~` | 不可断空格 |
| `#xxx` | 函数调用 |
| `\` | 转义符 |
| `<label>` | label / 锚点 |

**症状**：HTTP 500，响应 body 里能看到 `error: unclosed delimiter ... ┌─ ... report.typ:NNN`。

**应对（优先级从高到低）**

1. **改写文本绕开**——最稳。例：`references/*.md` → `references/ 六个 .md`；glob/正则里的 `*` 换成中文描述。
2. **转义**：JSON 里写 `\\*` `\\_` `\\[`（必须双反斜杠，因为要穿过 JSON → Typst 两层解析）。

正文段落 (`paragraph` / `quote`) 同样受影响，但实践中表格列名（路径、glob、代码片段）才是高发区。**写完 JSON 前 grep 一遍 `[*_~#\\]` 心里有数。**
