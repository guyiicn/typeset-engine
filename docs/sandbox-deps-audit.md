# typeset-engine 系统依赖盘点

跑通所有 14 个端点需要哪些 .so / 二进制 / 字体。

## C 库（最难绕过 sudo 的部分）

| 库 | 哪个端点需要 | conda-forge 包名 | 备注 |
|---|---|---|---|
| `libpango-1.0.so.0` | `/render/kami` (WeasyPrint) | `pango` | 文本布局核心 |
| `libcairo.so.2` | 同上 | `cairo` | 2D 绘图 |
| `libgdk-pixbuf-2.0.so.0` | 同上 | `gdk-pixbuf` | 图片加载 |
| `libharfbuzz.so.0` | 同上 | `harfbuzz` | 文本 shaping |
| `libfontconfig.so.1` | 全部 | `fontconfig` | 字体查找 |
| `libfreetype.so.6` | 全部 | `freetype` | 字体光栅化 |
| `libglib-2.0.so.0` | pango 依赖 | `glib` | 注意版本一致! |
| `librsvg-2.so.2` | `/render/diagram` | `librsvg` | SVG → PNG (rsvg-convert) |

## 系统二进制

| 二进制 | 哪个端点需要 | 替代方案 |
|---|---|---|
| `rsvg-convert` | `/render/diagram` | conda-forge `librsvg` 装时带 |
| `ffmpeg` | `/render/pptx-ai` (视频合成) | conda-forge `ffmpeg` |
| `typst` | `/render/pdf` `/render/docx` | GitHub release 单 binary, 拷进 env/bin/ 即可 |

## Chrome (kaleido)

| 用途 | 大小 | 来源 |
|---|---|---|
| `kaleido` (Plotly → PNG) `/render/chart` 必需 | 250MB | typeset-engine repo 的 `native-v1.0` release 已经打包好 |

## 字体

| 字体 | 必需吗 | conda-forge / 包名 |
|---|---|---|
| Noto Sans CJK SC | 中文渲染必需 | `font-noto-cjk` (conda-forge) |
| Source Han Serif SC | kami long-doc-* 模板用 | `font-source-han-serif` 不确定 conda-forge 有, 可能要手动塞 |
| 公文专用方正字体 | 仅 gongwen / tbs 主题 | 仓库自带 `fonts/` 目录 |
| Liberation Serif | ieee 等学术主题 | `font-liberation` |

## Python wheel (pip install 即可)

不需要 sudo:
- weasyprint==68.1 (cffi → 系统 libpango/libcairo, **这是难点**)
- python-pptx, python-docx, pypdf
- plotly, kaleido, matplotlib, pillow
- google-genai
- 其他

## 总结：sandbox 必装清单

```
[conda-forge 装到 env]
python=3.12
cairo pango harfbuzz fontconfig freetype gdk-pixbuf glib
librsvg ffmpeg
font-noto-cjk font-liberation
weasyprint plotly kaleido matplotlib pillow pypdf
python-pptx python-docx
google-generativeai python-dotenv

[手动塞进 env]
typst (二进制, GitHub release, ~30MB)
chrome-linux64 (kaleido, GitHub release native-v1.0, 148MB)
typeset-engine 源码 (git clone master)
公文字体 (fonts/*.TTF, 仓库自带 ~10MB)
```

体积估算：
- conda env (含所有 .so) ~700MB
- Chrome 250MB
- 代码 + 字体 ~20MB
- **总 tarball pack 后约 1.2-1.5 GB**
