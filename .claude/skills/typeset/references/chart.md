# chart reference

`/render/chart` 用 Plotly 渲染单张 PNG（输出 1920×1080 默认）。

## JSON

```json
{
  "type": "bar",
  "theme": "cicc",
  "title": "营收对比",
  "categories": ["2022", "2023", "2024"],
  "series": [
    {"name": "营收", "values": [100, 120, 150]},
    {"name": "利润", "values": [30, 40, 55]}
  ]
}
```

## type（13 种）

`bar` · `line` · `area` · `pie` · `waterfall` · `scatter` · `heatmap` · `radar` · `funnel` · `gauge` · `treemap` · `candlestick` · `combo`

## theme（4 种）

| theme | 配色 |
|---|---|
| `default` | 通用 |
| `cicc` | 中金风（深蓝+红） |
| `goldman` | Goldman 风（深蓝+浅蓝） |
| `dark` | 暗色 |

## 类型差异提醒

- `pie` / `funnel` / `gauge` / `treemap` 通常**只取一个 series** 的 values。
- `heatmap` 需要二维数据：`{"z": [[1,2],[3,4]], "x": [...], "y": [...]}`。
- `candlestick` 需要 OHLC：`{"x": [...], "open": [...], "high": [...], "low": [...], "close": [...]}`。
- `scatter` 用 `{"x": [...], "y": [...]}` 替代 categories。

具体字段以 `<typeset-engine repo>/scripts/render_charts.py` 为准。

## 调用

```bash
bash ~/.claude/skills/typeset/scripts/render.sh \
  /render/chart /tmp/typeset-output/payload.json \
  /tmp/typeset-output/chart.png
```
