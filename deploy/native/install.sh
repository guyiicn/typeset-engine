#!/usr/bin/env bash
# typeset-engine 非 Docker 部署脚本 — Debian/Ubuntu x86_64
#
# 用法 (在 git clone 出来的仓库根目录的 deploy/native/ 子目录里运行):
#   export HTTPS_PROXY=... HTTP_PROXY=... NO_PROXY=localhost,127.0.0.1
#   sudo -E bash install.sh
#
# 5 阶段:
#   1. 系统依赖 (apt)         2. Python venv + pip
#   3. typst 二进制 (GitHub)   4. Chrome (本仓库的 GitHub Release 附件)
#   5. 字体注册 (fc-cache + matplotlib 预热)

set -euo pipefail

# ═══════════════════════════════════════════════════════════
# 配置 — 可通过环境变量覆盖
# ═══════════════════════════════════════════════════════════
INSTALL_PREFIX="${INSTALL_PREFIX:-/opt/typeset-native}"
SERVICE_USER="${SERVICE_USER:-typeset}"
OUTPUT_DIR="${OUTPUT_DIR:-/var/lib/typeset/output}"
ENV_FILE="${ENV_FILE:-/etc/typeset/typeset.env}"
TYPST_VERSION="${TYPST_VERSION:-v0.14.0}"
PYTHON_BIN="${PYTHON_BIN:-python3.10}"

# Chrome 二进制下载 (本仓库 GitHub Release 附件)
CHROME_RELEASE_TAG="${CHROME_RELEASE_TAG:-native-v1.0}"
CHROME_RELEASE_REPO="${CHROME_RELEASE_REPO:-guyiicn/typeset-engine}"
CHROME_URL="${CHROME_URL:-https://github.com/${CHROME_RELEASE_REPO}/releases/download/${CHROME_RELEASE_TAG}/chrome-linux64.tar.gz}"
CHROME_SHA256="${CHROME_SHA256:-b876bb9106db4dcd354c5d7a67fa8d6a75cb1872277a4f542eda0240d78458f9}"

# ═══════════════════════════════════════════════════════════
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# 代理变量透传 (apt / pip / curl 都尊重这些)
export HTTPS_PROXY="${HTTPS_PROXY:-}"
export HTTP_PROXY="${HTTP_PROXY:-}"
export NO_PROXY="${NO_PROXY:-localhost,127.0.0.1}"

log()  { printf '\033[1;34m[*]\033[0m %s\n' "$*"; }
ok()   { printf '\033[1;32m[+]\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m[!]\033[0m %s\n' "$*"; }
die()  { printf '\033[1;31m[x]\033[0m %s\n' "$*" >&2; exit 1; }

[[ $EUID -eq 0 ]] || die "请以 root 运行 (sudo -E bash install.sh)"

# 健全性检查: 必须能找到 repo 根目录的源码
[[ -d "$REPO_ROOT/scripts" ]] || die "未找到 $REPO_ROOT/scripts — 请确认本脚本位于 typeset-engine repo 的 deploy/native/ 下"

if [[ -n "$HTTPS_PROXY" ]]; then
    log "代理已启用: HTTPS_PROXY=$HTTPS_PROXY"
else
    warn "未检测到 HTTPS_PROXY — 若目标机内网, 请 Ctrl-C 后先 export 代理变量"
fi

# ═══════════════════════════════════════════════════════════
# 阶段 1: 系统依赖
# ═══════════════════════════════════════════════════════════
log "[1/5] 安装系统依赖 (apt)"

if [[ -n "$HTTPS_PROXY" ]]; then
    cat > /etc/apt/apt.conf.d/99typeset-proxy <<EOF
Acquire::http::Proxy "$HTTP_PROXY";
Acquire::https::Proxy "$HTTPS_PROXY";
EOF
fi

apt-get update

