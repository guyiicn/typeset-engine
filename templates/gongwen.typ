// ═══════════════════════════════════════════════════════════════
// 党政公文模板 — GB/T 9704-2012《党政机关公文格式》
// 适用于：通知、决定、意见、函、纪要、报告等
//
// 字体规范（GB/T 9704）：
//   发文机关标志：方正小标宋（用 Noto Serif CJK SC Bold 替代）
//   正文：仿宋 三号（≈16pt）
//   一级标题：黑体 三号
//   二级标题：楷体 三号
//   三级标题：仿宋 三号 加粗
//   发文字号：仿宋 三号
// ═══════════════════════════════════════════════════════════════

// ── 字体定义 ────────────────────────────────────────────────
#let font-fangsong = ("FangSong", "FZFangSong-Z02", "cwTeXFangSong", "Noto Serif CJK SC")
#let font-heiti = ("SimHei", "cwTeXHeiBold", "Noto Sans CJK SC")
#let font-kaiti = ("cwTeXKai", "AR PL UKai CN", "Noto Serif CJK SC")
#let font-songti = ("cwTeXMing", "AR PL UMing CN", "Noto Serif CJK SC")
#let font-xiaobiaosong = ("FZXiaoBiaoSong-B05", "Noto Serif CJK SC")

// ── 颜色定义 ────────────────────────────────────────────────
#let gw-red = rgb("#e60012")        // 公文红（红头、五角星）
#let gw-black = rgb("#000000")      // 正文纯黑
#let gw-rule = rgb("#e60012")       // 分隔线红色

// ── 公文尺寸常量（GB/T 9704） ───────────────────────────────
// A4 纸张，上边距 37mm，下边距 35mm，左边距 28mm，右边距 26mm
// 版心宽度 156mm，行间距 28.95pt（三号字 28 磅行距）
#let gw-size-sanhao = 16pt          // 三号字 ≈ 16pt
#let gw-size-sihao = 14pt           // 四号字 ≈ 14pt
#let gw-size-xiaosihao = 12pt       // 小四号 ≈ 12pt
#let gw-leading = 28.95pt           // 行距 28.95 磅

// ── 页面设置 ────────────────────────────────────────────────
#let gongwen-page-setup() = {
  set page(
    paper: "a4",
    margin: (top: 37mm, bottom: 35mm, left: 28mm, right: 26mm),
    header: none,
    footer: context {
      set text(size: gw-size-sihao, font: font-fangsong)
      align(center)[～ #counter(page).display() ～]
    },
  )
}

// ── 文本基础 ────────────────────────────────────────────────
#let gongwen-text-setup() = {
  set text(
    font: font-fangsong,
    size: gw-size-sanhao,
    lang: "zh",
    region: "cn",
    fill: gw-black,
    cjk-latin-spacing: none,
  )
  set par(
    justify: true,
    leading: 0.8em,
    first-line-indent: 2em,
  )
}

// ── 红头（发文机关标志）─────────────────────────────────────
// 居中排列，红色字，字号由份数决定（通常在22-36pt之间）
#let redhead(
  organ: "XX机关",
  doc-type: "文件",
  font-size: 30pt,
) = {
  block(spacing: 0pt)[
    #align(center)[
      #set par(first-line-indent: 0em, spacing: 0pt)
      #text(
        size: font-size,
        font: font-xiaobiaosong,
        fill: gw-red,
        weight: "bold",
      )[#organ]
    ]
  ]
  if doc-type != "" {
    v(1mm)
    block(spacing: 0pt)[
      #align(center)[
        #set par(first-line-indent: 0em, spacing: 0pt)
        #text(
          size: font-size * 0.7,
          font: font-xiaobiaosong,
          fill: gw-red,
          weight: "bold",
          tracking: 4pt,
        )[#doc-type]
      ]
    ]
  }
  v(2mm)
  line(length: 100%, stroke: 2pt + gw-rule)
  v(12mm)
}

// ── 发文字号 + 签发人 ───────────────────────────────────────
// 发文字号：发文机关代字〔年份〕序号，居中或左空一字
#let doc-number(
  number: "",           // 如 "国发〔2026〕1号"
  urgency: "",          // 紧急程度：特急、加急
  secret-level: "",     // 密级：机密、秘密
  signer: "",           // 签发人
) = {
  if number != "" or signer != "" {
    set par(first-line-indent: 0em)
    if signer != "" {
      // 上行文格式：左边发文字号，右边签发人
      grid(
        columns: (1fr, 1fr),
        align(left)[
          #text(size: gw-size-sanhao, font: font-fangsong)[#number]
        ],
        align(right)[
          #text(size: gw-size-sanhao, font: font-fangsong)[签发人：#signer]
        ],
      )
    } else {
      // 下行文格式：居中
      align(center)[
        #text(size: gw-size-sanhao, font: font-fangsong)[#number]
      ]
    }
    v(4mm)
    // 红色分隔线
    line(length: 100%, stroke: 1pt + gw-rule)
    v(4mm)
  }
}

// ── 公文标题 ────────────────────────────────────────────────
// 红线下方空二行，标题用二号方正小标宋
#let gw-title(title: "") = {
  v(2mm)
  block(spacing: 0pt)[
    #align(center)[
      #set par(first-line-indent: 0em, spacing: 0pt)
      #text(
        size: 22pt,   // 二号字
        font: font-xiaobiaosong,
        weight: "bold",
        fill: gw-black,
        cjk-latin-spacing: none,
      )[#title]
    ]
  ]
  v(6mm)
}

