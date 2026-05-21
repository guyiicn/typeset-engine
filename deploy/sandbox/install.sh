#!/usr/bin/env bash
# typeset-engine 沙箱一键部署 v2 (无 sudo, 沙箱端在线装)
#
# POC 验证: 2026-05-21 in Jammy docker container
#   - miniforge 用户级装 OK
#   - conda 装 cairo/pango/harfbuzz/... C 库 OK
#   - pip 装 weasyprint=68.1 OK, cffi 真的 dlopen conda env 内的 libpango (find_library 验证)
#   - PDF 渲染 6679 bytes (test 字符串)
#
# 完整方案: 沙箱 (Ubuntu 22.04+, no sudo) 一条命令完成
#   curl -sL <this-script-url> | bash
#
# 使用方法:
#   bash install-sandbox-v2.sh [DEST]
#   默认 DEST=$HOME/typeset
#
# 启动:
#   GEMINI_API_KEY=AIza... PORT=9090 bash $DEST/start.sh

set -euo pipefail

DEST="${1:-$HOME/typeset}"
TYPESET_REPO="${TYPESET_REPO:-https://github.com/guyiicn/typeset-engine.git}"
TYPESET_BRANCH="${TYPESET_BRANCH:-master}"
MINIFORGE_URL="https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-x86_64.sh"
CHROME_URL="${CHROME_URL:-https://github.com/guyiicn/typeset-engine/releases/download/native-v1.0/chrome-linux64.tar.gz}"
TYPST_VERSION="${TYPST_VERSION:-v0.14.0}"
TYPST_URL="https://github.com/typst/typst/releases/download/${TYPST_VERSION}/typst-x86_64-unknown-linux-musl.tar.xz"

log()  { printf '\033[1;34m[*]\033[0m %s\n' "$*"; }
ok()   { printf '\033[1;32m[+]\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m[!]\033[0m %s\n' "$*"; }
die()  { printf '\033[1;31m[x]\033[0m %s\n' "$*" >&2; exit 1; }

# ─── 0. 预检 ───────────────────────────────────────────────────
[[ "$EUID" -ne 0 ]] || warn "你是 root, 这个脚本不需要 sudo, 用普通 user 跑更好"
command -v curl >/dev/null || die "curl 未安装. 沙箱无 sudo 不能 apt install — 找管理员"
command -v tar  >/dev/null || die "tar 未安装"

AVAIL_KB=$(df -k "$HOME" 2>/dev/null | awk 'NR==2 {print $4}')
[[ "$AVAIL_KB" -gt 2500000 ]] || warn "可用空间 < 2.5 GB ($AVAIL_KB KB), 装可能失败"

log "目标位置: $DEST"
mkdir -p "$DEST"

# ─── 1. miniforge 用户级安装 ──────────────────────────────────
if [[ -d "$DEST/miniforge3" ]]; then
    ok "miniforge 已存在, 跳过"
else
    log "1. 下载并安装 miniforge (用户级, 102 MB)"
    TMP=$(mktemp -d)
    curl -L --fail "$MINIFORGE_URL" -o "$TMP/miniforge.sh"
    bash "$TMP/miniforge.sh" -b -p "$DEST/miniforge3"
    rm -rf "$TMP"
fi
CONDA="$DEST/miniforge3/bin/conda"

# ─── 2. conda env 装 C 库 + Noto CJK 中文字体 ────────────────
if [[ -d "$DEST/miniforge3/envs/typeset" ]]; then
    ok "typeset env 已存在, 跳过 conda create"
else
    log "2. 创建 typeset env + 装 C 库 (cairo/pango/.../glib, 5-8 分钟)"
    "$CONDA" create -n typeset -y \
        python=3.12 \
        cairo pango harfbuzz fontconfig freetype gdk-pixbuf glib \
        cffi pillow lxml \
        librsvg ffmpeg \
        font-ttf-noto-cjk \
        binutils \
        2>&1 | tail -3
fi
ENV="$DEST/miniforge3/envs/typeset"
PIP="$ENV/bin/pip"
PYTHON="$ENV/bin/python"

# 已有 env 也确保字体装了 (幂等)
if ! "$ENV/bin/fc-list" 2>/dev/null | grep -qi "noto.*cjk\|noto serif cjk"; then
    log "2a. 补装 Noto CJK 字体 (中文必需, 否则 PDF 中文是方框)"
    "$CONDA" install -n typeset -y -c conda-forge font-ttf-noto-cjk 2>&1 | tail -3
fi

