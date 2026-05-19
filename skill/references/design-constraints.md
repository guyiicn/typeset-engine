# typeset-engine 设计约束（美学宪法）

适用于：新建 theme、改 CSS token、写 HTML 模板、手工调样式。
**T0/T1 任务（仅内容）不需要读本文**。

灵感来自 [tw93/kami](https://github.com/tw93/kami) 的 9 条铁律，结合 typeset-engine 自身（Typst / WeasyPrint / python-pptx 多路线）做了适配。

---

## 1. 画布（Canvas）

| 允许 | 禁止 |
|---|---|
| `#f5f4ed` 米纸 | `#ffffff` 纯白 |
| `#faf9f5` 象牙 | `#fafafa` 冷白 |
| theme 预设暖底（cicc 的深蓝也 OK，它是主色不是画布） | 任何 R=G=B 的灰白 |

**为什么**：纯白在 PDF 里反光重、不像纸。暖底（R>G>B 的 1-3% 偏差）在纸质输出和屏幕阅读都更舒服。

**cicc / ms / cms / dachen 这四个现有主题**：继续用现有预设，不要改。

---

## 2. 强调色（Accent）

**一份文档只能有一种强调色**。其他着色必须来自中性色链。

typeset-engine 主题的强调色：

| theme | 强调色 | Hex |
|---|---|---|
| `cicc` 中金 | 深蓝 | `#1B365D` |
| `ms` 摩根 | 蓝纸蓝 | `#3D5A80` |
| `cms` 招商 | 招商红 | `#C8102E` |
| `dachen` 达晨 | 稳重深红 | `#8B1538` |

**禁止**：一份报告里同时出现两种 hue（比如蓝+红、蓝+绿）。红色装饰线作为品牌元素属于中性色维度（黑/红双色品牌系统），不算第二 hue。

---

## 3. 中性色（Neutrals）

**全部暖调**（R ≥ G ≥ B，黄褐底色）。

推荐色板（来自 kami tokens）：

| token | Hex | 用处 |
|---|---|---|
| `--parchment` | `#f5f4ed` | 画布 |
| `--ivory` | `#faf9f5` | 卡片底 |
| `--near-black` | `#141413` | 最深字色 |
| `--dark-warm` | `#3d3d3a` | 标题字 |
| `--charcoal` | `#4d4c48` | 正文字 |
| `--olive` | `#5e5d59` | 辅助字 |
| `--stone` | `#87867f` | 元信息 / 分割线 |

**禁止使用的冷灰**（这些是 AI slop 标志）：

```
#8C8C8C  #999999  #A0A0A0  #666666  #333333
#e5e7eb  #d1d5db  #9ca3af  #6b7280  #374151
```

以上 Tailwind 默认 gray 系在 print 下都会出现冷蓝偏，**一律替换成暖调等价色**。

---

## 4. 字体 & 字重

### 字体链（**不用商业字体**）

**中文**：
```
Source Han Serif SC, Noto Serif CJK SC, Songti SC, Georgia, serif
```

**英文**：
```
Newsreader, Charter, Georgia, system-ui, serif
```

Docker 镜像里已有 `fonts-noto-cjk` 和 Source Han fallback。Newsreader 从 Google Fonts OFL 获取，放 `typeset-engine/fonts/` 下，模板用 `@font-face` 相对路径加载。

### 字重规则

- **Serif 正文**：`font-weight: 500`
- **Serif 标题**：`font-weight: 500`（**不加粗**）
- **Sans UI 元素**（label、eyebrow、meta）：`font-weight: 400-500`
- **禁用**：`font-weight: 700` / `bold`（在 serif 上永远禁；sans 上仅 cover 页大标题例外）

单字重是 typeset-engine 的设计 signature。想要"强调"靠**字号跳跃 + 字色跳跃**，不靠 bold。

---

## 5. 行高（Line-height）

| 用途 | 允许范围 | 推荐 |
|---|---|---|
| 大标题（H1 cover） | 1.1 - 1.25 | 1.15 |
| 小标题（H2/H3） | 1.2 - 1.35 | 1.3 |
| 密集正文（表格、卡片内文） | 1.4 - 1.45 | 1.42 |
| 阅读正文（long-doc 段落） | 1.5 - 1.55 | 1.52 |
| eyebrow / label | 1.1 - 1.3 | 1.2 |

**禁止** `line-height ≥ 1.6`。超过会显得松垮没密度。这条是 build.py --check 扫描的第一目标。

---

## 6. 阴影

只允许两种：

```css
/* Ring shadow: 薄一层，用于 tag、badge */
box-shadow: 0 0 0 1px rgba(20, 20, 19, 0.08);

/* Whisper shadow: 浮起感，用于卡片 */
box-shadow: 0 1px 2px rgba(20, 20, 19, 0.04);
```

**禁止**：

```css
/* 硬 drop shadow — 看起来就是 1999 年 PowerPoint */
box-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
box-shadow: 4px 4px 8px #888888;

/* 多层深阴影 */
box-shadow: 0 4px 6px rgba(0,0,0,.1), 0 10px 15px rgba(0,0,0,.15);
```

PDF 输出的阴影经常失真，宁可不加。纸面阅读靠间距和 ruler 线建立层级，不靠阴影。

---

## 7. Tag / Badge 底色 — 必须实色 hex

```css
/* ✓ 对 */
.tag { background: #e8e6df; color: #4d4c48; }

/* ✗ 错 — WeasyPrint 双矩形 bug */
.tag { background: rgba(20, 20, 19, 0.08); }
```

`rgba()` 在 WeasyPrint 渲染 `<span class="tag">` 时会画两次，导致**双层错位矩形**。必须预先把 alpha 合成成实色 hex。

合成工具：

```python
def blend(fg_hex: str, alpha: float, bg_hex: str = "#f5f4ed") -> str:
    fg = tuple(int(fg_hex[i:i+2], 16) for i in (1, 3, 5))
    bg = tuple(int(bg_hex[i:i+2], 16) for i in (1, 3, 5))
    out = tuple(int(f * alpha + b * (1 - alpha)) for f, b in zip(fg, bg))
    return "#" + "".join(f"{c:02x}" for c in out)
```

---

## 8. Border + 圆角的双圈陷阱

```css
/* ✗ 错 — 薄 border + 圆角 → 双圈 */
.card {
  border: 0.5px solid #ddd;
  border-radius: 8px;
}

/* ✓ 对 — border ≥ 1pt，或不用 border 改用 ring shadow */
.card {
  border: 1pt solid #e0ddd4;
  border-radius: 8px;
}
/* 或 */
.card {
  box-shadow: 0 0 0 1px rgba(20, 20, 19, 0.08);
  border-radius: 8px;
}
```

---

## 9. 页面尺寸 & 分页

```css
/* ✓ 对 */
@page {
  size: 210mm 297mm;  /* A4 显式 */
  margin: 18mm 16mm;
}
.page { height: 261mm; }  /* 297 - 2*18 */

/* ✗ 错 */
@page { size: A4; }  /* 某些 engine 下不识别别名 */
.page { height: 100vh; }  /* @page 下 vh 不准 */
```

**break-inside 在 flex 里不生效**（WeasyPrint bug）：

```html
<!-- ✗ 错 -->
<div style="display: flex; break-inside: avoid;">...</div>

<!-- ✓ 对：外层 block 包装 -->
<div style="break-inside: avoid;">
  <div style="display: flex;">...</div>
</div>
```

**SVG marker orient="auto" 不转向**（WeasyPrint 不支持），箭头方向需手工计算并写死 `rotate()`。

---

## 10. Typst 主题专属约束

现有 Typst 主题（`cicc-report.typ`、`gongwen.typ`、`themes.typ`）：

- `themes.typ` 内色板不要手动改，改完要跑 `scripts/render_pdf.py --test all-themes`
- 新 theme 必须继承 `themes.typ` 的 tokens，不要 copy-paste
- 公文主题（`gongwen.typ`）字体链锁死国标（方正小标宋、方正仿宋、方正黑体、方正楷体），**不走这套暖调约束**——公文有自己的国家规范

---

## 自动扫描（T3 troubleshoot 必用）

理想情况下应该有 `scripts/validate_css.py` 执行：

```python
# 扫描违规
import re, pathlib

COOL_GRAYS = {"#8C8C8C", "#999999", "#A0A0A0", "#666666", "#333333",
              "#e5e7eb", "#d1d5db", "#9ca3af", "#6b7280", "#374151"}

issues = []
for f in pathlib.Path("templates").rglob("*.html"):
    text = f.read_text()
    # rgba in tag/badge
    if re.search(r"\.(tag|badge|chip)[^{]*\{[^}]*rgba\(", text):
        issues.append((f, "rgba in tag/badge → 双矩形 bug"))
    # cool gray
    for g in COOL_GRAYS:
        if g.lower() in text.lower():
            issues.append((f, f"cool gray {g}"))
    # line-height >= 1.6
    for m in re.finditer(r"line-height:\s*([\d.]+)", text):
        if float(m.group(1)) >= 1.6:
            issues.append((f, f"line-height {m.group(1)} ≥ 1.6"))

for f, msg in issues:
    print(f"✗ {f}: {msg}")
```

**建议**：把这个脚本加到 `typeset-engine/scripts/validate_kami.py`，和现有 `validate_docx.py` 平行。集成到 Docker 镜像后，每次 `/render/*` 前后都可以跑一次扫描。

---

## 违反约束的后果示例

**做过这件事的文档 = AI slop 识别标志**：

| 违反 | 效果 |
|---|---|
| 纯白画布 + 多种彩色高亮 | "Google Doc 默认稿" 观感 |
| bold 到处用 | 层级视觉噪音 |
| 冷灰字 + 暖色图片 | 色温冲突，廉价感 |
| 硬 drop shadow | 2005 年 Web 2.0 风 |
| rgba tag | WeasyPrint 双层错位矩形（直接 bug） |
| line-height 1.8 | "宽松友好" 的假象，其实是稀薄无密度 |

这套约束的价值：**排除 90% 的俗 pattern**，让输出一眼看得出"这是认真做的，不是随便跑的 AI"。
