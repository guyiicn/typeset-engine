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

// ── Theme: 公文 Gongwen (GB/T 9704-2012) ───────────────────
#let theme-gongwen = (
  name: "gongwen",
  label: "党政公文 GB/T 9704",
  primary: rgb("#e60012"),          // 公文红
  accent: rgb("#e60012"),           // 红头/分隔线
  text-primary: rgb("#000000"),     // 纯黑
  text-body: rgb("#000000"),        // 纯黑
  text-secondary: rgb("#333333"),
  table-header-bg: rgb("#000000"),
  table-header-fg: white,
  table-alt-row: rgb("#f5f5f5"),
  quote-border: rgb("#000000"),
  quote-bg: rgb("#f5f5f5"),
  cover-bg: white,
  cover-fg: rgb("#000000"),
  heading-rule-full: false,         // 公文无装饰线
  heading-rule-partial: 0,
  table-style: "full-border",
  serif-body: true,                 // 仿宋正文
)

// ── Theme: 电广传媒 TBS (TV & Broadcast) ────────────────────
#let theme-tbs = (
  name: "tbs",
  label: "电广传媒 TBS",
  primary: rgb("#e60012"),          // 公文红
  accent: rgb("#e60012"),
  text-primary: rgb("#000000"),
  text-body: rgb("#000000"),
  text-secondary: rgb("#333333"),
  table-header-bg: rgb("#000000"),
  table-header-fg: white,
  table-alt-row: rgb("#f5f5f5"),
  quote-border: rgb("#000000"),
  quote-bg: rgb("#f5f5f5"),
  cover-bg: white,
  cover-fg: rgb("#000000"),
  heading-rule-full: false,
  heading-rule-partial: 0,
  table-style: "full-border",
  serif-body: true,
)

// ── Theme: Goldman Sachs ────────────────────────────────────
// 极简蓝白专业风，仅水平线表格，Sans-serif 正文
#let theme-goldman = (
  name: "goldman",
  label: "Goldman Sachs",
  primary: rgb("#003A70"),          // GS 深蓝
  accent: rgb("#6CACE4"),           // GS 浅蓝
  text-primary: rgb("#003A70"),     // 标题深蓝
  text-body: rgb("#333333"),        // 正文深灰
  text-secondary: rgb("#7F8C8D"),   // 辅助灰
  table-header-bg: rgb("#003A70"),
  table-header-fg: white,
  table-alt-row: rgb("#F0F4F8"),    // 极浅蓝灰交替行
  quote-border: rgb("#6CACE4"),
  quote-bg: rgb("#EBF5FB"),
  cover-bg: rgb("#003A70"),         // 深蓝封面
  cover-fg: white,
  heading-rule-full: true,
  heading-rule-partial: 0.3,        // H2 短线（简约）
  table-style: "horizontal-only",   // GS 标志性：仅水平线
  serif-body: false,                // Sans-serif 正文
)

// ── Theme: UBS ─────────────────────────────────────────────
// 红黑撞色，白底封面+红色装饰条，衬线正文
#let theme-ubs = (
  name: "ubs",
  label: "UBS",
  primary: rgb("#E60000"),          // UBS 红
  accent: rgb("#333333"),           // 黑色辅助
  text-primary: rgb("#333333"),     // 标题黑色
  text-body: rgb("#333333"),        // 正文色
  text-secondary: rgb("#666666"),
  table-header-bg: rgb("#E60000"),  // 红色表头
  table-header-fg: white,
  table-alt-row: rgb("#FDF2F2"),    // 浅粉交替行
  quote-border: rgb("#E60000"),
  quote-bg: rgb("#FDF2F2"),
  cover-bg: white,                  // 白底 + 红色装饰带
  cover-fg: rgb("#333333"),
  heading-rule-full: true,
  heading-rule-partial: 0.5,
  table-style: "full-border",
  serif-body: true,                 // 衬线正文
)

