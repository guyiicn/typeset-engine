# typeset-engine 非 Docker 部署 (native)

把 `typeset-engine` 部署到一台没有 Docker 的 Debian/Ubuntu x86_64 机器上, 走 GitHub 同步。

源 Docker 镜像: `typeset-engine:v4` (2.42 GB, 基于 `finrobot:v2`)
本部署: ~1 GB 安装后 (apt 字体 ~600 MB + venv ~350 MB + Chrome ~350 MB)

---

## 分支与版本

| 资源 | 位置 |
|------|------|
| 代码 | 本仓库 `deploy/native` 分支 (目标机始终拉这条分支, 不合并 master) |
| Chrome 二进制 | GitHub Release [`native-v1.0`](https://github.com/guyiicn/typeset-engine/releases/tag/native-v1.0) 附件 `chrome-linux64.tar.gz` (148 MB) |
| typst 二进制 | 上游 [`typst/typst@v0.14.0`](https://github.com/typst/typst/releases/tag/v0.14.0) |

> 升级 Chrome / 静态资源会发布新的 `native-v1.x` tag, 升级方式见末尾。

---

## 目标机环境要求

| 项 | 要求 |
|----|------|
| 系统 | Debian 11/12, Ubuntu 22.04/24.04 (x86_64) |
| Python | 3.10 (install.sh 通过 apt 安装) |
| 权限 | root (apt + systemctl) |
| 磁盘 | ≥ 2 GB |
| 网络 | 可通过代理访问 deb 源 / PyPI / github.com / generativelanguage.googleapis.com |

---

## 部署流程 (给目标机 agent)

### 1. 克隆分支

```bash
git clone -b deploy/native --depth 1 https://github.com/guyiicn/typeset-engine.git
cd typeset-engine/deploy/native
```

### 2. 配置代理 (内网必填)

```bash
export HTTPS_PROXY=http://your-proxy:port
export HTTP_PROXY=http://your-proxy:port
export NO_PROXY=localhost,127.0.0.1
```

`install.sh` 自动用这些变量配置 apt、pip、curl。

### 3. 运行安装

```bash
sudo -E bash install.sh
```

`-E` 透传代理变量给 sudo。脚本会:

| 阶段 | 内容 |
|------|------|
| 1 | apt 装 Python 3.10、CJK 字体、PDF/图像/视频工具、Chrome 系统库 |
| 2 | 建 `typeset` 用户、`rsync` 源码到 `/opt/typeset-native/app/`、建 venv、`pip install -r requirements.txt` |
| 3 | 下载 typst v0.14.0 到 `/usr/local/bin/typst` |
| 4 | 从本仓库 Release `native-v1.0` 下载 `chrome-linux64.tar.gz`, sha256 校验, 解压到 choreographer 路径 |
| 5 | `fc-cache` 注册字体, matplotlib 字体缓存预热 |
| 末 | 写 `/etc/typeset/typeset.env` 和 `/etc/systemd/system/typeset.service` |

### 4. 填 secrets

```bash
sudo $EDITOR /etc/typeset/typeset.env
```

至少填:
```
GEMINI_API_KEY=AIza...    # AI PPT / AI 配图需要
HTTPS_PROXY=http://...    # Gemini API 走代理
HTTP_PROXY=http://...
```

### 5. 启动服务

```bash
sudo systemctl enable --now typeset
sudo systemctl status typeset
sudo journalctl -u typeset -f
```

### 6. 健康检查

```bash
curl http://localhost:9090/health
# 期望: {"status": "ok", "engine": "typeset-engine", "version": "1.0"}

curl http://localhost:9090/capabilities | python3 -m json.tool
```

---

## 可调参数 (install.sh 环境变量)

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `INSTALL_PREFIX` | `/opt/typeset-native` | 部署根目录 |
| `OUTPUT_DIR` | `/var/lib/typeset/output` | 生成文件输出目录 |
| `SERVICE_USER` | `typeset` | 服务运行用户 |
| `ENV_FILE` | `/etc/typeset/typeset.env` | 环境变量文件路径 |
| `PORT` | `9090` (env 文件) | HTTP 监听端口 |
| `TYPST_VERSION` | `v0.14.0` | typst 上游版本 |
| `CHROME_RELEASE_TAG` | `native-v1.0` | 本仓库 Chrome release tag |
| `CHROME_SHA256` | (硬编码) | sha256 校验值 |
| `PYTHON_BIN` | `python3.10` | Python 解释器 |

示例:

```bash
sudo -E OUTPUT_DIR=/data/typeset/out PORT=9090 bash install.sh
```

⚠️ **OUTPUT_DIR 是调用方契约**: 上层 SKILL.md 默认写 `/tmp/typeset-output/`。如改成别的, 调用方 (Claude / agent) 那边必须同步改, 否则它读不到生成的文件。

---

## 4 个核心接口快速验证

### PDF 报告 (typst 链路)

```bash
cat > /tmp/test.json <<'EOF'
{
  "title": "测试报告", "theme": "cicc",
  "sections": [{"type": "heading", "title": "概述", "content": "测试"}]
}
EOF
curl -X POST http://localhost:9090/render/pdf \
  -H "Content-Type: application/json" -d @/tmp/test.json -o /tmp/test.pdf
file /tmp/test.pdf
```

### 图表 (Chrome + plotly 链路)

```bash
curl -X POST http://localhost:9090/render/chart \
  -H "Content-Type: application/json" \
  -d '{"type":"bar","data":{"title":"t","categories":["A","B"],"series":[{"name":"x","values":[1,2]}]}}' \
  -o /tmp/chart.png
file /tmp/chart.png
```

### 技术架构图 (librsvg 链路)

```bash
curl -X POST http://localhost:9090/render/diagram \
  -H "Content-Type: application/json" \
  -d '{"svg":"<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 100 100\"><rect width=\"100\" height=\"100\" fill=\"red\"/></svg>","width":200}' \
  -o /tmp/diagram.png
```

### AI 配图 (Gemini + 代理出网验证)

```bash
curl -X POST http://localhost:9090/render/illustrate \
  -H "Content-Type: application/json" \
  -d '{"content":"一只猫坐在窗台上","style":"ticket"}' \
  -o /tmp/cat.png
```

---

## 升级方式

### 代码升级 (常见)

```bash
cd typeset-engine
git pull origin deploy/native
sudo -E bash deploy/native/install.sh
```

`install.sh` 幂等, 每次跑会重新 rsync 源码 + 重装 pip 依赖, 但已存在的 typst / Chrome 会跳过下载。

### Chrome / 静态资源升级

发新 release tag `native-v1.1` 后:

```bash
sudo -E CHROME_RELEASE_TAG=native-v1.1 CHROME_SHA256=<新值> bash deploy/native/install.sh
```

或编辑 `install.sh` 顶部默认值后提交到 `deploy/native` 分支。

### 单次重启

```bash
sudo systemctl restart typeset
```

---

## 故障排查

| 症状 | 原因 | 解法 |
|------|------|------|
| `Failed to connect localhost:9090` | 服务没起 | `systemctl status typeset` + `journalctl -u typeset -n 50` |
| PDF 中文乱码 | 字体没注册 | `fc-list :lang=zh \| head` 确认 Noto CJK 存在; 重跑 `fc-cache -fv` |
| `/render/chart` 报 chrome 找不到 | choreographer 找不到 chrome | 检查 `/opt/typeset-native/.venv/lib/python3.10/site-packages/choreographer/cli/browser_exe/chrome-linux64/chrome` 存在且可执行 |
| chrome sha256 不匹配 | release 资源被替换或下载损坏 | 重新跑 install.sh; 或 `CHROME_SHA256=` 留空跳过校验 |
| `/render/illustrate` 超时 | Gemini 不可达 | `curl -x $HTTPS_PROXY https://generativelanguage.googleapis.com` 测试 |
| `typst: command not found` | 二进制下载失败 | `ls /usr/local/bin/typst`; 手动下载 https://github.com/typst/typst/releases/tag/v0.14.0 |
| OUTPUT_DIR 写权限报错 | systemd `ReadWritePaths` 限制 | 检查 `typeset.service` 中 `ReadWritePaths` 与 OUTPUT_DIR 父目录一致 |
| apt 装包卡住 | 代理未传给 sudo | 用 `sudo -E` 不要用 `sudo` |
| pip 装 weasyprint 报 cairo 错 | libcairo2 没装 | install.sh 已含; 手工补 `apt install libcairo2 libpango-1.0-0` |

---

## 与 Docker 镜像的差异

| 项 | Docker `typeset-engine:v4` | 本部署 |
|----|---------------------------|--------|
| 体积 | 2.42 GB | ~1 GB 安装后 |
| 含 finrobot/金融分析 | 是 | **否** — server.py 不依赖, 已剔除 |
| Chrome 来源 | `plotly_get_chrome` 在线装 | 本仓库 Release 离线 tarball |
| wkhtmltopdf | 装了但未使用 | 不装 |
| `GEMINI_API_KEY` 硬编码 | **是** (镜像 ENV, 安全风险) | **否** — env file |
| 启动 | `python scripts/server.py` (CMD) | systemd `ExecStart` 等价 |

---

## 文件清单 (deploy/native/)

```
deploy/native/
├── README.md            本文档
├── install.sh           5 阶段部署脚本 (幂等)
├── requirements.txt     13 个 Python 包 (无 finrobot)
├── env.example          环境变量模板
└── typeset.service      systemd 单元模板
```

源码不在本目录, 由 `install.sh` 从仓库根目录 (`../..`) rsync 过去。
