---
name: typeset-engine
aliases:
- 排版引擎
- 文档渲染
- typeset
slug: typeset-engine
version: 2.1.0
description: '统一文档渲染引擎。通过 HTTP API (native 部署优先, docker 在 transition) 生成 PDF / DOCX / PPTX / 图表 / AI幻灯片 / AI配图。
  触发词：生成报告、排版、做个PDF、做个PPT、生成图表、投研报告、中金风格、
  渲染文档、出个Word、chart、illustrate、配图、AI PPT、幻灯片、Coding Plan、
  claude 风格、anthropic 风格、烧橙风格、长文报告、管理层讨论稿、研究报告 PDF、
  创始人指南、founders playbook、创业者风格、星战风格、star wars、光剑风格、
  学术论文、ieee 格式、中文论文、工作论文、SSRN、论文排版。
  不要用于：纯文本输出、Markdown 输出、不需要排版的场景。'
metadata:
  clawdbot:
    emoji: "\U0001F4D0"
    requires:
      bins:
      - curl
    os:
    - linux
    - darwin
---

# typeset-engine — 统一文档渲染引擎

HTTP API（默认端口 9091）生成专业文档。一个 curl 调用 = 一份完整文档。

> 部署形态：master 分支 = native (systemd 直管 .venv python)，2026-05-19 已正式
> 升为 canonical（取代原 docker 路线）。docker 时代代码归档到 `legacy-docker` 分支。
> 本机和 sg2 都切到 native，端口 9091 不变，调用方无感。详见
> `deploy/native/README.md`（路径保留）+ `docs/MIGRATION-docker-to-native.md`
> （老 docker 用户升级路径）。

## 触发词

- "生成报告" / "投研报告" / "研究报告"
- "做个PDF" / "做个PPT" / "出个Word"
- "生成图表" / "画个柱状图" / "饼图"
- "AI PPT" / "科技风幻灯片"
- "配个图" / "ticket风格" / "illustrate"
- "中金风格" / "摩根风格" / "CICC" / "gradient-glass"
- **"claude 风格" / "anthropic 风格" / "烧橙风格" / "长文报告" / "管理层讨论稿"** → kami `long-doc-claude`
- **"创始人指南" / "founders playbook" / "创业者风格" / "数据驱动长文"** → kami `founders-playbook`（slots + chapters[] 数据驱动，7 色循环扉页 + Claude 太阳花 logo）
- **"星战风格" / "star wars" / "光剑风格" / "银河风格"** → kami `long-doc-starwars`（深空蓝封面 + Star Wars 黄 + EPISODE 罗马数字章节扉页，**内部 / 创意场景 only**，不外发客户）
- **"学术论文" / "ieee 格式" / "中文论文" / "工作论文" / "SSRN"** → `/render/pdf` + `?theme=ieee|cn-paper|working-paper`（学位论文 PKU/HUST/SJTU 直接写 Typst 源码，不走 JSON API）

---

## kami 长文模板（WeasyPrint 链路）

适用于：管理层讨论稿、长篇研究报告、白皮书、战略推演（5-30 页 A4）。

| 触发词 | doc_type | 强调色 / 风格 | 页数约束 |
|--------|---------|--------|--------|
| 默认 / parchment / 商务长文 | `long-doc` | 深蓝 #1B365D | 5-9 |
| **claude / anthropic / 烧橙** | `long-doc-claude` | **烧橙 #d97757 + 鼠尾草绿 #788c5d** | 5-80 |
| **OpenAI 风格 / 大体量长报告** | `long-doc-openai` | OpenAI 黑白调 | 5-100 |
| **星战 / star wars / 光剑（内部 only）** | `long-doc-starwars` | Star Wars 黄 #FFE81F + 深空蓝 + EPISODE 罗马数字章节扉页 | 5-80 |
| **创始人指南 / founders playbook** | `founders-playbook` | 7 色循环扉页 (Coral/Teal/Purple/Mint/Lavender/Peach/Warm Gray) + Claude 太阳花 logo | 10-40 |

> ⚠️ **founders-playbook 是数据驱动模式**（不是模板替换）：必须传
> `slots = {title, subtitle, chapters: [{number, title, mode, body}]}`，每个
> chapter 的 `mode` 取 `full`/`minimal`/`plain` 控制扉页类型。详见
> `references/api-reference.md` 和 `scripts/render_kami.py:_build_fpb_html`。

调用方式（CLI 或 Python）：

```bash
python3 /home/guyii/clawd/code/typeset-engine/scripts/render_kami.py \
  --template long-doc-claude --lang zh \
  --body /tmp/body.html --out /tmp/report.pdf
```

