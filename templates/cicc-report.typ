// ═══════════════════════════════════════════════════════════════
// CICC-Style (中金风格) Research Report — Typst Template
// Reusable base template for consulting-grade PDF reports
// ═══════════════════════════════════════════════════════════════

// ── PARAMETERS (override when #import-ing) ──────────────────
#let report-title-zh = "报告标题"
#let report-title-en = "Report Title"
#let report-author = "DeerFlow Research"
#let report-date = datetime.today()
#let report-version = ""
#let accent-color = rgb("#c41e3a")   // CICC red
#let heading-color = rgb("#1a1a2e")  // Dark navy

// ── PAGE SETUP ──────────────────────────────────────────────
#set document(title: report-title-zh, author: report-author)

#set page(
  paper: "a4",
  margin: (top: 2.5cm, bottom: 2.5cm, left: 2.2cm, right: 2.2cm),
  header: context {
    if counter(page).get().first() > 1 {
      set text(size: 8pt, fill: rgb("#666666"))
      grid(
        columns: (1fr, 1fr),
        align(left)[#report-title-zh],
        align(right)[#report-author · #report-date.display("[year]")],
      )
      line(length: 100%, stroke: 0.5pt + rgb("#cccccc"))
    }
  },
  footer: context {
    set text(size: 8pt, fill: rgb("#888888"))
    align(center)[— #counter(page).display() —]
  },
)

// ── TYPOGRAPHY ──────────────────────────────────────────────
#set text(
  font: ("Noto Serif CJK SC", "Noto Sans CJK SC", "FZFangSong-Z02", "DejaVu Serif"),
  size: 10.5pt,
  lang: "zh",
  region: "cn",
)

#set par(
  justify: true,
  leading: 0.85em,
  first-line-indent: 2em,
)

// ── HEADING STYLES ──────────────────────────────────────────
#set heading(numbering: none)

#show heading.where(level: 1): it => {
  set text(size: 18pt, weight: "bold", fill: heading-color)
  set par(first-line-indent: 0em)
  v(0.8em)
  block(it.body)
  v(0.3em)
  line(length: 100%, stroke: 2pt + accent-color)
  v(0.5em)
}

#show heading.where(level: 2): it => {
  set text(size: 14pt, weight: "bold", fill: heading-color)
  set par(first-line-indent: 0em)
  v(0.6em)
  block(it.body)
  v(0.2em)
  line(length: 60%, stroke: 1pt + accent-color)
  v(0.3em)
}

#show heading.where(level: 3): it => {
  set text(size: 12pt, weight: "bold", fill: rgb("#2d3436"))
  set par(first-line-indent: 0em)
  v(0.4em)
  block(it.body)
  v(0.2em)
}

// ── TABLE STYLES ────────────────────────────────────────────
#set table(
  stroke: 0.5pt + rgb("#cccccc"),
  inset: 8pt,
)
#show table.cell.where(y: 0): set text(weight: "bold", fill: white, size: 9.5pt)
#show table.cell: set text(size: 9.5pt)

// ── BLOCKQUOTE STYLES ───────────────────────────────────────
#show quote: it => {
  set par(first-line-indent: 0em)
  block(
    width: 100%,
    inset: (left: 16pt, top: 10pt, bottom: 10pt, right: 12pt),
    stroke: (left: 3pt + accent-color),
    fill: rgb("#fdf2f2"),
    text(style: "italic", weight: "bold", size: 10pt, it.body),
  )
}

// ── COVER PAGE FUNCTION ─────────────────────────────────────
#let cover-page(title-zh: "", title-en: "", author: "", date: "", version: "") = {
  page(
    header: none,
    footer: none,
    margin: (top: 0cm, bottom: 0cm, left: 0cm, right: 0cm),
  )[
    #block(width: 100%, height: 100%, fill: heading-color)[
      #v(6cm)
      #align(center)[
        #block(width: 80%)[
          #line(length: 100%, stroke: 2pt + accent-color)
          #v(1.5cm)
          #text(size: 32pt, weight: "bold", fill: white, tracking: 2pt)[
            #title-zh
          ]
          #v(1.5cm)
          #line(length: 100%, stroke: 2pt + accent-color)
          #v(1.2cm)
          #text(size: 14pt, fill: rgb("#aaaaaa"), weight: "regular")[
            #title-en
          ]
          #v(2cm)
          #text(size: 12pt, fill: rgb("#cccccc"))[#author]
          #v(0.5cm)
          #text(size: 11pt, fill: rgb("#888888"))[
            #date #if version != "" [· #version]
          ]
        ]
      ]
    ]
  ]
}

// ── TOC PAGE FUNCTION ───────────────────────────────────────
#let toc-page() = {
  page(header: none)[
    #v(2cm)
    #align(center)[
      #text(size: 20pt, weight: "bold", fill: heading-color)[目 录]
    ]
    #v(1cm)
    #outline(title: none, indent: 1.5em, depth: 3)
  ]
}