# Ubuntu 24.04+ "t64 transition" (64-bit time_t)：libasound2 / libatk-bridge2.0-0
# / libcups2 等被 t64 后缀版本取代。自动选当前 apt 真正能装的名字，老系统
# (22.04/Debian 12) 走原名，24.04+ 走 t64 变体。
pick_pkg() {
    for cand in "$@"; do
        if apt-cache show "$cand" >/dev/null 2>&1; then
            echo "$cand"
            return 0
        fi
    done
    echo "$1"  # fallback：让 apt-get 自己报错
}
LIBASOUND=$(pick_pkg libasound2t64 libasound2)
LIBATK_BRIDGE=$(pick_pkg libatk-bridge2.0-0t64 libatk-bridge2.0-0)
LIBCUPS=$(pick_pkg libcups2t64 libcups2)

apt-get install -y --no-install-recommends \
    "$PYTHON_BIN" "${PYTHON_BIN}-venv" "${PYTHON_BIN}-dev" \
    curl xz-utils ca-certificates rsync \
    poppler-utils imagemagick diffutils librsvg2-bin ffmpeg \
    libnss3 "$LIBATK_BRIDGE" "$LIBCUPS" libxcomposite1 libxdamage1 \
    libxfixes3 libxrandr2 libgbm1 libxkbcommon0 libpango-1.0-0 \
    libcairo2 "$LIBASOUND" libxshmfence1 \
    fonts-noto-cjk fonts-arphic-ukai fonts-arphic-uming \
    fonts-cwtex-fs fonts-cwtex-heib fonts-cwtex-kai fonts-cwtex-ming \
    fonts-liberation

ok "系统依赖安装完成"

# ═══════════════════════════════════════════════════════════
# 阶段 2: 服务用户 + 目录 + 源码同步 + Python venv
# ═══════════════════════════════════════════════════════════
log "[2/5] 同步源码 + 创建 venv"

id "$SERVICE_USER" &>/dev/null || useradd -r -s /usr/sbin/nologin -d "$INSTALL_PREFIX" "$SERVICE_USER"

mkdir -p "$INSTALL_PREFIX/app" "$OUTPUT_DIR" "$(dirname "$ENV_FILE")"

# 仅同步运行时需要的子目录, 避免把 finrobot/tests/Dockerfile 等带过去
RSYNC_INCLUDES=(scripts styles templates references fonts)
for d in "${RSYNC_INCLUDES[@]}"; do
    [[ -d "$REPO_ROOT/$d" ]] || die "缺少 $REPO_ROOT/$d"
    rsync -a --delete \
        --exclude='__pycache__' --exclude='.pytest_cache' \
        "$REPO_ROOT/$d/" "$INSTALL_PREFIX/app/$d/"
done

"$PYTHON_BIN" -m venv "$INSTALL_PREFIX/.venv"
PIP="$INSTALL_PREFIX/.venv/bin/pip"

PIP_PROXY_ARGS=()
[[ -n "$HTTPS_PROXY" ]] && PIP_PROXY_ARGS=(--proxy "$HTTPS_PROXY")

"$PIP" install "${PIP_PROXY_ARGS[@]}" --upgrade pip setuptools wheel
"$PIP" install "${PIP_PROXY_ARGS[@]}" -r "$SCRIPT_DIR/requirements.txt"

ok "Python 依赖安装完成"

# ═══════════════════════════════════════════════════════════
# 阶段 3: typst 二进制
# ═══════════════════════════════════════════════════════════
log "[3/5] 安装 typst $TYPST_VERSION"

if command -v typst &>/dev/null && typst --version | grep -q "${TYPST_VERSION#v}"; then
    ok "typst $TYPST_VERSION 已存在, 跳过"
else
    TYPST_URL="https://github.com/typst/typst/releases/download/${TYPST_VERSION}/typst-x86_64-unknown-linux-musl.tar.xz"
    curl -fsSL "$TYPST_URL" | tar -xJ --strip-components=1 -C /usr/local/bin/ \
        typst-x86_64-unknown-linux-musl/typst
    typst --version
    ok "typst 安装完成"
