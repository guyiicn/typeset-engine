#!/usr/bin/env bash
# 在 build host 上一次性构建沙箱离线 bundle
#
# 用法 (在跑过 install.sh 的 host 上, 或 docker container 内):
#   bash deploy/sandbox/build-bundle.sh [DEST=$HOME/typeset] [OUT_DIR=/tmp/sandbox-bundle]
#
# 产物 (4 个文件):
#   typeset-env.tar.gz         (~950 MB, conda-pack 出的 env)
#   typeset-engine-code.tar.gz (~40 MB, git archive HEAD)
#   install-from-bundle.sh     (沙箱端解压脚本)
#   MD5SUMS                    (3 个文件 md5)
#
# 然后把 4 个文件上传到文件服务器, 沙箱端 curl 下来跑 install-from-bundle.sh.
# 详见 deploy/sandbox/README-bundle.md

set -euo pipefail

DEST="${1:-$HOME/typeset}"
OUT_DIR="${2:-/tmp/sandbox-bundle}"

ENV_PREFIX="$DEST/miniforge3/envs/typeset"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

log()  { printf '\033[1;34m[*]\033[0m %s\n' "$*"; }
ok()   { printf '\033[1;32m[+]\033[0m %s\n' "$*"; }
die()  { printf '\033[1;31m[x]\033[0m %s\n' "$*" >&2; exit 1; }

[[ -d "$ENV_PREFIX" ]] || die "$ENV_PREFIX 不存在 — 先跑 deploy/sandbox/install.sh build env"
[[ -d "$REPO_ROOT/.git" ]] || die "$REPO_ROOT 不是 git repo"
command -v "$DEST/miniforge3/bin/conda" >/dev/null || die "找不到 conda"

mkdir -p "$OUT_DIR"

# ─── 1. conda-pack env ────────────────────────────────────────
ENV_TARBALL="$OUT_DIR/typeset-env.tar.gz"
if [[ -f "$ENV_TARBALL" ]]; then
    log "1. $ENV_TARBALL 已存在, 跳过 (如要重建: rm $ENV_TARBALL)"
else
    log "1. 装 conda-pack (如未装)"
    "$DEST/miniforge3/bin/conda" install -n base -y -c conda-forge conda-pack 2>&1 | tail -3

    log "1a. 清缓存 (减体积)"
    "$DEST/miniforge3/bin/conda" clean -ay 2>&1 | tail -2

    log "1b. conda-pack env (~2-5 min)"
    "$DEST/miniforge3/bin/conda-pack" \
        -p "$ENV_PREFIX" \
        -o "$ENV_TARBALL" \
        --ignore-missing-files \
        2>&1 | tail -3
fi
ok "env tarball: $(du -h "$ENV_TARBALL" | cut -f1)"

# ─── 2. git archive code ─────────────────────────────────────
CODE_TARBALL="$OUT_DIR/typeset-engine-code.tar.gz"
log "2. git archive HEAD ($(cd "$REPO_ROOT" && git rev-parse --short HEAD))"
(cd "$REPO_ROOT" && git archive --format=tar.gz --prefix=typeset-engine/ HEAD -o "$CODE_TARBALL")
ok "code tarball: $(du -h "$CODE_TARBALL" | cut -f1)"

# ─── 3. 复制 install-from-bundle.sh ───────────────────────────
log "3. 复制 install-from-bundle.sh"
cp "$SCRIPT_DIR/install-from-bundle.sh" "$OUT_DIR/install-from-bundle.sh"
chmod +x "$OUT_DIR/install-from-bundle.sh"

# ─── 4. MD5SUMS ──────────────────────────────────────────────
log "4. 算 MD5SUMS (沙箱端校验完整性用)"
(cd "$OUT_DIR" && md5sum install-from-bundle.sh typeset-engine-code.tar.gz typeset-env.tar.gz > MD5SUMS)
cat "$OUT_DIR/MD5SUMS"

# ─── 5. README ──────────────────────────────────────────────
cp "$SCRIPT_DIR/README-bundle.md" "$OUT_DIR/README.md"

echo
ok "构建完成 — $OUT_DIR/"
ls -lh "$OUT_DIR/"
cat <<EOF

═══════════════════════════════════════════════════════════
下一步 (上传 4 个文件到文件服务器):
  $OUT_DIR/install-from-bundle.sh
  $OUT_DIR/typeset-engine-code.tar.gz
  $OUT_DIR/typeset-env.tar.gz
  $OUT_DIR/MD5SUMS

沙箱端部署:
  mkdir -p ~/bundle && cd ~/bundle
  curl -O https://YOUR-FILESERVER/typeset-bundle/{install-from-bundle.sh,typeset-engine-code.tar.gz,typeset-env.tar.gz,MD5SUMS}
  md5sum -c MD5SUMS && bash install-from-bundle.sh
═══════════════════════════════════════════════════════════
EOF
