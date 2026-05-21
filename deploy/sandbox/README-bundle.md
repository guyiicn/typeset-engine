# typeset-engine 沙箱离线 bundle (deploy/sandbox 路径之二)

> 跟 `install.sh` (online 一键, 沙箱端联网拉 conda-forge) 并列的另一条沙箱部署路径:
> **离线 bundle** — build host 一次打包, 跨网中转, 沙箱端 0 联网解压即用.
> 适用: 沙箱**不能直接访问 conda-forge / GitHub** 但能下公司文件服务器的场景.

为**无 SSH 沙箱**准备的完整离线部署包. 你下载到中转文件服务器后, 沙箱端用
`curl` / `wget` 拉这 3 个文件到同一目录, 跑 `bash install-from-bundle.sh` 即可.

## 重建 bundle (开发者用)

在跑过 `install.sh` (online 版) 的 build host 上:

```bash
bash deploy/sandbox/build-bundle.sh
# 默认输出到 /tmp/sandbox-bundle/, 4 个文件
```

详见 [`build-bundle.sh`](build-bundle.sh) 顶部注释.

---

## bundle 内容 (3 个文件)

| 文件 | 大小 | 内容 |
|---|---|---|
| `typeset-env.tar.gz` | **947 MB** | conda-pack 的完整 Python env — 含 Python 3.12, weasyprint 68.1, cairo/pango/.../glib C 库 (self-contained, **无需 sudo apt**), Noto CJK + AR PL UKai/UMing + Liberation + 公文方正字体, typst 0.14, Chrome (kaleido), python-pptx/docx/pypdf/google-genai/... |
| `typeset-engine-code.tar.gz` | **40 MB** | typeset-engine master HEAD `f8323d3` git archive — 含 scripts/templates/styles/fonts/skill/tests |
| `install-from-bundle.sh` | ~6 KB | 沙箱端一键脚本: 解压 → conda-unpack 修 prefix → 生成 start.sh → 自检 |

**总下载量**: 约 **990 MB**

## 在中转文件服务器准备

把这 3 个文件上传到任意 HTTPS / SFTP / 公司内网文件服务器, 用户能 `curl` 或 `wget`
访问即可. 例如:

```
https://your-fileserver.com/typeset-bundle/
    ├── typeset-env.tar.gz
    ├── typeset-engine-code.tar.gz
    └── install-from-bundle.sh
```

## 沙箱端部署 (无 sudo, 无 SSH from outside)

```bash
# 1. 进沙箱 (你 hand-off, 不是我 ssh)
# 2. 在沙箱里建 bundle 目录, 下 3 个文件:
mkdir -p ~/bundle && cd ~/bundle
curl -O https://your-fileserver.com/typeset-bundle/typeset-env.tar.gz
curl -O https://your-fileserver.com/typeset-bundle/typeset-engine-code.tar.gz
curl -O https://your-fileserver.com/typeset-bundle/install-from-bundle.sh

# 3. 跑 install
bash install-from-bundle.sh
# 默认装到 ~/typeset/, 自定义: bash install-from-bundle.sh /custom/dest

# 4. 启动 (前台)
GEMINI_API_KEY=AIza... PORT=9090 bash ~/typeset/start.sh

# 4. 启动 (后台)
GEMINI_API_KEY=AIza... PORT=9090 bash ~/typeset/start.sh --bg
# log: ~/typeset.log

# 5. 验证
curl http://localhost:9090/health
curl http://localhost:9090/capabilities
```

## 系统要求

- Ubuntu 22.04+ / Debian 12+ (glibc ≥ 2.35) — bundle build 时验证过 Jammy
- 磁盘 ≥ **4 GB free** (947 MB tarball + 解压后 ~3 GB env + ~50 MB code)
- 普通 user 即可 (无 sudo / root 需求)
- 沙箱 inbound 通：能 `curl` 你的文件服务器
- 沙箱 outbound 通：调 GEMINI API 需要能访问 `generativelanguage.googleapis.com`

## 这 bundle build 自哪里

- **build 时间**: 2026-05-21
- **build 平台**: Ubuntu 22.04 (Jammy) docker container, UID 9000 non-sudo
- **代码版本**: master HEAD `f8323d3`
- **conda env**: Python 3.12.x, weasyprint 68.1, typst 0.14.0, Chrome native-v1.0
- **字体覆盖**: 跟生产 sg2/us native 部署一致 + Noto CJK 全套 (118 字体)

## 跟生产 native (sg2/us) 比

| 项 | sg2/us 生产 | 沙箱 bundle |
|---|---|---|
| 部署位置 | `/opt/typeset-engine/` | `$HOME/typeset/` (普通 user) |
| C 库 | apt 装系统包 | conda-forge self-contained |
| 进程管理 | systemd typeset.service | nohup + start.sh |
| 端口 | 9090 / 9091 | 9090 (可改) |
| 端点数 | 14 (含 pdf-md/docx-md/kami/validate-css) | 14 (一样) |
| PDF 主题 | 16 (cicc/ms/cms/dachen/cn-paper/gongwen/...) | 16 (一样) |
| Kami 模板 | 14 (founders-playbook / long-doc-starwars / ...) | 14 (一样) |
| PPTX 主题 | 6 | 6 |
| 字体 family 数 | 69 | 118 (沙箱反而多, 因 conda font-ttf-noto-cjk 含全 CJK 变体) |

## 注意 / 已知坑 (沙箱专属)

- typst 不读 fontconfig — `start.sh` 必须 export `TYPST_FONT_PATHS`. 已自动配置.
- conda env 内 Python shebang 是 hardcoded prefix, 解压后**必须**跑 `conda-unpack`
  才能修正. install-from-bundle.sh 自动跑.
- bundle 跨发行版兼容 glibc ≥ 2.35 (Jammy build). 如果你沙箱是更老的 Focal (2.31)
  或 CentOS 7 (2.17), 部分包可能 segfault. 出问题告诉我, 重 build.

## 升级代码 (master 有新 commit, 不重 build env)

```bash
# 沙箱端
cd ~/typeset/typeset-engine
# 把新版 typeset-engine-code.tar.gz 下到 ~/bundle/
rm -rf scripts templates skill tests fonts docs deploy
tar -xzf ~/bundle/typeset-engine-code.tar.gz --strip-components=1
# 重启
pkill -f scripts/server.py
bash ~/typeset/start.sh --bg
```

或者直接 `git pull` 如果沙箱能访问 github.com.

## bundle 重建

如果代码 / env 有大变, 在 build host 上跑:

```bash
docker exec -u 9000 typeset-sandbox-poc \
  /sandbox-home/typeset/miniforge3/bin/conda-pack \
  -p /sandbox-home/typeset/miniforge3/envs/typeset \
  -o /sandbox-home/typeset-env.tar.gz \
  --ignore-missing-files

cd ~/clawd/code/typeset-engine
git archive --format=tar.gz --prefix=typeset-engine/ HEAD \
  -o /tmp/sandbox-bundle/typeset-engine-code.tar.gz
```
