# 创始人指南 PDF 渲染规范 (The Founder's Playbook)

## 文档概况
- **源文件**: `/tmp/founders-playbook-v3.pdf` (36 页, 8.5×11 英寸横版)
- **中文翻译**: `/tmp/founders-playbook-zh.txt` (76,079 字符)
- **布局数据**: `/tmp/pb-layout.json` (每页文本 span + drawing rect)
- **参考样本**: `/tmp/cn-bilingual.pdf` (33 页, 官方中英双语版)

## 页面尺寸
- **尺寸**: 8.5in × 11in (792pt × 612pt), 横版
- **页边距**: 无 (full-bleed)
- **CSS**: `@page { size: 8.5in 11in; margin: 0; }`

## 配色方案 (章节扉页背景色循环)
| 颜色 | 名称 | RGB |
|------|------|-----|
| #D36F53 | Coral | (0.851, 0.467, 0.341) |
| #5F9B89 | Teal | (0.384, 0.600, 0.529) |
| #8C77D1 | Purple | (0.510, 0.490, 0.741) |
| #BBD1C9 | Mint | (0.733, 0.820, 0.788) |
| #CAC9DB | Lavender | (0.792, 0.788, 0.859) |
| #EFD4C6 | Peach | (0.937, 0.831, 0.776) |
| #AFADA4 | Warm Gray | (0.686, 0.678, 0.643) |

## 字体规范

### 中文
- **正文字体**: `Source Han Serif CN` (思源宋体 CN Regular) — 9pt
- **标题字体**: `Source Han Serif CN` — 48pt (扉页) / 30pt (章节)
- **Sans 字体**: `Noto Sans CJK SC` — 11pt (Pill/页码) / 13pt (副标题)
- **中文字重**: `font-weight: 400` (Regular)
- **中文行高**: 12.9pt (9pt × 1.43 倍)
- **副标题行高**: 16pt (13pt × 1.23 倍)
- **扉页标题行高**: 52pt (48pt × 1.08 倍)

### 英文
- **Serif**: `AnthropicSerifVariable-T` — 9pt (正文) / 56pt (封面) / 30pt (标题)
- **Sans**: `AnthropicSansVariable-Te` — 11pt (Pill) / 7pt (页码)
- **字重**: Regular (4)

### 字体回退链 (CSS)
```css
font-family: 'Source Han Serif CN', 'Noto Serif CJK SC', Georgia, serif;
```

## 页面模板

### 封面 (Cover)
- **背景**: Coral (#D36F53) 全幅
- **标题**: "创始人指南" / "打造原生 AI 初创企业"
  - 位置: left=54pt, top=110pt / top=172pt
  - 字体: Source Han Serif CN, 56pt, 行高 62pt
- **Logo**: Claude 太阳花 SVG (白色, 40pt×40pt, 左下)
  - 中心圆: cx=20, cy=20, r=3
  - 12 花瓣 (椭圆 rx=4, ry=12) + 12 射线 (三角形) 交替
  - 位置: left=54pt, top=528pt
- **Wordmark**: "Claude" (Georgia serif, 22pt)
  - 位置: left=94pt, top=531pt

### 目录 (Contents)
- **背景**: 白色
- **标题**: "Contents" — 30pt serif, left=54pt, top=84pt
- **表格**: 双栏 (条目 + 页码)
  - 位置: left=54pt, top=138pt, width=684pt
  - 字体: Noto Sans CJK SC, 12pt
- **页码**: 7pt, right=60pt, bottom=30pt

### 章节扉页 (Chapter Opener)
- **背景**: 章节颜色 (Coral→Teal→Purple→Mint→Lavender→Peach→Warm Gray 循环)
- **Pill**: `<rect x="54.25" y="418.6" width="68" height="19.15" rx="9.5" stroke="#141413" stroke-width="1.5" fill="none"/>`
- **Pill 文字**: "Chapter X" — 11pt sans, left=63pt, top=484pt
- **标题**: 中文标题, 48pt serif, left=54pt, top=506pt, 行高 52pt
- **页码**: 7pt, right=60pt, bottom=30pt

### 正文页 (Body Page)
- **背景**: 白色
- **章节标题**: 30pt serif, left=54pt, top=118pt
- **正文容器**: 单栏 (左栏 54-408pt, width=354pt), top=160pt
  - 字体: Source Han Serif CN, 9pt, 行高 12.9pt
  - 字重: 400
- **副标题**: 13pt sans, 字重 600, 行高 16pt
- **页码**: 7pt, right=60pt, bottom=30pt

## 关键发现 (来自双语 PDF 分析)
1. 官方双语 PDF 使用 `Source Han Serif CN Regular` 作为中文正文字体
2. 中文行高 12.9pt (9pt × 1.43) 比英文 11.3pt (9pt × 1.25) 更宽松
3. 中英文标题/正文层级一致 (30pt > 13pt > 9pt)
4. 扉页是**完整单页** (颜色+Pill+标题在同一页)

## 渲染方式
- **引擎**: WeasyPrint (via `render_kami.py`)
- **输入**: 完整 HTML 字符串 (`render_html(html_text, base_url, out_path)`)
- **关键点**:
  - `@font-face` 必须匹配系统字体名 (如 `'Source Han Serif CN'`)
  - 中文文本必须在 HTML 中直接包含 UTF-8 编码的中文字符
  - `base_url` 设为 `/tmp` (无外部资源)

## 输出
- **PDF**: `/tmp/founders-playbook-zh-v1.pdf` (31 页, 691KB) — 中文翻译版
- **HTML**: `/tmp/founders-playbook-zh.html`
