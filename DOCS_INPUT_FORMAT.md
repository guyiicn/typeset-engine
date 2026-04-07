# typeset-engine DOCX 输入规范

## 快速检查

渲染前运行：
```bash
python scripts/validate_docx.py --data input.json
```

## 顶层字段

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `title` | string | ✅ | 报告标题 |
| `title_en` | string | ❌ | 英文副标题 |
| `author` | string | ❌ | 作者 |
| `date` | string | ❌ | 日期 |
| `version` | string | ❌ | 版本 |
| `toc` | boolean | ❌ | 是否生成目录（默认 True） |
| `disclaimer` | string | ❌ | 免责声明 |
| `sections` | array | ✅ | 章节列表 |

## Section 类型

### `heading`
```json
{
  "type": "heading",
  "title": "标题文本",
  "content": "可选正文内容",
  "children": []   // 可嵌套子章节
}
```

### `paragraph`
```json
{
  "type": "paragraph",
  "content": "正文内容，支持\\n\\n分段"
}
```

**换行规范：**
- `\n\n` → 分段（多段落）
- `\n`   → 段内换行（左对齐，不会被 JUSTIFY 错排）
- 列表项：以 `• ` 开头，自动加悬挂缩进

**⚠️ 避免：**
- 不要在 `\n` 之后单独放一行纯数字或纯百分比（会导致格式碎片化）
- 不要在字符串里写未转义的 `"`，用 `「」` 代替

### `quote`
```json
{
  "type": "quote",
  "content": "引用内容（左侧红色边框 + 浅红背景）"
}
```

### `table`
```json
{
  "type": "table",
  "headers": ["列1", "列2"],
  "rows": [
    ["数据1", "数据2"],
    ["数据3", "数据4"]
  ]
}
```

**⚠️ 规范：**
- `headers` 和 `rows` 每行列数必须一致
- 空单元格填 `—`，不要留空字符串
- 避免在单元格内换行（`\n`），会影响居中对齐
- 数字不要带 `$` 符号（触发数学模式），用 `0.30 USD` 代替

### `chart`
```json
{
  "type": "chart",
  "chart_id": "my_chart",
  "caption": "图表说明"
}
```
需要同目录有 `my_chart.png`。

### `pagebreak`
```json
{ "type": "pagebreak" }
```

### `kpi`
```json
{
  "type": "kpi",
  "metrics": [
    { "label": "指标名", "value": "123", "change": "+10%" }
  ]
}
```

## 字体规则（已内置，无需指定）

渲染器内置以下字体规则，**无需在 JSON 中指定**：

| 内容类型 | 西文 | 中文 |
|---------|------|------|
| 正文 | DejaVu Sans | Noto Serif CJK SC |
| 标题 | DejaVu Sans | Noto Serif CJK SC |
| 表头 | DejaVu Sans | Noto Serif CJK SC |
| 代码/数字 | DejaVu Sans Mono | — |

## 排版规则（已内置）

| 规则 | 说明 |
|------|------|
| 表格数据列 | **左对齐**，非居中 |
| 正文段落 | **左对齐**，非 JUSTIFY |
| 列表项 | 悬挂缩进（bullet 左对齐，首行负缩进） |
| 换行 `\n` | 段内普通换行，不触发 JUSTIFY |

## 常见错误

### 1. 表格列错位
```json
{ "cell": "0.30 USD" }   // ✅
{ "cell": "$0.30" }       // ❌ $ 触发数学模式
```

### 2. 空单元格
```json
{ "cell": "—" }           // ✅
{ "cell": "" }             // ❌ 空字符串
```

### 3. 孤立数字行
```json
// ❌ 不好：孤立百分比
"• 较2024年增长\n363%"

// ✅ 好：合并到一行
"• 较2024年增长363%"
```

### 4. 未转义的引号
```json
// ❌ 不好
"内容含「"内部引号"」"

// ✅ 好
"内容含「内部引号」"
```

## 主题列表

| 主题 | 说明 |
|------|------|
| `cicc` | 中金风格（深蓝+红色，衬线风） |
| `ms` | 摩根斯坦利风格（蓝色，Sans-serif） |
| `cms` | 招商证券风格（红色，衬线） |
| `dachen` | 达晨创投风格（达晨红） |