fi

# ═══════════════════════════════════════════════════════════
# 阶段 4: Chrome (kaleido v1 依赖) — 从 GitHub Release 下载
# ═══════════════════════════════════════════════════════════
log "[4/5] 下载并部署 Chrome ($CHROME_RELEASE_TAG)"

CHROME_TARGET="$INSTALL_PREFIX/.venv/lib/${PYTHON_BIN}/site-packages/choreographer/cli/browser_exe"
[[ -d "$(dirname "$CHROME_TARGET")" ]] || die "choreographer 未安装 — pip 步骤可能失败"

TMP_TARBALL="$(mktemp --suffix=.tar.gz)"
trap 'rm -f "$TMP_TARBALL"' EXIT

log "下载 $CHROME_URL"
curl -fL --progress-bar -o "$TMP_TARBALL" "$CHROME_URL"

# sha256 校验
if [[ -n "$CHROME_SHA256" ]]; then
    log "校验 sha256..."
    ACTUAL=$(sha256sum "$TMP_TARBALL" | awk '{print $1}')
    if [[ "$ACTUAL" != "$CHROME_SHA256" ]]; then
        die "Chrome tarball sha256 不匹配: 期望 $CHROME_SHA256, 实际 $ACTUAL"
    fi
    ok "sha256 校验通过"
fi

mkdir -p "$CHROME_TARGET"
tar -xzf "$TMP_TARBALL" -C "$CHROME_TARGET"
chmod +x "$CHROME_TARGET/chrome-linux64/chrome" \
         "$CHROME_TARGET/chrome-linux64/chrome-wrapper" \
         "$CHROME_TARGET/chrome-linux64/chrome_crashpad_handler" 2>/dev/null || true

# 验证: choreographer 能找到 chrome
if "$INSTALL_PREFIX/.venv/bin/python" -c \
    "from choreographer.cli.browser_exe import get_browser_exe; print(get_browser_exe())" 2>/dev/null; then
    ok "Chrome 已就位"
else
    warn "Chrome 路径验证失败 — 首次运行 kaleido 可能报错, 检查 $CHROME_TARGET"
fi

# ═══════════════════════════════════════════════════════════
# 阶段 5: 字体注册
# ═══════════════════════════════════════════════════════════
log "[5/5] 注册字体"

if [[ -d "$INSTALL_PREFIX/app/fonts" ]]; then
    cp -n "$INSTALL_PREFIX/app/fonts/"*.{ttf,TTF,TTC,otf} /usr/local/share/fonts/ 2>/dev/null || true
fi
fc-cache -fv >/dev/null

"$INSTALL_PREFIX/.venv/bin/python" -c "
import matplotlib.font_manager as fm
fm._load_fontmanager(try_read_cache=False)
print(f'matplotlib fonts registered: {len(fm.fontManager.ttflist)}')
"
ok "字体注册完成"

# ═══════════════════════════════════════════════════════════
# 写 env 文件 + systemd 单元
# ═══════════════════════════════════════════════════════════
log "部署 env 文件和 systemd 单元"