# ─── 3. pip 装 Python 包 ──────────────────────────────────────
log "3. pip 装 typeset-engine Python 依赖"
"$PIP" install --quiet \
    weasyprint==68.1 \
    plotly==6.7.0 kaleido==1.2.0 matplotlib==3.10.8 \
    python-pptx==1.0.2 python-docx==1.2.0 pypdf==6.10.2 \
    google-genai==1.73.1 python-dotenv markdown choreographer \
    2>&1 | tail -3
ok "pip install OK"

# ─── 4. typst 二进制 ───────────────────────────────────────────
if [[ -x "$ENV/bin/typst" ]]; then
    ok "typst 已存在: $($ENV/bin/typst --version)"
else
    log "4. 下载 typst $TYPST_VERSION (~30 MB)"
    TMP=$(mktemp -d)
    curl -L --fail "$TYPST_URL" -o "$TMP/typst.tar.xz"
    tar -xJf "$TMP/typst.tar.xz" -C "$TMP"
    cp "$TMP"/typst-*/typst "$ENV/bin/typst"
    chmod +x "$ENV/bin/typst"
    "$ENV/bin/typst" --version
    rm -rf "$TMP"
fi

# ─── 5. Chrome (kaleido 渲染图表) ──────────────────────────────
CHROME_DST="$ENV/lib/python3.12/site-packages/choreographer/cli/browser_exe"
if [[ -x "$CHROME_DST/chrome-linux64/chrome" ]]; then
    ok "Chrome 已存在: $CHROME_DST/chrome-linux64/chrome"
else
    log "5. 下载 Chrome native-v1.0 (148 MB)"
    mkdir -p "$CHROME_DST"
    curl -L --fail "$CHROME_URL" | tar xz -C "$CHROME_DST"
    [[ -x "$CHROME_DST/chrome-linux64/chrome" ]] || die "Chrome 解压失败"
fi

# ─── 5b. 注册仓库自带公文字体 (方正/SimHei/SimFang etc) ───────
# 在 git clone 之后做更顺序, 提前到这里防 PATH/fc-cache 顺序问题
# (clone 在 step 6, 字体注册放 step 5b 占位 — 实际由 step 6.5 完成)

# ─── 6. clone typeset-engine 代码 ─────────────────────────────
if [[ -d "$DEST/typeset-engine" ]]; then
    log "6. typeset-engine repo 已存在, git pull"
    (cd "$DEST/typeset-engine" && git pull --quiet origin "$TYPESET_BRANCH")
else
    log "6. clone typeset-engine"
    # 找 git: 系统级 OR conda env 内 OR 现装
    GIT_BIN=""
    if command -v git >/dev/null; then
        GIT_BIN=$(command -v git)
    elif [[ -x "$ENV/bin/git" ]]; then
        GIT_BIN="$ENV/bin/git"
    else
        log "  conda 装 git (沙箱无 git)"
        "$CONDA" install -n typeset -y -c conda-forge git 2>&1 | tail -1
        GIT_BIN="$ENV/bin/git"
    fi
    "$GIT_BIN" clone --depth 1 -b "$TYPESET_BRANCH" "$TYPESET_REPO" "$DEST/typeset-engine"
fi

# ─── 6.5. 装齐字体 (跟生产 sg2/us 对齐) ─────────────────────
# 三类来源:
#   (a) 仓库 fonts/ 公文字体 (方正小标宋/SimHei/SimFang/SimKai/SimSun/FZFS) - 直接拷贝
#   (b) Debian deb 提取 (AR PL UKai/UMing 楷体明体 + Liberation Serif/Sans/Mono)
#       — 沙箱无 sudo 不能 apt install, 从 Debian mirror 下 deb + ar/tar 解包
#   (c) Noto CJK 已经在 step 2 conda 装好
#
# 装完字体覆盖跟 sg2/us 完全对齐 (除 cwTeX, Debian sid 已废且模板不引用)
log "6.5. 装齐字体 (跟生产 sg2/us 对齐)"
FONT_DIR="$ENV/share/fonts/typeset"
mkdir -p "$FONT_DIR"

# (a) 仓库公文字体
cp -n "$DEST/typeset-engine/fonts/"*.{TTF,ttf,TTC,ttc,OTF,otf} "$FONT_DIR/" 2>/dev/null || true

# (b) Debian deb 字体 (arphic + liberation)
# ar (binutils) 在 conda env 已装 (step 2)
TMP=$(mktemp -d)
for url in \
    "http://ftp.debian.org/debian/pool/main/f/fonts-arphic-ukai/fonts-arphic-ukai_0.2.20080216.2-5_all.deb" \
    "http://ftp.debian.org/debian/pool/main/f/fonts-arphic-uming/fonts-arphic-uming_0.2.20080216.2-11_all.deb" \
    "http://ftp.debian.org/debian/pool/main/f/fonts-liberation/fonts-liberation_2.1.5-3_all.deb"; do
    name=$(basename "$url" | sed 's/_[^_]*_all.deb//')
    curl -sSL --fail "$url" -o "$TMP/$name.deb" || warn "$name.deb 下载失败, 跳过"