或在 Python 脚本中：

```python
from scripts.render_kami import render_template
render_template(
    doc_type="long-doc-claude",
    language="zh",
    body_html=BODY,            # 自己拼接的 <section> 序列
    slots=None,
    out_path="/tmp/report.pdf",
)
```

**Claude 风格的核心技术特征**（详见模板顶部注释 + 下文"风格特征"段）：
- 配色：parchment #faf9f5（更白画布）+ brand #d97757（烧橙）+ olive #788c5d（鼠尾草绿）+ tag-bg #f3e2d6（蜜桃）
- 字体：思源宋体 SC（中文正文）+ Source Han Sans（UI 元素），单字重 500（标题不加粗）
- 排版：所有 H1 都有 2.5pt 烧橙左边线 + 1.5pt 圆角；callout / takeaway 用 ivory 底 + 烧橙左边线
- 章节：每个 `<section class="chapter">` 自动 break-before: page，开头是 sans-serif 烧橙小标题（chapter-num）
- 表格：极简风——表头烧橙底线，表体仅虚线分隔，无垂直边框，无斑马纹

---

## Step 0 · 前置（必查）

健康检查：

```bash
curl -s http://localhost:9091/health
# 期望：{"status": "ok", "engine": "typeset-engine", "version": "1.0"}
```

如果失败，按部署形态恢复：

```bash
# 形态 A: native (本机和 sg2 默认, master 分支 = canonical)
ss -tlnp | grep :9091   # 看进程是否还在
# 进程死了 → 重启:
cd /home/guyii/clawd/code/typeset-engine && \
  PORT=9091 OUTPUT_DIR=/tmp/native-output \
  GEMINI_API_KEY=$(grep '^GEMINI_API_KEY=' ~/.env | cut -d= -f2-) \
  nohup .venv/bin/python scripts/server.py > /tmp/native.log 2>&1 &

# 形态 B: docker (transition, 不推荐新接入)
docker start typeset-engine
```

⚠️ 远端 sg2 用 systemd: `ssh sg2 'systemctl status typeset && systemctl restart typeset'`

---

## Step 1 · 判断任务类型

| 用户说 | 端点 | 输出 | 需 API Key |
|---|---|---|:---:|
| 投研报告 / 白皮书（Typst 强结构）| `POST /render/pdf` | PDF | 否 |
| 学术论文 / ieee / 中文论文 / 工作论文（`?theme=ieee\|cn-paper\|working-paper`）| `POST /render/pdf` | PDF | 否 |
| 简历 / 一页纸 / 正式信件 / 作品集 / 长文报告 / 创始人指南 / 星战风 | `POST /render/kami` | PDF | 否 |
| 出个 Word / 文档化 | `POST /render/docx` | DOCX | 否 |
| 做 PPT / 演示 / 幻灯片 | `POST /render/pptx` | PPTX | 否 |
| 生成图表 / 柱状图 / 饼图 | `POST /render/chart` | PNG | 否 |
| SVG 技术图 → PNG | `POST /render/diagram` | PNG/SVG | 否 |
| CSS 美学扫描（9 条铁律） | `POST /validate/css` | JSON | 否 |
| AI PPT（从一个主题生成全部内容） | `POST /render/pptx-ai` | ZIP | **是**（Gemini, **billing-enabled**） |
| AI 配图 / 图示 | `POST /render/illustrate` | PNG | **是**（Gemini, **billing-enabled**） |

> ⚠️ Gemini key 必须是 **billing-enabled GCP 项目** — Google 对图像生成模型
> (`gemini-2.5-flash-image`) free tier 配额 = 0。free key 调 illustrate / pptx-ai
> 会得到 429 RESOURCE_EXHAUSTED。本机用 `~/.env` 里那把 (`AIzaSyAItJ...JVHFM`)，
> 不是 `~/.bashrc` 里那把 free key。

> 📋 **PPTX 有 20 种 layout**（12 通用 + 8 投行）— `title / section / content /
> two_column / table / summary / chart / kpi / comparison / timeline / quote /
> end` + `comparable_companies / football_field / sources_uses /
> sensitivity_matrix / transaction_overview / disclaimer / waterfall / org_chart`。
> 完整 schema 见 `scripts/render_pptx.py` docstring + `tests/test_render_pptx_layouts.py`
> (21/21 测试覆盖每个 layout 的 minimal payload)。
> **table layout 陷阱**: `headers`/`rows` 直接放 slide 顶层，**不要**嵌成
> `"table": {"headers":..., "rows":...}`（旧文档错误示例，会触发
> `ZeroDivisionError: cols=0`，已在 commit 13953a3 修 docstring）。

