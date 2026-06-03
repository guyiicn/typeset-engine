# 黑金风格 (heijin / black-gold) — 深色技术阅读简报模式

一个 Kami (HTML→PDF) 模板，复刻"深色技术阅读简报" PDF 的排版语言：近黑蓝底 +
单一暗金强调，衬线(叙述) / 等宽(数据) 二元，适合技术报告/论文阅读摘要、产品规格
简报、研究速记。

- **doc_type**: `heijin`（别名 `黑金`，symlink → heijin）
- **模板**: `templates/kami/heijin.html`（含完整设计系统文档头）
- **引擎**: WeasyPrint（与其它 Kami 模板一致）

---

## 1. 快速使用

### HTTP（推荐；服务常驻）

```bash
# ⚠ 端口是 9091（不是 9090！9090 被 mihomo 代理占用，会回 Go 式 "404 page not found"）
# ⚠ 本机 curl 测 localhost 必须 --noproxy '*'，否则 HTTPS_PROXY(mihomo) 截走返 502
curl -s --noproxy '*' -X POST http://127.0.0.1:9091/render/kami \
  -H 'Content-Type: application/json' \
  -d '{"doc_type":"heijin","language":"zh",
       "slots":{"文档标题":"我的简报 · 2026-06-03"},
       "body_html":"<section class=\"hero\">...</section>..."}' \
  -o out.pdf
```

### CLI

```bash
cd /home/guyii/clawd/code/typeset-engine
# 直接渲染模板自带的示例内容（showcase）
.venv/bin/python scripts/render_kami.py --template heijin --out /tmp/o.pdf

# 注入自定义内容：--body 是 body innerHTML 文件，--slots 是 JSON 文件路径
printf '{"文档标题":"我的简报"}' > /tmp/slots.json
.venv/bin/python scripts/render_kami.py --template heijin --lang zh \
  --body /tmp/body.html --slots /tmp/slots.json --out /tmp/o.pdf
```

### 两种填充方式（来自 render_kami.render_template）

| 方式 | 作用 | 优先级 |
|---|---|---|
| `slots` | 替换模板里的 `{{key}}` 占位符（如页脚 / `<title>` 的 `{{文档标题}}`）；支持中文 key | 先执行 |
| `body_html` | **整段替换** `<body>...</body>` innerHTML，用文档化的组件 class 写正文 | 后执行，最高 |

典型用法：`slots` 填页脚标题，`body_html` 填正文（用下面的组件库）。模板的 `<head>`
（CSS / @font-face / @page）始终保留。

---

## 2. 设计系统

**单强调色**：近黑蓝底 `#0a0c10` 上只用一种暗金 `#cda85f`，其余靠灰阶分层；点缀色
（绿/橙）只用于卡片头区分语义，不进正文。**字体二元**：衬线承载叙述，等宽承载数据。

| token | 值 | 用途 |
|---|---|---|
| `--bg` | `#0a0c10` | 页面底 |
| `--card` / `--card2` | `#14171f` / `#181c26` | 卡片底 / 表头 |
| `--line` | `#262b37` | 分隔线/边框 |
| `--gold` / `--gold-hi` | `#cda85f` / `#e2bd6d` | 主强调 / 亮金大数字 |
| `--teal` / `--coral` | `#5cb79a` / `#d9895c` | 卡片头点缀 |
| `--tx` / `--tx-hi` / `--tx-dim` | `#c4c9d2` / `#eef0f4` / `#7f8694` | 正文/白标题/弱化 |

**字体**（全部在模板 `:root` 已配好 fallback 链）：
- 拉丁大标题 = **Playfair Display**（Didone 高对比，杂志感）
- 中文标题/正文 = **Source Han Serif CN / Noto Serif CJK SC**（思源宋体）
- 拉丁正文衬线(含斜体) = **Newsreader**
- 等宽 = **JetBrains Mono + Noto Sans Mono CJK SC**

---

## 3. 组件库（body_html 里用这些 class）

```html
<!-- 封面 -->
<section class="hero">
  <span class="eyebrow">EYEBROW<span class="sub"> · 副栏目</span></span>
  <h1 class="title">Big Title</h1>             <!-- Playfair 大标题 -->
  <div class="subtitle">副标题</div>
  <div class="meta">来源 <b>X</b> · 日期 <b>Y</b></div>
</section>

<!-- 4 列数据卡 -->
<div class="stats">
  <div class="stat"><div class="num">30T</div><div class="cap">说明</div></div>
  ... 共 4 个 ...
</div>

<hr class="sep">                                    <!-- 节间分隔线 -->
<div class="sec"><span class="no">01</span><h2>节标题</h2></div>
<p class="lead"><em>引语斜体</em> 正文…</p>      <!-- 导语 -->

<div class="h3">小节标题 <span class="note">mono 注脚</span></div>

<!-- 双栏圆点卡片：dot 用 g(金)/t(绿)/c(橙) -->
<div class="cols">
  <div class="card"><div class="head"><span class="dot g"></span>标题</div>
    <ul class="list"><li>要点…</li></ul></div>
  <div class="card">…</div>
</div>

<!-- 左金边引用块 -->
<div class="callout"><div class="label">LABEL</div><p>…</p></div>

<!-- 深色表 + 金色高亮行 tr.hl -->
<table><thead><tr><th>列</th>…</tr></thead>
  <tbody><tr><td>…</td></tr><tr class="hl"><td>高亮行</td></tr></tbody></table>

<!-- 金色递减漏斗 + 右侧标注 -->
<div class="funnel">
  <div class="row"><div class="bar" style="width:100%">100% 标签</div></div>
  <div class="row"><div class="bar" style="width:33%">33% <span class="pct">(明细)</span></div>
    <span class="ann">/ 右侧注</span></div>
</div>

<!-- 胶囊流程 -->
<div class="flow">
  <span class="pill">A</span><span class="arr">→</span>
  <span class="pill final">终点</span>
</div>

<!-- 大号衬线编号 tips -->
<div class="tip"><div class="n">1</div>
  <div class="body"><div class="h">标题</div><div class="d">说明</div></div></div>

<!-- 页脚 -->
<div class="footer"><div class="by">编制 · <b>名字</b></div>
  <div class="fine">免责声明…</div></div>

<!-- 行内：<em>斜体强调</em> <b>白色加重</b> <span class="tag">等宽标签</span> <span class="gold">金色</span> -->
```