done
cd "$TMP"
for deb in *.deb; do
    [[ -f "$deb" ]] || continue
    name=$(basename "$deb" .deb)
    mkdir -p "$name"
    (cd "$name" && "$ENV/bin/ar" x "../$deb" && tar -xf data.tar.* 2>/dev/null)
done
find "$TMP" \( -name "*.ttf" -o -name "*.ttc" \) -exec cp -n {} "$FONT_DIR/" \;
cd "$DEST" && rm -rf "$TMP"

# fc-cache 注册
"$ENV/bin/fc-cache" -f "$ENV/share/fonts" 2>&1 | tail -2 || warn "fc-cache 失败"
FCNT=$("$ENV/bin/fc-list" | wc -l)
CNT_CJK=$("$ENV/bin/fc-list" | grep -ciE "cjk|noto|simhei|simsun|方正|ukai|uming")
ok "字体注册完成: 总 $FCNT, 含 CJK/中文 family $CNT_CJK"

# (b) 关键 family 不可少 - 必填硬检查
for fam in "Noto Sans CJK SC" "AR PL UKai CN" "Liberation Serif" "SimHei"; do
    "$ENV/bin/fc-list" | grep -q "$fam" || warn "  ⚠️ 字体未注册: $fam (跟生产对比缺少这个)"
done

# ─── 7. 生成 start.sh ──────────────────────────────────────────
cat > "$DEST/start.sh" <<EOF
#!/usr/bin/env bash
# typeset-engine 沙箱启动 (无 systemd)
set -e
DEST="\${DEST:-$DEST}"
ENV="\$DEST/miniforge3/envs/typeset"
PORT="\${PORT:-9090}"
OUTPUT_DIR="\${OUTPUT_DIR:-\$HOME/typeset-output}"
mkdir -p "\$OUTPUT_DIR"

# GEMINI key 兜底
if [[ -z "\${GEMINI_API_KEY:-}" && -f "\$HOME/.env" ]]; then
    export GEMINI_API_KEY=\$(grep '^GEMINI_API_KEY=' "\$HOME/.env" | cut -d= -f2-)
fi

cd "\$DEST/typeset-engine"
export PORT OUTPUT_DIR
export PATH="\$ENV/bin:\$PATH"
# typst 不读 fontconfig, 必须显式指字体路径 (含 Noto CJK + 公文方正)
export TYPST_FONT_PATHS="\$ENV/fonts:\$ENV/share/fonts"

if [[ "\${1:-}" == "--bg" ]]; then
    nohup "\$ENV/bin/python" scripts/server.py > "\$HOME/typeset.log" 2>&1 &
    echo "started PID \$!, log: \$HOME/typeset.log"
else
    exec "\$ENV/bin/python" scripts/server.py
fi
EOF
chmod +x "$DEST/start.sh"

# ─── 8. 烟雾测试 (含中文字体) ──────────────────────────────────
log "8. 自检: weasyprint import + 中文渲染"
"$PYTHON" <<'PY'
from weasyprint import HTML
HTML(string="<h1>沙箱部署 OK</h1><p>这是中文测试 — 如果字体注册成功, 看到的是真中文而不是方框.</p>").write_pdf("/tmp/install-smoke.pdf")
import os
print(f"  smoke PDF: {os.path.getsize('/tmp/install-smoke.pdf')} bytes (含中文)")
PY
ok "weasyprint 自检通过 (中文渲染走 Noto CJK)"

cat <<EOF

═══════════════════════════════════════════════════════════
✅ 部署完成 — 位置: $DEST

启动:
  # 前台 (Ctrl-C 退):
  GEMINI_API_KEY=AIza... PORT=9090 bash $DEST/start.sh

  # 后台:
  GEMINI_API_KEY=AIza... PORT=9090 bash $DEST/start.sh --bg
  # log: ~/typeset.log

验证:
  curl http://localhost:9090/health

升级代码 (master):
  cd $DEST/typeset-engine && git pull && systemctl restart typeset
  (沙箱无 systemd: pkill -f scripts/server.py && bash $DEST/start.sh --bg)

卸载 (全删):
  rm -rf $DEST ~/typeset-output ~/typeset.log

总占用: ~$(du -sh "$DEST" | cut -f1)
═══════════════════════════════════════════════════════════
EOF