**kami 路线 vs /render/pdf 路线的差别**：
- `/render/pdf`（Typst）：cicc/ms/cms/dachen 等**投行/金融主题** + ieee/cn-paper/working-paper 等**学术主题**，JSON → 结构化报告，适合有 KPI 卡、图表、目录、免责声明的**长报告**
- `/render/kami`（WeasyPrint）：**编辑级精排**（简历/一页纸/白皮书/信件/作品集），暖米纸 + 油墨蓝 + serif 500，agent 填 HTML 模板直出

**学术主题速查**：

| theme | 说明 | 字体/格式 |
|-------|------|----------|
| `ieee` | IEEE 双栏学术论文 | Liberation Serif, 10pt |
| `cn-paper` | 中文学术论文 | 宋体/黑体/楷体, 五号 |
| `working-paper` | SSRN 工作论文 | 英文通用学术 |

学术 JSON 最简示例：
```bash
curl -s -X POST "http://localhost:9091/render/pdf?theme=ieee" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Paper Title",
    "authors": [{"name": "Author", "organization": "University"}],
    "abstract": "Abstract text...",
    "keywords": ["AI", "NLP"],
    "sections": [
      {"type": "heading", "title": "Introduction", "children": [
        {"type": "paragraph", "content": "Content..."}
      ]}
    ]
  }' -o /tmp/paper.pdf
```

> ⚠️ **学位论文**（PKU / HUST / SJTU）模板存于 `templates/academic/`，需直接写 Typst 源码 import，**不走 JSON API**。

模糊时**一句话问**，不要猜（例："做个总结" → 问"想要投研格式报告还是编辑级精排？"）。

---

## Step 2 · 如果用户给的是原料，先 Distill

跳过此步如果用户已给出结构化内容（明确章节 + 要点 + 数字）。

拿到**原料**（会议记录、脑暴、聊天转录、散点笔记）时：

1. **提取**：每条事实/数字/日期/名字/动作项都拎出来
2. **归类**：映射到目标文档的 section 结构（见 API 参考的 section type 表）
3. **Gap-check**：列出模板需要但原料缺的内容，做一个 compact 表
4. **问一次**：把 gap 表交回用户。**不要瞎补**。

Gap-check 示例：

| 模板需要 | 已有 | 缺 |
|---|---|---|
| 4 个 KPI 卡 | "8 年"、"50 人团队" | 还差 2 个量化指标 |
| 3-5 个核心项目 | 2 个 | 至少再要 1 个带结果的 |
| 图表数据 | 收入趋势（3 点） | — |

补全后进 Step 3。

完整 distill 规范与更多示例：`references/workflow.md`。

---

## Step 3 · 按 Tier 加载规范

按任务 tier 选最低所需的参考文件，**不要一次性全读**：

| Tier | 什么时候 | 读 |
|---|---|---|
| **T0 仅内容** | 更新文字、换数据、翻译，模板/CSS 不动 | 仅本 SKILL.md |
| **T1 标准调用** | 用现成主题生成新文档 | 本 SKILL + `references/api-reference.md` + `tests/test_render_pptx_layouts.py`（看 21 个 layout 的最小 payload） |
| **T2 新主题/CSS** | 加新 theme，或改 CSS token | `references/design-constraints.md`（**必读**）+ `tests/test_kami_template_sanity.py`（模板合法性校验） |
| **T3 Troubleshoot** | 渲染异常、字体 fallback、页溢出、图表错位 | `references/design-constraints.md` 第 5 节 + 进程日志（native: `journalctl -u typeset` 或 `/tmp/native.log`；docker: `docker logs`） |
| **T4 原料→结构化** | 用户丢了一堆散点要求排版 | `references/workflow.md`（distill + gap-check 全流程） |

可以中途升级 tier。

---

## Step 4 · 填 JSON / HTML → 调 API → 落盘

### 4A · Typst 路线（投研/公文/长报告）

```bash
cat > /tmp/report.json << 'EOF'
{
  "title": "报告标题",
  "author": "作者",
  "date": "2026-04-22",
  "theme": "cicc",
  "toc": true,
  "sections": [
    {"type": "heading", "title": "核心观点", "children": [
      {"type": "quote", "content": "核心结论一句话"}
    ]}
  ]
}
EOF

curl -s -X POST http://localhost:9091/render/pdf \
  -H "Content-Type: application/json" \
  -d @/tmp/report.json -o /tmp/report.pdf
```

### 4B · kami 路线（简历/一页纸/精排文档）