### WeasyPrint 兼容红线（改模板必读）
- ✅ 可用：`flex`、`linear/radial-gradient`、`box-shadow`、`text-shadow`、`transform`、`@page background`
- ❌ **不要用** CSS `grid` 和 `gap`（WeasyPrint 支持不稳）。多列布局用 `display:flex` + `.card + .card{margin-left}`
- 所有"块"组件加 `break-inside:avoid`（深色卡片被分页切断极丑）
- 不要用固定页高 `min-height:297mm` + 强制 `break`，容易产生半空孤页；让内容自然流式分页

---

## 4. 字体安装/注册

模板**渲染本身不依赖系统字体注册**：`@font-face` 指向 `templates/kami/fonts/*.woff2`
（Playfair / Newsreader / JetBrains Mono 都在仓库里），WeasyPrint 经 `base_url` 自包含解析，
**git pull 后开箱即渲染**。

用户级 fontconfig 注册（可选，便于其它工具/按名引用）：

```bash
bash scripts/install-user-fonts.sh
```

该脚本：把 `fonts/heijin/PlayfairDisplay-*.ttf` 复制到 `~/.local/share/fonts/typeset-heijin/`
并 `fc-cache -f`；**无需 sudo、不碰系统目录**；幂等。并会检查思源宋体/Noto Serif CJK 是否
可用（中文衬线依赖），缺失时给 apt 安装提示。

> 中文衬线 (Source Han Serif CN / Noto Serif CJK SC) 走系统 fontconfig。新机器若缺，
> `sudo apt-get install -y fonts-noto-cjk` 或把 SourceHanSerifCN-*.otf 放进 `~/.local/share/fonts`。

---

## 5. 给其它 Agent：升级 / 安装 SOP

> 适用场景：另一台机器 / 另一个 agent 要拿到并启用"黑金风格"。

```bash
# 1. 拉最新代码（黑金在 master）
cd /home/guyii/clawd/code/typeset-engine        # 本机 canonical 路径
git pull origin master

# 2. 用户级字体注册（可选但推荐）
bash scripts/install-user-fonts.sh

# 3. 重启服务让 HTTP 认识新 doc_type
#    ⚠ typeset 现为 *user* systemd 服务（非 docker）
systemctl --user restart typeset.service
systemctl --user is-active typeset.service       # 期望 active

# 4. 验证（注意 9091 + --noproxy）
curl -s --noproxy '*' http://127.0.0.1:9091/health
printf '{"文档标题":"smoke"}' > /tmp/s.json
.venv/bin/python scripts/render_kami.py --template heijin --slots /tmp/s.json --out /tmp/heijin-smoke.pdf
#    → 期望输出 {"pages": N, ...}，无 traceback
```

### 升级要点 / 常见坑
- **端口 9091**，不是 9090（9090=mihomo 代理，回 Go 式 404）。实际端口见服务 env `PORT`。
- 本机 `HTTPS_PROXY=127.0.0.1:7890`(mihomo)，curl 测 localhost **必须 `--noproxy '*'`**，否则 502。
- venv 在 `./.venv`，**必须用 `/usr/bin/python3.13` 建**（anaconda python 会拉旧 glib 与系统
  libpango 不兼容）。
- 改 `render_kami.py` 的 `DOC_TYPES` / `PAGE_LIMITS` 后**必须重启服务**（CLI 每次重读文件、
  无需重启；HTTP 服务进程启动时载入）。
- 新增/改 Kami 模板：放 `templates/kami/{doc_type}.html`，在 `render_kami.py` 的
  `DOC_TYPES` + `PAGE_LIMITS` 各登记一行即可；字体放 `templates/kami/fonts/` 并用相对
  `@font-face`（base_url 已是该目录）。

### 涉及文件清单（黑金）
```
templates/kami/heijin.html              模板（含设计系统文档头）
templates/kami/{heijin-en,黑金,黑金-en}.html   symlink → heijin.html
templates/kami/fonts/PlayfairDisplay-{700,800,900}.woff2   渲染用(自包含)
fonts/heijin/PlayfairDisplay-{700,900}.ttf                 用户级注册用(脚本读取)
scripts/install-user-fonts.sh           用户级字体注册脚本
scripts/render_kami.py                   DOC_TYPES + PAGE_LIMITS 各 +2 行
docs/heijin-black-gold.md                本文档
```
