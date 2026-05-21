# Sandbox 部署 (无 sudo)

一条命令把 typeset-engine 部署到**没有 sudo 权限**的沙箱环境（普通 user / 不能
`apt install` / 不能写 `/opt` `/etc` / 不能创建 system user / 不能 systemd）。

POC 验证: Ubuntu 22.04 jammy + UID 9000 (non-root) docker 容器, 端到端跑通
全部 14 个 HTTP 端点 + 16 个 PDF 主题 + 14 个 Kami 模板 + 6 个 PPTX 主题.

详见: [`docs/sandbox-poc-results.md`](../../docs/sandbox-poc-results.md)

---

## 快速开始

```bash
# 沙箱端一条命令 (~10 分钟)
curl -sL https://raw.githubusercontent.com/guyiicn/typeset-engine/master/deploy/sandbox/install.sh \
    | bash -s $HOME/typeset

# 启动 (前台)
GEMINI_API_KEY=AIza... PORT=9090 bash $HOME/typeset/start.sh

# 启动 (后台)
GEMINI_API_KEY=AIza... PORT=9090 bash $HOME/typeset/start.sh --bg
# log: ~/typeset.log

# 验证
curl http://localhost:9090/health
```

## 跟 deploy/native/ 的区别

| 项 | `deploy/native/` (sudo 机器) | `deploy/sandbox/` (无 sudo) |
|---|---|---|
| Python 装 | `apt install python3-venv` + 系统 python | 用户级 `miniforge` (102 MB) |
| 系统 C 库 (libpango/libcairo) | `apt install libpango libcairo ...` | `conda install cairo pango ...` (self-contained 走 conda env 的 .so) |
| typst | release tarball + `/usr/local/bin` | release tarball + `$ENV/bin` |
| Chrome | release tarball + 系统 site-packages | release tarball + venv site-packages |
| 字体 | `apt install fonts-noto-cjk fonts-arphic-* fonts-liberation` | conda `font-ttf-noto-cjk` + Debian deb 提取 (ar 拆) |
| 进程管理 | systemd `typeset.service` | nohup + 用户级 `start.sh` |
| 部署位置 | `/opt/typeset-engine/` (root 拥) | `$HOME/typeset/` (普通 user) |
| GEMINI key | install.sh `$SUDO_USER` 的 `~/.env` 兜底 | 启动 `start.sh` 时显式 `export` 或 `~/.env` |

## 系统要求

- Ubuntu 22.04+ (Jammy) 或 Debian 12+ (bookworm) — glibc ≥ 2.35
- 普通 user，能读 `$HOME`，能 `curl https://github.com`
- 磁盘 ≥ 5 GB free (部署 ~3 GB + 输出预留)
- 不需要 sudo / root

## 装了什么

部署完 `$HOME/typeset/` 大概长这样：
```
$HOME/typeset/
├── miniforge3/                       # conda 用户级 (~700 MB)
│   ├── bin/conda
│   └── envs/typeset/                 # Python 3.12 venv
│       ├── bin/{python,typst,fc-cache,ar,...}
│       ├── lib/libpango-1.0.so.0     # ★ self-contained C 库 (无 sudo apt 装的关键)
│       ├── lib/libcairo.so.2
│       ├── fonts/                    # Noto CJK + DejaVu 等
│       └── share/fonts/typeset/      # 仓库公文方正字体 + Debian AR PL UKai/UMing + Liberation
├── typeset-engine/                   # git clone master (20 MB)
│   └── scripts/server.py
└── start.sh                          # 启动 helper
```

## 字体覆盖 (跟生产对齐)

| Family | 来源 | 用途 |
|---|---|---|
| Noto Sans/Serif/Mono CJK × 5 lang | `conda install font-ttf-noto-cjk` | 中文通用 fallback |
| AR PL UKai CN/HK/TW × 4 | Debian deb 提取 (ar + tar) | 楷体 (学术 kaiti) |
| AR PL UMing CN/HK/TW × 4 | Debian deb 提取 | 明体备选 |
| Liberation Serif/Sans/Mono | Debian deb 提取 | 英文 fallback baseline |
| 方正小标宋/SimHei/SimFang/SimKai/SimSun/FZFS | 仓库 `fonts/` | 公文专用 |

总 ~118 字体（比生产 sg2/us 69 多）。

## 已知坑 (脚本已绕过)

详见 `docs/sandbox-poc-results.md` 的 "关键发现". 简版:

- **typst 不读 fontconfig** → 启动必须 `export TYPST_FONT_PATHS=$ENV/fonts:$ENV/share/fonts`
- **学术 + 公文主题写 `TYPESET_ROOT/output`** → `TYPESET_ROOT/output` 必须可写
  (已在 commit `9631970` + `0c10207` 解决)
- **conda env Python 不能用 anaconda** → 沙箱无 anaconda 不是问题, 自带 miniforge

## 重新部署 / 升级

```bash
# 升级代码 (master 有新 commit)
cd ~/typeset/typeset-engine && git pull
pkill -f scripts/server.py
bash ~/typeset/start.sh --bg

# 完全重装
rm -rf ~/typeset ~/typeset-output ~/typeset.log
curl -sL https://raw.githubusercontent.com/.../deploy/sandbox/install.sh | bash
```