**Step 4B.1**：列出可用模板
```bash
curl -s http://localhost:9091/kami/templates
```
返回 **14 个模板**：
- 标准 (5 类型 × 2 语言)：`one-pager` / `long-doc` / `letter` / `portfolio` / `resume` × `zh|en`
- 长文变体（仅 zh）：`long-doc-claude` / `long-doc-openai` / `long-doc-starwars`
- 数据驱动（仅 zh）：`founders-playbook`

**Step 4B.2**：拿到模板源码本地填内容
```bash
curl -s "http://localhost:9091/kami/template/resume?lang=en" > /tmp/resume.html
# 本地用编辑器 / Write 工具修改 /tmp/resume.html 的 <body> 内容
```

**Step 4B.3**：渲染（3 种模式任选）

```bash
# 模式 1：整 HTML 模式（最灵活）— agent 本地填好全量 HTML
curl -s -X POST http://localhost:9091/render/kami \
  -H "Content-Type: application/json" \
  -d "{\"html\": $(jq -Rs . < /tmp/resume.html)}" \
  -o /tmp/resume.pdf

# 模式 2：body_html 替换（只换 body 内容，保留模板 CSS/字体）
curl -s -X POST http://localhost:9091/render/kami \
  -H "Content-Type: application/json" \
  -d '{"doc_type":"resume","language":"en","body_html":"<h1>Name</h1>...<section>...</section>"}' \
  -o /tmp/resume.pdf

# 模式 3：slots 替换（模板里有 {{key}} 占位符时）
curl -s -X POST http://localhost:9091/render/kami \
  -H "Content-Type: application/json" \
  -d '{"doc_type":"one-pager","language":"zh","slots":{"文档标题":"...","作者":"...","日期":"..."}}' \
  -o /tmp/brief.pdf
```

> 💡 **中文 key 现已支持**（commit d9c91c1, 2026-05-19）。模板里大量
> `{{文档标题}}`、`{{副标题}}`、`{{作者}}` 等中文占位符可以直接传中文 key 替换。
> 老版本 `_apply_slots` 正则 `[a-zA-Z_]...` 只接 ASCII，导致 14 模板 698 个占位符
> 中 490 个失效（特别是 `long-doc-*` / `one-pager` 中文版的 slots 模式整体不可用），
> 现已修复。如调用 sg2 早于 commit d9c91c1 的版本，需带上 body_html 作为兜底。

> 💡 **混用 body_html + slots**：当模板 CSS 里有 `{{文档标题}}` 之类
> `@page @bottom-left { content: "{{文档标题}}" }` 时，body_html 模式无法替换
> CSS 里的占位符（只换 `<body>` innerHTML）。解法是**同时**传 slots（覆盖 CSS
> 占位符）+ body_html（覆盖正文），二者叠加（先 slots 后 body_html）。

响应 header 里 `X-Kami-Pages: 2` 告诉你实际页数，`X-Kami-Warnings` 在页数出约束时会出现。

**kami 路线关键约束**：
- 改 HTML 时 **CSS 部分不要动**，只动 `<body>` 内容
- 保留模板原有的 `@font-face` 和 `--var()` token
- 每条新加的内容都要符合 `references/design-constraints.md` 的 9 条铁律

完整 JSON schema、全部 section type、全部 theme/style、所有端点 → `references/api-reference.md`。

---

## Step 5 · 验证

生成后必须验证以下三项，有问题回到对应 tier：

1. **文件完整**：`ls -la` 看大小 ≠ 0
2. **页数合理**：resume 应 ≤2 页；one-pager ≤1 页；long-doc 期望 7±2；portfolio 6±2
   ```bash
   python3 -c "from pypdf import PdfReader; print(len(PdfReader('/tmp/report.pdf').pages))"
   ```
3. **视觉抽查**：用户可见瑕疵（字体乱、图表错位、表格溢出）→ 回 T3

发送给用户：
```bash
curl -s -F chat_id=60555976 \
  -F document=@"/tmp/report.pdf" \
  -F caption="标题" \
  "https://api.telegram.org/bot8250723750:AAH0Yv0hj6CpHv9A0eyCa3vveQqg4ZSvhx4/sendDocument"
```

---

## 设计约束（改 CSS/新主题时强制遵守）

这是 typeset-engine 的**美学宪法**。违反任一条要有明确理由，否则必定出 AI slop。

**9 条铁律**（完整版见 `references/design-constraints.md`）：

