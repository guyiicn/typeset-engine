# pptx-ai reference

`/render/pptx-ai` 用 Gemini 生成精美幻灯片图片 + HTML 播放器（可选 MP4 视频），打包成 ZIP。

## ⚠️ 必需

容器启动时必须带 `GEMINI_API_KEY` env。如果容器已经在跑但缺 key：
```bash
docker rm -f typeset-engine
export GEMINI_API_KEY=xxx
bash ~/.claude/skills/typeset/scripts/ensure_running.sh
```

---

## JSON（slides_plan 格式）

```json
{
  "title": "演示标题",
  "style": "gradient-glass",
  "slides": [
    {"type": "cover",   "content": "封面标题文本"},
    {"type": "content", "content": "要点 1\n要点 2\n要点 3"},
    {"type": "data",    "content": "数据洞察 / 总结"},
    {"type": "content", "content": "..."}
  ]
}
```

## slide.type

| type | 用途 |
|---|---|
| `cover` | 封面 |
| `content` | 普通内容页（要点） |
| `data` | 数据/总结页（更视觉化） |

## style

| style | 视觉 |
|---|---|
| `gradient-glass` | 渐变玻璃，Apple Keynote 级科技感 |
| `vector-illustration` | 矢量插画，温暖教育风 |
| `ticket` | 数字票券，黑白对比，极简 |

自定义风格：在容器内 `/app/styles/` 放 `.md` 文件，文件名（不含 .md）作为 style 引用。

---

## query 参数（可选）

| param | 默认 | 说明 |
|---|---|---|
| `resolution` | `2K` | `2K` / `4K` |
| `video` | `false` | `true` 生成 MP4 |
| `duration` | `3.0` | 每帧秒数（生成视频时） |
| `transition` | `fade` | `fade` / `dissolve` / `wipeleft` / `slideright` / `none` |

---

## 输出

ZIP 文件，解开后包含：
- `slides/slide_001.png` ... `slide_NNN.png` — 高清图片
- `index.html` — 自包含 HTML5 播放器（键盘导航、全屏、自动播放）
- `presentation.mp4` — 带转场的视频（仅 `video=true`）
- `prompts.json` — 给 Gemini 的 prompt 记录

---

## 调用

```bash
# 不带视频，最快
bash ~/.claude/skills/typeset/scripts/render.sh \
  /render/pptx-ai /tmp/typeset-output/payload.json \
  /tmp/typeset-output/deck.zip "style=gradient-glass"

# 带 4K 视频，慢但漂亮
bash ~/.claude/skills/typeset/scripts/render.sh \
  /render/pptx-ai /tmp/typeset-output/payload.json \
  /tmp/typeset-output/deck.zip \
  "style=gradient-glass&resolution=4K&video=true&duration=3.5&transition=fade"
```

## Gotchas

- **生成时间**：每张幻灯片 ~10-30s（Gemini 调用），10 张约 2-5 分钟。视频额外 30s-2min。
- **配额**：Gemini 免费层有 RPM 限制，频繁调用会被节流。
- **ZIP 大小**：4K + video 通常 20-40 MB；2K 不带视频 1-5 MB。
