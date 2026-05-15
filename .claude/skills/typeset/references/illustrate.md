# illustrate reference

`/render/illustrate` 用 Gemini 给任意文本生成精美插图 PNG。

## ⚠️ 必需

容器启动时必须带 `GEMINI_API_KEY`。同 pptx-ai：缺 key 时 `docker rm -f` 后重启。

---

## JSON

```json
{
  "content": "AI Agent 多智能体协作架构解析",
  "style": "ticket",
  "title": "Multi-Agent Architecture (可选)",
  "ratio": "16:9",
  "cover": false
}
```

| field | 必需 | 说明 |
|---|---|---|
| `content` | 是 | 要配图的文本 |
| `style` | 是 | 见下表 |
| `title` | 否 | 显示在图中的标题 |
| `ratio` | 否 | `16:9` / `3:4` / `1:1`，默认 `16:9` |
| `cover` | 否 | `true` = 封面图模式（更大字体、更聚焦），默认 `false` |

## style

| style | 视觉 |
|---|---|
| `gradient-glass` | 科技玻璃风（深色背景，3D 物体，霓虹渐变） |
| `vector-illustration` | 矢量插画风（扁平、复古配色、几何简化） |
| `ticket` | 数字票券风（黑白对比、网格排版、极简信息图） |

---

## 调用

```bash
bash ~/.claude/skills/typeset/scripts/render.sh \
  /render/illustrate /tmp/typeset-output/payload.json \
  /tmp/typeset-output/illustration.png
```

## Gotchas

- **生成时间**：~10-20s 单张。
- **重复风格 vs 多次生成**：同 prompt + 同 style 每次输出不同（Gemini 非确定性）。如果第一张不满意，重跑即可。
- **content 不要太长**：超过 500 字效果会变差，建议核心要点 ≤ 200 字。