1. **画布**：用暖色底（`#f5f4ed` 米纸 或 theme 定义色），**禁纯白 `#ffffff`**
2. **强调色**：每份文档**只能一种**强调色（例：`#1B365D` 油墨蓝）；禁止第二个彩色 hue
3. **中性色全暖调**：黄褐底色系，**禁冷蓝灰**（`#8C8C8C` 这种禁用）
4. **Serif 字重锁死 500**：正文、标题、引用全用 500，**禁 bold**（700）
5. **行高**：标题 1.1-1.3，密集正文 1.4-1.45，阅读正文 1.5-1.55，**禁 ≥1.6**
6. **阴影**：只有 ring（`0 0 0 1px`）或 whisper（`0 1px 2px rgba(0,0,0,.04)`）；**禁 hard drop shadow**
7. **Tag 底色必须实色 hex**：`rgba()` 会触发 WeasyPrint 双矩形 bug
8. **薄 border + border-radius** 组合慎用：border <1pt 时圆角会双圈
9. **页面尺寸用 mm 明确值**，禁 `height: 100vh`（`@page` 下不准）

---

## 字体策略（**不用商业字体**）

当前 engine 使用：

- **中文**：`Source Han Serif SC` → `Noto Serif CJK SC` → `Songti SC` → `Georgia`
- **英文**：`Newsreader`（OFL 开源）或 `Charter` → `Georgia` → system-ui

**不要**要求 TsangerJinKai02（商业字体，需 tsanger.cn 授权）。现有 theme 全部基于开源 fallback 链。

---

## 反馈协议（用户说模糊话时）

用户说"太挤了/不好看/不对劲/不专业"时：**禁止直接动手改**，必须先回问带当前值的封闭选项。

| 用户说 | 回问（必须带当前值 + 2 个具体选项） |
|---|---|
| "太挤了" | "X 元素现在是 line-height 1.35、padding 8mm。要改成 (a) line-height 1.5 还是 (b) padding 12mm？" |
| "太松了" | 同上反向 |
| "颜色不对" | "哪个元素？主色当前 `#1B365D`；可选 (a) 调深到 `#12233F` 或 (b) 换 `#2B4A6F`？" |
| "不够好看" | "是 (a) 层级不清（标题字号差太小） (b) 留白不均 还是 (c) 字体渲染？" |
| "看着不专业" | "是 (a) 文案措辞 还是 (b) 对齐/一致性问题？" |

模板句式：**"X 当前是 Y，要改成 (a) Z1 还是 (b) Z2？"**

绝对不要说"我来调一下间距"这种话而不指明具体属性和新值。

完整反馈矩阵：`references/workflow.md` 第 3 节。

---

## 故障排查

| 问题 | 解法 |
|---|---|
| 连接失败 | `ss -tlnp \| grep :9091` 看进程, 死了按 Step 0 形态 A/B 重启 |
| AI 功能 500 | 检查 `/etc/typeset/typeset.env` (native) 或容器 env (docker) 里 `GEMINI_API_KEY` 已填 |
| **AI 功能 429 / RESOURCE_EXHAUSTED** | key 所属 GCP 项目对 image 模型 free tier 配额=0 → **必须 billing-enabled key**；报错 model 显示 `-preview-image` ≠ 代码传的 `-flash-image`（Google 计费名 vs API 名，别改代码） |
| 中文乱码 | 不应出现；`curl http://localhost:9091/fonts` 看注册字体, 应含 `Source Han Serif SC` 和 `Noto Sans CJK SC` |
| 页数超限（resume > 2 页） | 字体 fallback / 行高 / 字号 动一点就爆，读 T3 |
| 表格溢出页 | `break-inside` 在 flex 失效 → 包 block wrapper |
| 图表错位 / 双矩形 | 肯定违反了约束 7：找 `rgba(` 改实色 hex |
| **PPTX `ZeroDivisionError: cols=0`** | `table` layout 错把 headers/rows 嵌成 `"table": {}` 对象 → 必须直接放 slide 顶层（见 Step 1 PPTX 速查表的陷阱说明） |
| **kami 模板里 `{{文档标题}}` 字面值出现在页脚** | 老 sg2 / 老 docker 版本 `_apply_slots` 不支持中文 key → 升级到 commit d9c91c1 之后，或同时传 body_html 兜底 |
| **kami 渲染出 CSS 源码当正文** | 模板源文件被破坏（曾出现 `<<htmlhtml>` 重复 tag）→ 跑 `tests/test_kami_template_sanity.py` 扫描，commit e03de9c 后已加 lint 防护 |

深度踩坑表见 `references/design-constraints.md` 第 5 节。

---

## 项目仓库

https://github.com/guyiicn/typeset-engine
