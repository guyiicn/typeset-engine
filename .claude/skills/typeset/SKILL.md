---
name: typeset
description: Load when the user wants to render content into PDF / DOCX / PPTX / data chart / technical diagram / AI slide deck / AI illustration via the local typeset-engine HTTP API (port 9091, container "typeset-engine"). Triggers — "出一份PDF/DOCX/PPTX", "做投研报告", "排版", "渲染幻灯片", "生成图表/技术图", "AI 配图", "用 typeset 出一份…". Do NOT load for: pure text answers, screenshots, Markdown viewing, or content that won't end up as a real output file.
---

# typeset

把对话内容渲染成文件，调用本地 typeset-engine HTTP API（`http://localhost:9091`）。

## 流程（按顺序，不要跳步）

### 0. 确认容器在跑

```bash
bash ~/.claude/skills/typeset/scripts/ensure_running.sh
```

非 0 退出 → 把错误转给用户并停止。

### 1. AskUserQuestion：选输出类型

| label | endpoint | 输出 ext | 需 GEMINI_API_KEY |
|---|---|---|---|
| PDF 文档 | `/render/pdf` | `.pdf` | 否 |
| DOCX Word | `/render/docx` | `.docx` | 否 |
| PPTX 演示 | `/render/pptx` | `.pptx` | 否 |
| 数据图表 | `/render/chart` | `.png` | 否 |
| 技术架构图 | `/render/diagram` | `.png` | 否 |
| AI 幻灯片 | `/render/pptx-ai` | `.zip` | **是** |
| AI 配图 | `/render/illustrate` | `.png` | **是** |

如果用户选了 AI 端点但容器没带 GEMINI key（见 Gotcha #2），提醒并改选或重启容器。

### 2. 加载对应 reference + AskUserQuestion 选风格

只读用户选的那一份，节省上下文：

| 输出类型 | reference |
|---|---|
| pdf / docx | `references/pdf.md` |
| pptx | `references/pptx.md` |
| chart | `references/chart.md` |
| diagram | `references/diagram.md` |
| pptx-ai | `references/pptx-ai.md` |
| illustrate | `references/illustrate.md` |

读完 reference 用 AskUserQuestion 让用户选 theme / layout / style。

### 3. 构造 JSON

按 reference schema，把对话上下文整理成 JSON，写到 `/tmp/typeset-output/payload.json`。

- **严格遵守字段名**。不确定的字段省略，**不要瞎编**。
- UTF-8 + 双引号；中文直接写，不要 `\uXXXX` escape。
- 不确定字段是否存在 → 看权威源 `<typeset-engine repo>/scripts/render_<type>.py`。

### 4. 调用 API

```bash
bash ~/.claude/skills/typeset/scripts/render.sh \
  <endpoint> /tmp/typeset-output/payload.json \
  /tmp/typeset-output/<filename>.<ext> [query_string]
```

例：
```bash
bash ~/.claude/skills/typeset/scripts/render.sh \
  /render/pdf /tmp/typeset-output/payload.json \
  /tmp/typeset-output/report.pdf "theme=cicc"
```

`render.sh` 会做 HTTP 状态码检查，非 200 自动报错并打印响应前 1000 字节。

### 5. AskUserQuestion：选交付方式

| label | 行动 |
|---|---|
| 仅本地 | 给用户绝对路径即可 |
| Telegram 推送 | 调用 `Skill(telegram-sendfile)`，参数为生成文件的绝对路径 |

## 容器约定

- 容器名：`typeset-engine`
- 端口映射：`9091:9090`
- 输出挂载：`/tmp/typeset-output -> /app/output`
- 镜像：`typeset-engine:v3`
- 项目源码（权威 schema 来源）：`<typeset-engine repo>/`

## Gotchas

1. **docker 权限**：如果脚本报 `permission denied while trying to connect to the Docker daemon`，docker 组没生效——让用户重新登录或 `newgrp docker`。脚本不会自动 sudo。

2. **AI 端点的 key**：`/render/pptx-ai` 与 `/render/illustrate` 必须容器启动时带 `GEMINI_API_KEY` env。`ensure_running.sh` 启动时会从宿主环境透传，所以用户得先 `export GEMINI_API_KEY=...` 再让 ensure_running 第一次拉起容器。**容器一旦起来就不能动态加 env**——如果容器在跑但缺 key，先 `docker rm -f typeset-engine` 再调 `ensure_running.sh`。

3. **只问 3 个问题**：用户的设计原则是 type → style → delivery，三步走。不要为了"完整"硬塞第 4 个 AskUserQuestion。内容来源是对话上下文，不是另起一问。

4. **diagram 端点没有 server-side theme**：风格全部由 SVG 内容决定。`references/diagram.md` 指向项目内 `references/diagram/style-*.md` 取风格指南；自己写 SVG 时再贴这些规则给 Claude 借鉴。

5. **大文件**：pdf 几十~几百 KB，pptx 几百 KB~几 MB，pptx-ai zip 1-10 MB，diagram png 1-3 MB——都在 telegram-sendfile 50 MB 限内，直发即可。

6. **不要重 build 镜像**：`docker images typeset-engine` 检查一下，已有 `:v3` 就别再 build。Dockerfile 改了再 build。

7. **JSON 字段不对会 500**：reference 里的字段名是从 README/USAGE 整理的，可能与 `scripts/render_*.py` 实际期望略有偏差。返回 4xx/5xx 时去看对应的 render 脚本源码，里面的 dict key 是权威。
