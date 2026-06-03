#!/usr/bin/env bash
# ==============================================================================
# install-user-fonts.sh — 黑金风格 (heijin) 用户级字体注册
#
# 作用：把 黑金风格 用到的拉丁大标题字体 Playfair Display 注册到 *用户级*
#       fontconfig (~/.local/share/fonts)，无需 sudo、不碰系统目录。
#
# 重要：黑金模板 (templates/kami/heijin.html) 的渲染 *不依赖* 本脚本——
#       模板用 @font-face 指向 templates/kami/fonts/*.woff2 (WeasyPrint 经
#       base_url 自包含解析)，开箱即渲染。本脚本只是把字体额外注册到
#       fontconfig，方便其它工具 / 按字体名引用 / 系统级发现。
#
# 幂等：可重复运行。仅复制 + 刷新用户字体缓存。
#
# 用法：  bash scripts/install-user-fonts.sh
# ==============================================================================
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC_DIR="$REPO_DIR/fonts/heijin"
DEST_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/fonts/typeset-heijin"

echo "▸ 黑金风格用户级字体注册"
echo "  源:   $SRC_DIR"
echo "  目标: $DEST_DIR"

if [[ ! -d "$SRC_DIR" ]]; then
  echo "✗ 找不到字体源目录 $SRC_DIR (确认已 git pull 最新代码)" >&2
  exit 1
fi

mkdir -p "$DEST_DIR"
copied=0
shopt -s nullglob
for f in "$SRC_DIR"/*.ttf "$SRC_DIR"/*.otf; do
  cp -f "$f" "$DEST_DIR/"
  echo "  + $(basename "$f")"
  copied=$((copied+1))
done
shopt -u nullglob

if [[ "$copied" -eq 0 ]]; then
  echo "✗ 源目录无 ttf/otf 字体文件" >&2
  exit 1
fi

# 仅刷新用户字体缓存（不传系统路径，绝不触碰 /usr/share /usr/local）
echo "▸ 刷新用户字体缓存 (fc-cache -f \"$DEST_DIR\")"
fc-cache -f "$DEST_DIR" >/dev/null 2>&1 || fc-cache -f >/dev/null 2>&1 || true

echo "▸ 校验"
ok=1
verify() { # family -> 期望命中文件名包含 needle
  local fam="$1" needle="$2" hit
  hit="$(fc-match "$fam" 2>/dev/null || true)"
  if echo "$hit" | grep -qi "$needle"; then
    echo "  ✓ $fam  ->  $hit"
  else
    echo "  ✗ $fam 未命中预期字体 (got: ${hit:-none})"; ok=0
  fi
}
verify "Playfair Display" "Playfair"

# CJK 衬线 (黑金正文/标题中文) — 系统级，缺失时给安装提示，不强制失败
echo "▸ 检查中文衬线 (黑金正文/标题依赖；任一可用即可)"
cjk_ok=0
for fam in "Source Han Serif CN" "Source Han Serif SC" "Noto Serif CJK SC"; do
  hit="$(fc-match "$fam" 2>/dev/null || true)"
  # fc-match 总会回退，故按命中文件名是否真为思源/Noto Serif CJK 判断
  if echo "$hit" | grep -qiE "SourceHanSerif|NotoSerifCJK|思源宋体"; then
    echo "  ✓ 命中中文衬线: $fam -> $hit"; cjk_ok=1; break
  fi
done
if [[ "$cjk_ok" -eq 0 ]]; then
  echo "  ⚠ 未发现思源宋体 / Noto Serif CJK SC。黑金中文会回退到默认字体，观感下降。"
  echo "    安装建议(任选其一)："
  echo "      apt:   sudo apt-get install -y fonts-noto-cjk    # 提供 Noto Serif CJK SC"
  echo "      用户级: 把 SourceHanSerifCN-*.otf 放进 ~/.local/share/fonts 后 fc-cache -f"
fi

echo
if [[ "$ok" -eq 1 ]]; then
  echo "✅ 用户级字体注册完成。"
else
  echo "⚠ 注册完成，但部分校验未通过（见上）。模板仍可经 @font-face woff2 正常渲染。"
fi