if [[ ! -f "$ENV_FILE" ]]; then
    cp "$SCRIPT_DIR/env.example" "$ENV_FILE"
    sed -i "s|^OUTPUT_DIR=.*|OUTPUT_DIR=$OUTPUT_DIR|" "$ENV_FILE"
    chmod 640 "$ENV_FILE"
    chown root:"$SERVICE_USER" "$ENV_FILE"

    # ── 自动发现并注入 GEMINI_API_KEY ──────────────────────
    # 优先级: install 时传入的 env var > $SUDO_USER 的 ~/.env > 无 (留 warn)
    _gemini_key=""
    _gemini_src=""
    if [[ -n "${GEMINI_API_KEY:-}" ]]; then
        _gemini_key="$GEMINI_API_KEY"
        _gemini_src="env var"
    elif [[ -n "${SUDO_USER:-}" && "${SUDO_USER}" != "root" ]]; then
        _user_home=$(getent passwd "$SUDO_USER" | cut -d: -f6)
        if [[ -n "$_user_home" && -f "$_user_home/.env" ]]; then
            _gemini_key=$(grep -E '^GEMINI_API_KEY=' "$_user_home/.env" \
                          | head -1 | cut -d= -f2- \
                          | sed -e 's/^["'\'']//' -e 's/["'\'']$//')
            [[ -n "$_gemini_key" ]] && _gemini_src="$_user_home/.env"
        fi
    fi

    if [[ -n "$_gemini_key" ]]; then
        # key 字符仅含 [A-Za-z0-9_-]，| 作分隔符安全
        sed -i "s|^GEMINI_API_KEY=.*|GEMINI_API_KEY=$_gemini_key|" "$ENV_FILE"
        ok "已自动注入 GEMINI_API_KEY (来源: $_gemini_src)"
        warn "前提: 该 key 所属 GCP 项目需 enable billing — free tier 对 image 模型配额为 0"
    else
        warn "未检测到 GEMINI_API_KEY — 请手动编辑 $ENV_FILE 填入"
    fi

    # ── 把 install 时的代理变量持久化到 env ─────────────────
    # (install.sh 上面已 export HTTPS_PROXY/HTTP_PROXY/NO_PROXY；这里只是落盘)
    if [[ -n "$HTTPS_PROXY" ]]; then
        sed -i "s|^HTTPS_PROXY=.*|HTTPS_PROXY=$HTTPS_PROXY|" "$ENV_FILE"
        sed -i "s|^HTTP_PROXY=.*|HTTP_PROXY=${HTTP_PROXY:-$HTTPS_PROXY}|" "$ENV_FILE"
        [[ -n "${NO_PROXY:-}" ]] && sed -i "s|^NO_PROXY=.*|NO_PROXY=$NO_PROXY|" "$ENV_FILE"
        ok "已注入 HTTPS_PROXY / HTTP_PROXY / NO_PROXY"
    fi
else
    warn "$ENV_FILE 已存在, 未覆盖 (如需重置: rm $ENV_FILE 后重跑 install.sh)"
fi

SERVICE_FILE=/etc/systemd/system/typeset.service
# 把 typeset.service 中的占位路径替换为实际安装路径
sed \
    -e "s|/opt/typeset-native|$INSTALL_PREFIX|g" \
    -e "s|/etc/typeset/typeset.env|$ENV_FILE|g" \
    -e "s|/var/lib/typeset|$(dirname "$OUTPUT_DIR")|g" \
    -e "s|User=typeset|User=$SERVICE_USER|g" \
    -e "s|Group=typeset|Group=$SERVICE_USER|g" \
    "$SCRIPT_DIR/typeset.service" > "$SERVICE_FILE"

chown -R "$SERVICE_USER:$SERVICE_USER" "$INSTALL_PREFIX" "$OUTPUT_DIR"

systemctl daemon-reload

# 清理临时 apt 代理配置
rm -f /etc/apt/apt.conf.d/99typeset-proxy

ok "安装完成!"
cat <<EOF

═══════════════════════════════════════════════════════════
后续步骤:
  1. 检查 $ENV_FILE (GEMINI_API_KEY/代理是否已自动注入)
     非交互预填: GEMINI_API_KEY=AIza... sudo -E bash install.sh
     或在 \$SUDO_USER 的 ~/.env 里放 GEMINI_API_KEY=...
  2. systemctl enable --now typeset
  3. curl http://localhost:\${PORT:-9090}/health

升级 (代码层面):
  cd <repo>
  git pull origin deploy/native
  sudo -E bash deploy/native/install.sh   # 幂等, 会重新 rsync 源码

升级 (Chrome / 静态资源):
  sudo -E CHROME_RELEASE_TAG=native-v1.1 bash deploy/native/install.sh
═══════════════════════════════════════════════════════════
EOF
