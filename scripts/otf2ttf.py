#!/usr/bin/env python3
"""otf2ttf.py — 把 CFF/OTF 字体转成 glyf 轮廓的 TrueType (.ttf)。

为什么需要：CFF/OTF 字体（如思源宋体 Source Han Serif、Noto CJK）被 WeasyPrint
子集嵌入 PDF 后是 `CID Type 0C`，**苹果 PDFKit (iOS / Preview / 快速查看) 渲染会失败
→ 中文整片空白**（桌面 poppler/Adobe 正常）。把字体先转成 glyf(TrueType) 轮廓即可
全平台正常。黑金风格 (templates/kami/heijin.html) 的中文衬线即用本脚本预生成。

用法:
    python scripts/otf2ttf.py <in.otf> <out.ttf>
    # 再压成 woff2（可选，体积更小，给 @font-face 用）：
    python -c "from fontTools.ttLib import TTFont; f=TTFont('out.ttf'); f.flavor='woff2'; f.save('out.woff2')"

依赖: fontTools (+ cu2qu, 已内置)。CJK 全字符集约 3 万字形，单字重约 16s。
"""
import sys
import time
from fontTools.ttLib import TTFont, newTable
from fontTools.pens.cu2quPen import Cu2QuPen
from fontTools.pens.ttGlyphPen import TTGlyphPen

MAX_ERR = 1.0  # 立方→二次贝塞尔逼近误差(font units)，1.0 视觉无损


def otf_to_ttf(src: str, dst: str, max_err: float = MAX_ERR) -> None:
    t0 = time.time()
    f = TTFont(src)
    if f.sfntVersion != "OTTO" or "CFF " not in f:
        raise SystemExit(f"{src} 不是 CFF/OTF 字体（无需转换或格式不符）")
    glyph_order = f.getGlyphOrder()
    glyph_set = f.getGlyphSet()
    quad = {}
    for gname in glyph_order:
        pen = TTGlyphPen(glyph_set)
        glyph_set[gname].draw(Cu2QuPen(pen, max_err))
        quad[gname] = pen.glyph()
    f["loca"] = newTable("loca")
    glyf = f["glyf"] = newTable("glyf")
    glyf.glyphOrder = glyph_order
    glyf.glyphs = quad
    del f["CFF "]
    glyf.compile(f)
    f["maxp"].numGlyphs = len(glyph_order)
    if "post" in f:
        f["post"].formatType = 3.0  # 降级 post，避免 CFF 名表残留
    f.sfntVersion = "\x00\x01\x00\x00"
    f.save(dst)
    print(f"OK {len(glyph_order)} glyphs in {time.time() - t0:.1f}s -> {dst}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    otf_to_ttf(sys.argv[1], sys.argv[2])