// ── Theme: Whitepaper 技术白皮书 ────────────────────────────
// 无品牌色，蓝灰专业色调，适合技术白皮书/开源项目
#let theme-whitepaper = (
  name: "whitepaper",
  label: "Technical Whitepaper",
  primary: rgb("#2C3E50"),          // 深灰蓝
  accent: rgb("#3498DB"),           // 专业蓝
  text-primary: rgb("#2C3E50"),     // 标题深灰蓝
  text-body: rgb("#34495E"),        // 正文色
  text-secondary: rgb("#7F8C8D"),   // 辅助灰
  table-header-bg: rgb("#2C3E50"),
  table-header-fg: white,
  table-alt-row: rgb("#F8F9FA"),    // 极浅灰
  quote-border: rgb("#3498DB"),
  quote-bg: rgb("#EBF5FB"),
  cover-bg: rgb("#2C3E50"),         // 深灰蓝封面
  cover-fg: white,
  heading-rule-full: true,
  heading-rule-partial: 0.5,
  table-style: "horizontal-only",   // 简约水平线
  serif-body: false,                // Sans-serif 正文
)

// ── Theme: McKinsey 麦肯锡 ──────────────────────────────────
// 极简大留白，深蓝品牌色，Sans-serif 正文，无装饰线
#let theme-mckinsey = (
  name: "mckinsey",
  label: "McKinsey & Company",
  primary: rgb("#00205B"),
  accent: rgb("#009FDA"),
  text-primary: rgb("#00205B"),
  text-body: rgb("#333333"),
  text-secondary: rgb("#666666"),
  table-header-bg: rgb("#00205B"),
  table-header-fg: white,
  table-alt-row: rgb("#F0F4F8"),
  quote-border: rgb("#009FDA"),
  quote-bg: rgb("#E8F4FD"),
  cover-bg: rgb("#00205B"),
  cover-fg: white,
  heading-rule-full: false,
  heading-rule-partial: 0,
  table-style: "horizontal-only",
  serif-body: false,
)

// ── Theme: BCG 波士顿咨询 ──────────────────────────────────
// 绿色品牌色，现代专业，Sans-serif
#let theme-bcg = (
  name: "bcg",
  label: "Boston Consulting Group",
  primary: rgb("#00645A"),
  accent: rgb("#6CC24A"),
  text-primary: rgb("#2D2D2D"),
  text-body: rgb("#333333"),
  text-secondary: rgb("#666666"),
  table-header-bg: rgb("#00645A"),
  table-header-fg: white,
  table-alt-row: rgb("#F0F7F5"),
  quote-border: rgb("#00645A"),
  quote-bg: rgb("#E8F5E9"),
  cover-bg: rgb("#00645A"),
  cover-fg: white,
  heading-rule-full: true,
  heading-rule-partial: 0.4,
  table-style: "horizontal-only",
  serif-body: false,
)

// ── Theme: Bain 贝恩咨询 ───────────────────────────────────
// 红色品牌色，红黑配色，衬线正文
#let theme-bain = (
  name: "bain",
  label: "Bain & Company",
  primary: rgb("#CC0000"),
  accent: rgb("#D4A843"),
  text-primary: rgb("#333333"),
  text-body: rgb("#333333"),
  text-secondary: rgb("#666666"),
  table-header-bg: rgb("#CC0000"),
  table-header-fg: white,
  table-alt-row: rgb("#FDF5F5"),
  quote-border: rgb("#CC0000"),
  quote-bg: rgb("#FDF5F5"),
  cover-bg: rgb("#CC0000"),
  cover-fg: white,
  heading-rule-full: true,
  heading-rule-partial: 0.5,
  table-style: "full-border",
  serif-body: true,
)

// ── Theme Registry ──────────────────────────────────────────
#let themes = (
  cicc: theme-cicc,
  ms: theme-ms,
  cms: theme-cms,
  dachen: theme-dachen,
  gongwen: theme-gongwen,
  tbs: theme-tbs,
  goldman: theme-goldman,
  ubs: theme-ubs,
  whitepaper: theme-whitepaper,
  mckinsey: theme-mckinsey,
  bcg: theme-bcg,
  bain: theme-bain,
)

// ── Helper: Get theme by name ───────────────────────────────
#let get-theme(name) = {
  if name in themes { themes.at(name) }
  else { theme-cicc }  // fallback to CICC
}