// ── 主送机关 ────────────────────────────────────────────────
#let gw-recipient(to: "") = {
  if to != "" {
    set par(first-line-indent: 0em)
    text(size: gw-size-sanhao, font: font-fangsong, cjk-latin-spacing: none)[#to：]
  }
}

// ── 附件列表 ────────────────────────────────────────────────
// 格式："附　件：1. 附件名称" （附和件之间全角空格）
#let gw-attachments(items: ()) = {
  if items.len() > 0 {
    v(4mm)
    set par(first-line-indent: 0em)
    if items.len() == 1 {
      text(size: gw-size-sanhao, font: font-fangsong)[附#h(1em)件：#items.at(0)]
    } else {
      text(size: gw-size-sanhao, font: font-fangsong)[附#h(1em)件：]
      let idx = 0
      while idx < items.len() {
        v(1mm)
        text(size: gw-size-sanhao, font: font-fangsong)[#h(4em)#{ idx + 1 }.#items.at(idx)]
        idx = idx + 1
      }
    }
    v(4mm)
  }
}

// ── 落款（发文机关署名 + 日期）──────────────────────────────
#let gw-signature(
  organ: "",
  date: "",
) = {
  v(8mm)
  set par(first-line-indent: 0em)
  align(right)[
    #pad(right: 2em)[
      #text(size: gw-size-sanhao, font: font-fangsong)[#organ]
      #v(4mm)
      #text(size: gw-size-sanhao, font: font-fangsong)[#date]
    ]
  ]
}

// ── 附注/抄送 ───────────────────────────────────────────────
#let gw-footer-info(
  cc: "",               // 抄送：XX，XX
  printer: "",          // 印发：XX办公室
  print-date: "",       // 印发日期
  copies: "",           // 印发份数
) = {
  v(10mm)
  line(length: 100%, stroke: 0.5pt + gw-black)
  set text(size: gw-size-sihao, font: font-fangsong)
  set par(first-line-indent: 0em)
  if cc != "" {
    v(2mm)
    [抄送：#cc。]
  }
  if printer != "" or print-date != "" {
    v(1mm)
    line(length: 100%, stroke: 0.5pt + gw-black)
    v(1mm)
    grid(
      columns: (1fr, 1fr),
      align(left)[#printer],
      align(right)[#print-date #if copies != "" [（共印#{ copies }份）]],
    )
  }
}

// ── 标题样式 ────────────────────────────────────────────────
// 一级标题：黑体 三号（一、二、三……）
// 二级标题：楷体 三号（（一）（二）（三）……）
// 三级标题：仿宋加粗 三号（1. 2. 3.……）
#let gongwen-heading-setup() = {
  set heading(numbering: none)

  show heading.where(level: 1): it => {
    set text(size: gw-size-sanhao, font: font-heiti, weight: "bold", fill: gw-black)
    set par(first-line-indent: 0em)
    v(0.5em)
    block(it.body)
    v(0.3em)
  }

  show heading.where(level: 2): it => {
    set text(size: gw-size-sanhao, font: font-kaiti, weight: "regular", fill: gw-black)
    set par(first-line-indent: 0em)
    v(0.3em)
    block(it.body)
    v(0.2em)
  }

  show heading.where(level: 3): it => {
    set text(size: gw-size-sanhao, font: font-fangsong, weight: "bold", fill: gw-black)
    set par(first-line-indent: 0em)
    v(0.2em)
    block(it.body)
    v(0.1em)
  }
}

// ═══════════════════════════════════════════════════════════════
// 公文主函数 — 组合所有元素
// ═══════════════════════════════════════════════════════════════
#let gongwen(
  // 红头区
  organ: "XX机关",
  doc-type: "文件",
  redhead-size: 30pt,
  // 发文字号区
  number: "",
  urgency: "",
  secret-level: "",
  signer: "",
  // 标题区
  title: "",
  // 主送机关
  recipient: "",
  // 落款
  signature-organ: "",
  signature-date: "",
  // 附件
  attachments: (),
  // 附注
  cc: "",
  printer: "",
  print-date: "",
  copies: "",
  // 正文
  body,
) = {
  // 应用页面和文本设置
  gongwen-page-setup()
  gongwen-text-setup()
  gongwen-heading-setup()

  set document(title: title, author: organ)

  // ── 正文 ──
  // 红头
  redhead(organ: organ, doc-type: doc-type, font-size: redhead-size)

  // 发文字号
  doc-number(
    number: number,
    urgency: urgency,
    secret-level: secret-level,
    signer: signer,
  )

  // 公文标题
  gw-title(title: title)

  // 主送机关
  gw-recipient(to: recipient)

  // 正文（重置缩进，确保段落首行缩进 2 字符）
  set par(first-line-indent: 2em, justify: true, leading: 0.9em)
  set text(size: gw-size-sanhao, font: font-fangsong, fill: gw-black, cjk-latin-spacing: none)
  body

  // 附件
  gw-attachments(items: attachments)

  // 落款
  if signature-organ != "" or signature-date != "" {
    gw-signature(organ: signature-organ, date: signature-date)
  }

  // 抄送/印发信息
  if cc != "" or printer != "" {
    gw-footer-info(
      cc: cc,
      printer: printer,
      print-date: print-date,
      copies: copies,
    )
  }
}
