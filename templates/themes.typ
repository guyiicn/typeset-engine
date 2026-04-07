// ═══════════════════════════════════════════════════════════════
// Multi-Theme Research Report Styles
// 支持：中金 CICC / 摩根斯坦利 MS / 招商证券 CMS / 达晨创投 Dachen
// ═══════════════════════════════════════════════════════════════

// ── Theme: 中金 CICC ────────────────────────────────────────
#let theme-cicc = (
  name: "cicc",
  label: "中金公司 CICC",
  primary: rgb("#1a1a2e"),       // 深蓝（标题/封面底色）
  accent: rgb("#c41e3a"),        // 中金红（装饰线/引用框）
  text-primary: rgb("#1a1a2e"),  // 正文标题色
  text-body: rgb("#333333"),     // 正文色
  text-secondary: rgb("#666666"),// 辅助文字
  table-header-bg: rgb("#1a1a2e"),
  table-header-fg: white,
  table-alt-row: rgb("#f5f5f5"),
  quote-border: rgb("#c41e3a"),
  quote-bg: rgb("#fdf2f2"),
  cover-bg: rgb("#1a1a2e"),
  cover-fg: white,
  heading-rule-full: true,       // H1 全宽线
  heading-rule-partial: 0.6,     // H2 60% 宽
  table-style: "full-border",    // 有边框
  serif-body: true,              // 正文用宋体/衬线
)

// ── Theme: 摩根斯坦利 Morgan Stanley ────────────────────────
#let theme-ms = (
  name: "ms",
  label: "Morgan Stanley",
  primary: rgb("#002D72"),       // MS 深蓝（标志性）
  accent: rgb("#0078C8"),        // 中蓝（图表/链接）
  text-primary: rgb("#002D72"),  // 标题深蓝
  text-body: rgb("#4D4D4D"),     // 正文深灰
  text-secondary: rgb("#808080"),// 辅助灰
  table-header-bg: rgb("#002D72"),
  table-header-fg: white,
  table-alt-row: rgb("#F2F2F2"),
  quote-border: rgb("#002D72"),
  quote-bg: rgb("#EBF0F7"),
  cover-bg: rgb("#002D72"),
  cover-fg: white,
  heading-rule-full: true,
  heading-rule-partial: 0.4,     // H2 短线
  table-style: "horizontal-only", // MS 标志性：仅水平线
  serif-body: false,              // Sans-serif 正文
)

// ── Theme: 招商证券 CMS ─────────────────────────────────────
#let theme-cms = (
  name: "cms",
  label: "招商证券 CMS",
  primary: rgb("#C1002A"),       // 招商红
  accent: rgb("#E60033"),        // 亮红高亮
  text-primary: rgb("#333333"),  // 标题深灰
  text-body: rgb("#333333"),     // 正文色
  text-secondary: rgb("#666666"),// 辅助文字
  table-header-bg: rgb("#A00020"),// 暗红表头
  table-header-fg: white,
  table-alt-row: rgb("#F2F2F2"),
  quote-border: rgb("#C1002A"),
  quote-bg: rgb("#FDF2F4"),
  cover-bg: white,               // 白底 + 红色装饰带
  cover-fg: rgb("#333333"),
  heading-rule-full: true,
  heading-rule-partial: 0.5,
  table-style: "full-border",
  serif-body: true,               // 宋体正文（券商传统）
)

// ── Theme: 达晨财智 Dachen (Fortune Capital) ────────────────
// Source: fortunevc.com CSS analysis + logo (#b8141d 暗红主色)
#let theme-dachen = (
  name: "dachen",
  label: "达晨财智 Fortune Capital",
  primary: rgb("#b8141d"),       // 达晨红（官网主色，出现73次）
  accent: rgb("#185db1"),        // 蓝色点缀（官网辅助色）
  text-primary: rgb("#333333"),  // 标题深灰
  text-body: rgb("#333333"),     // 正文色
  text-secondary: rgb("#666666"),
  table-header-bg: rgb("#b8141d"),// 红色表头
  table-header-fg: white,
  table-alt-row: rgb("#f6f3f4"),  // 浅粉灰交替行（官网实际色）
  quote-border: rgb("#b8141d"),
  quote-bg: rgb("#f6f3f4"),
  cover-bg: rgb("#b8141d"),       // 红色封面
  cover-fg: white,
  heading-rule-full: true,        // 有装饰线
  heading-rule-partial: 0.5,
  table-style: "full-border",     // 国资创投传统风
  serif-body: true,               // 宋体正文（国资风）
)

// ── Theme Registry ──────────────────────────────────────────
#let themes = (
  cicc: theme-cicc,
  ms: theme-ms,
  cms: theme-cms,
  dachen: theme-dachen,
)

// ── Helper: Get theme by name ───────────────────────────────
#let get-theme(name) = {
  if name in themes { themes.at(name) }
  else { theme-cicc }  // fallback to CICC
}
