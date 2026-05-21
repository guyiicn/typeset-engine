#!/usr/bin/env bash
# typeset-engine 沙箱无 sudo 部署 (离线 bundle 版)
#
# 用法 (沙箱端):
#   把 install-from-bundle.sh + typeset-env.tar.gz + typeset-engine-code.tar.gz
#   三个文件下到同一目录 (例如 ~/bundle/), 然后:
#       cd ~/bundle && bash install-from-bundle.sh
#
#   默认装到 $HOME/typeset/, 用 install-from-bundle.sh <DEST> 改位置.
#
# bundle 内容:
#   - typeset-env.tar.gz       (947 MB conda env, 含 Python/cairo/pango/weasyprint/
#                              Noto CJK/AR PL UKai/Liberation/typst/Chrome/...)
#   - typeset-engine-code.tar.gz (40 MB git archive, master HEAD f8323d3)
#   - install-from-bundle.sh   (本脚本)
#
# 启动:
#   GEMINI_API_KEY=AIza... PORT=9090 bash $DEST/start.sh
#   或后台: bash $DEST/start.sh --bg

set -euo pipefail

DEST="${1:-$HOME/typeset}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_TARBALL="$SCRIPT_DIR/typeset-env.tar.gz"
CODE_TARBALL="$SCRIPT_DIR/typeset-engine-code.tar.gz"

log()  { printf '\033[1;34m[*]\033[0m %s\n' "$*"; }
ok()   { printf '\033[1;32m[+]\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m[!]\033[0m %s\n' "$*"; }
die()  { printf '\033[1;31m[x]\033[0m %s\n' "$*" >&2; exit 1; }

# ─── 预检 ──────────────────────────────────────────────────────
[[ -f "$ENV_TARBALL"  ]] || die "找不到 $ENV_TARBALL (要跟脚本同目录)"
[[ -f "$CODE_TARBALL" ]] || die "找不到 $CODE_TARBALL"
command -v tar >/dev/null || die "tar 未装"

AVAIL_KB=$(df -k "$(dirname "$DEST")" 2>/dev/null | awk 'NR==2 {print $4}')
[[ "$AVAIL_KB" -gt 4000000 ]] || warn "目标盘空间 < 4 GB ($AVAIL_KB KB), 解压可能失败"

log "目标位置: $DEST"
mkdir -p "$DEST"

# ─── 1. 解压 conda env ─────────────────────────────────────────
ENV_PREFIX="$DEST/miniforge3/envs/typeset"
if [[ -x "$ENV_PREFIX/bin/python" && -f "$ENV_PREFIX/conda-meta/history" ]]; then
    ok "conda env 已存在 ($ENV_PREFIX), 跳过解压"
else
    log "1. 解压 conda env tarball (947 MB → ~3 GB, ~2 分钟)"
    mkdir -p "$ENV_PREFIX"
    tar -xzf "$ENV_TARBALL" -C "$ENV_PREFIX"
    [[ -x "$ENV_PREFIX/bin/conda-unpack" ]] || die "conda-unpack 不存在, tarball 可能损坏"
fi

# ─── 2. conda-unpack 修 hardcoded prefix ───────────────────────
# conda-unpack 的 shebang 是 `#!/usr/bin/env python`, 沙箱无系统 python 会失败.
# 显式用 env 内的 python 调.
log "2. conda-unpack 修复 hardcode prefix (从原 build 路径 → 当前 $ENV_PREFIX)"
"$ENV_PREFIX/bin/python" "$ENV_PREFIX/bin/conda-unpack"
ok "conda-unpack 完成"

# ─── 3. 解压代码 ───────────────────────────────────────────────
if [[ -d "$DEST/typeset-engine" && -f "$DEST/typeset-engine/scripts/server.py" ]]; then
    ok "代码已解压, 跳过"
else
    log "3. 解压 typeset-engine 代码 (40 MB)"
    tar -xzf "$CODE_TARBALL" -C "$DEST"
    [[ -f "$DEST/typeset-engine/scripts/server.py" ]] || die "代码解压失败"
fi

# ─── 4. 生成 start.sh ──────────────────────────────────────────
log "4. 生成 start.sh"
cat > "$DEST/start.sh" <<EOF
#!/usr/bin/env bash
# typeset-engine 沙箱启动 (离线 bundle 版)
set -e
DEST="\${DEST:-$DEST}"
ENV="\$DEST/miniforge3/envs/typeset"
PORT="\${PORT:-9090}"
OUTPUT_DIR="\${OUTPUT_DIR:-\$HOME/typeset-output}"
mkdir -p "\$OUTPUT_DIR"

# GEMINI key 兜底 (~/.env 自动读取)
if [[ -z "\${GEMINI_API_KEY:-}" && -f "\$HOME/.env" ]]; then
    export GEMINI_API_KEY=\$(grep '^GEMINI_API_KEY=' "\$HOME/.env" | cut -d= -f2-)
fi

cd "\$DEST/typeset-engine"
export PORT OUTPUT_DIR
export PATH="\$ENV/bin:\$PATH"
# typst 不读 fontconfig, 必须显式指字体路径
export TYPST_FONT_PATHS="\$ENV/fonts:\$ENV/share/fonts"

if [[ "\${1:-}" == "--bg" ]]; then
    nohup "\$ENV/bin/python" scripts/server.py > "\$HOME/typeset.log" 2>&1 &
    echo "started PID \$!, log: \$HOME/typeset.log"
else
    exec "\$ENV/bin/python" scripts/server.py
fi
EOF
chmod +x "$DEST/start.sh"

# ─── 5. 烟雾测试 (中文 weasyprint) ────────────────────────────
log "5. 自检: weasyprint 中文渲染"
"$ENV_PREFIX/bin/python" <<'PY' 2>&1 || warn "weasyprint 自检失败, 看日志"
from weasyprint import HTML
HTML(string="<h1>沙箱 bundle install OK</h1><p>中文渲染走 Noto CJK</p>").write_pdf("/tmp/smoke.pdf")
import os
print(f"  smoke PDF: {os.path.getsize('/tmp/smoke.pdf')} bytes")
PY

cat <<EOF

═══════════════════════════════════════════════════════════
✅ 部署完成: $DEST  ($(du -sh "$DEST" 2>/dev/null | cut -f1))

启动 (前台, Ctrl-C 退):
  GEMINI_API_KEY=AIza... PORT=9090 bash $DEST/start.sh

启动 (后台):
  GEMINI_API_KEY=AIza... PORT=9090 bash $DEST/start.sh --bg
  # log: ~/typeset.log

验证:
  curl http://localhost:9090/health
  curl http://localhost:9090/capabilities

卸载:
  rm -rf $DEST ~/typeset-output ~/typeset.log

bundle 内代码版本: $(cd "$DEST/typeset-engine" && head -1 README.md 2>/dev/null || echo "git archive HEAD f8323d3")
═══════════════════════════════════════════════════════════
EOF
