# diagram reference

`/render/diagram` 接收 SVG 字符串，用 `rsvg-convert` 输出 1920px PNG。
**Server 端没有 theme 参数**——风格全部由 SVG 内容决定。

## JSON

```json
{
  "svg": "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 1920 1080'>...</svg>",
  "width": 1920
}
```

`width` 可选，默认 1920。

---

## 7 种风格指南（写 SVG 时参考）

让 Claude 自己写 SVG 之前，**先读对应 style 文件**学规范。文件在项目里：

```
<typeset-engine repo>/references/diagram/
├── style-1-flat-icon.md         # 扁平图标风，白底（文档/博客）
├── style-2-dark-terminal.md     # 暗黑终端 #0f0f1a（GitHub README）
├── style-3-blueprint.md         # 蓝图 #0a1628（架构设计）
├── style-4-notion-clean.md      # Notion 极简，白底（Wiki）
├── style-5-glassmorphism.md     # 玻璃态，深色渐变（Keynote/官网）
├── style-6-claude-official.md   # Claude #f8f6f3（Anthropic 风格）
└── style-7-openai-official.md   # OpenAI 白底
```

## 10 种图模板（SVG 起始模板）

```
<typeset-engine repo>/references/diagram-templates/*.svg
```

10 种常见架构图（multi-agent / pipeline / data-flow / 三层架构 / microservices 等）。读完拷贝并按需求改字段、配色、连线。

## 7 种风格示例数据

```
<typeset-engine repo>/references/diagram-fixtures/*.json
```

每个 style 一个完整 SVG 示例（可直接 POST 验证渲染流程，再做小改）。

---

## 工作流

1. 问用户选哪种 style（1-7）。
2. 读 `style-N-*.md` + 一个匹配的 template SVG。
3. 按内容改 SVG（节点 label、连线、配色按 style 规范来）。
4. 用 `jq` 把 SVG 包装成 JSON：

```bash
# 写 SVG 到 svg.txt，然后：
jq -Rs '{svg: ., width: 1920}' < /tmp/typeset-output/svg.txt \
  > /tmp/typeset-output/payload.json

bash ~/.claude/skills/typeset/scripts/render.sh \
  /render/diagram /tmp/typeset-output/payload.json \
  /tmp/typeset-output/diagram.png
```

或者直接 Python：

```python
import json, pathlib
svg = pathlib.Path('/tmp/typeset-output/svg.txt').read_text()
pathlib.Path('/tmp/typeset-output/payload.json').write_text(
    json.dumps({"svg": svg, "width": 1920})
)
```

## Gotchas

- **SVG 里的中文**：`xmlns` 必须有，`<text>` 用 `font-family="Noto Sans CJK SC"` 才能正确渲染。
- **复杂 SVG 30s 超时**：节点超过 ~80 个考虑分图。
- **rsvg-convert 不支持 `<foreignObject>`**：所有文字用 `<text>`，不能内嵌 HTML。
