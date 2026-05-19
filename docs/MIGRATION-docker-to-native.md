# 从 docker 迁到 native — 已部署 v1-v4 用户必读

**适用对象**：在 2026-05-19 之前 clone 过本仓库并跑过 `typeset-engine:v1` ~ `v4` 镜像
（`docker run` / `docker compose up` 等形式）的所有用户。

**起因**：2026-05-19 起 `master` 分支正式承载 native 部署（systemd + .venv），原 docker
路线（`Dockerfile` + `docker-compose.yaml`）已被归档到 `legacy-docker` 分支。任何在跑的
docker 容器还能继续用（镜像和容器不会被删），但**新的 fix / 新特性都只进 master**。

---

## TL;DR

```
1. 装 native (5 分钟):
   git pull origin master   # 拉新代码 (注: 你的本地分支可能叫 master 或 deploy/native, 都行)
   sudo -E GEMINI_API_KEY=$(grep '^GEMINI_API_KEY=' ~/.env | cut -d= -f2-) \
     bash deploy/native/install.sh
   sudo systemctl enable --now typeset
   curl http://localhost:9090/health     # 期望 {"status":"ok"...}

2. 切流量 + 停 docker (不删):
   # 把调用方 9091 改成 9090, 或保留 9091:
   sudo sed -i 's|^PORT=.*|PORT=9091|' /etc/typeset/typeset.env
   sudo systemctl restart typeset
   docker stop typeset-engine

3. 观察 1-3 天没问题再清理:
   docker rm typeset-engine
   docker rmi typeset-engine:v1 typeset-engine:v2 typeset-engine:v3 typeset-engine:v4
```

回退命令：`pkill -f scripts/server.py && docker start typeset-engine`

---

## 1. 谁该读 / 怎么识别你是 docker 用户

跑下面这条命令，看哪个有输出就走哪条路：

```bash
docker ps -a --filter name=typeset-engine
```

- **有输出（容器存在）** → 你是 docker 用户，继续往下读
- **空（容器不存在）** → 已经是 native 用户或没部署过，跳过本文档

---

## 2. 升级前盘点：你当前的 docker 部署是什么样

```bash
# 镜像版本
docker inspect typeset-engine --format '{{.Config.Image}}'
# 期望: typeset-engine:v1 / v2 / v3 / v4

# 端口映射 (一般是 9091:9090, 也有人改过)
docker port typeset-engine

# 环境变量 (GEMINI key 在哪)
docker inspect typeset-engine --format '{{json .Config.Env}}' | python3 -m json.tool | grep -i gemini

# 输出目录挂载 (一般是 /tmp/typeset-output)
docker inspect typeset-engine --format '{{json .Mounts}}' | python3 -m json.tool
```

把这些值记下来，第 4 步要复用。

---

## 3. 装 native（5-8 分钟）

### 3.1 拉最新代码

```bash
cd /path/to/typeset-engine
git fetch origin
git checkout master            # 如果你之前在 master 上, 强制同步: git reset --hard origin/master
git pull origin master
```

> ⚠️ 老 `master` 已经被覆写！如果你本地 `master` 有未推送的 docker 时代 commit，
> 它们现在在 `legacy-docker` 分支保留着，看 `git log origin/legacy-docker`。

### 3.2 跑 install.sh

`install.sh` 默认走 sudo，会装：
- 系统包（fontconfig / libpango / libcairo / rsvg-convert / ffmpeg 等 weasyprint+plotly 依赖）
- Python venv（`python3.10` 默认；用 `PYTHON_BIN=python3.13` 等覆盖）
- typst 0.14.0 二进制
- Chrome native-v1.0 tarball
- systemd unit + env 文件

```bash
# 最常见: 把现有 ~/.env 里的 GEMINI key 自动注入
sudo -E bash deploy/native/install.sh

# 或显式传入
sudo -E GEMINI_API_KEY=AIza... bash deploy/native/install.sh

# 需要代理 (内网部署)
sudo -E HTTPS_PROXY=http://x.y.z:p HTTP_PROXY=... \
  GEMINI_API_KEY=AIza... bash deploy/native/install.sh
```

> 🚨 **venv Python 版本坑**：如果系统装了 anaconda，**不要**让 install.sh 用 anaconda
> 的 python 创建 venv。anaconda 的 glib (2.78) 跟系统 libpango (1.56+) ABI 不兼容，
> 缺 `g_once_init_leave_pointer` symbol，weasyprint 起不来。强制用系统 Python：
> `sudo -E PYTHON_BIN=/usr/bin/python3.13 bash deploy/native/install.sh`

### 3.3 启动 + 验证

```bash
sudo systemctl enable --now typeset
sudo systemctl status typeset      # 应该 active (running)

# 端口 (默认 9090, 跟 docker 时代的 9091 不同!)
curl http://localhost:9090/health
# 期望: {"status":"ok","engine":"typeset-engine","version":"1.0"}

# 全端点
curl http://localhost:9090/capabilities
```

---

## 4. 配置迁移：把 docker 时代的设置复用过来

native 把所有运行配置放到 **`/etc/typeset/typeset.env`**（docker 时代是 `docker run -e`
或 `docker-compose.yaml`）。install.sh 会创建一份模板，你按下表对照填：

| docker 时代 | native | 备注 |
|---|---|---|
| `docker run -p 9091:9090` | `PORT=9091` | 想保持 9091 入口（**调用方零改动**），改 env 后 `systemctl restart typeset` |
| `docker run -e GEMINI_API_KEY=...` | `GEMINI_API_KEY=...` | install.sh 已自动从 `~/.env` 注入；老 docker 容器里的 env 用 `docker inspect` 拿出来填 |
| `docker run -e HTTPS_PROXY=...` | `HTTPS_PROXY=...` | install 时已 export 的代理会被持久化；如未 export 则手动填 |
| `-v /tmp/typeset-output:/app/output` | `OUTPUT_DIR=/var/lib/typeset/output` | native 默认 `/var/lib/typeset/output`；想继续用 `/tmp/typeset-output` 改 env |
| 自定义字体（`-v fonts:/app/fonts`） | 把字体放系统 `/usr/share/fonts/...` + `fc-cache -f` | native 共用系统字体；docker 时代 host 字体不一定生效 |
| 自定义模板（`-v templates:/app/templates`） | git 改 `templates/` 后 `git push` 或本地直接改 | native 直接读 `/opt/typeset-native/app/templates/` |

修完 env：
```bash
sudo systemctl restart typeset
curl http://localhost:9090/health   # 或 9091, 看你 PORT 改了没
```

---

## 5. 切流量

调用方（openclaw skill / 自动化 pipeline / agent）：

- **如果你 PORT 保持 9091**（接管 docker 旧端口）：调用方代码**零改动**，docker 停了就直接连到 native
- **如果你接受默认 9090**：调用方所有 `localhost:9091` 改成 `localhost:9090`

切完：
```bash
# 把 docker 容器 stop (不删, 留观察期)
docker stop typeset-engine
```

---

## 6. 端点 / 行为差异（关键变化）

**完全没变**：
- 所有 14 个端点（`/health`, `/capabilities`, `/styles`, `/fonts`, `/kami/templates`,
  `/kami/template/{}`, `/render/pdf`, `/render/docx`, `/render/pptx`, `/render/pptx-ai`,
  `/render/chart`, `/render/diagram`, `/render/illustrate`, `/render/kami`, `/validate/css`）
- 所有 JSON schema（含 PPTX 20 layout / kami 14 模板 / 4 PDF theme）
- 所有 GEMINI key 调用、weasyprint / typst / python-pptx 引擎逻辑

**变了的（仔细看一眼）**：
- 默认端口 **9090** vs docker 时代 **9091**（docker 内部一直 9090，host 映射 9091；
  native 直接绑 9090）
- 字体来源：docker 时代镜像内 `Source Han Serif SC / Noto Sans CJK SC` 是镜像里 ship 的；
  native 用宿主机 `fc-list` 看到的字体。如果宿主机没装中文字体会 fallback 出乱码 →
  `sudo apt install fonts-noto-cjk fonts-noto-cjk-extra`
- 进程身份：docker 时代是 root（容器内）；native 是 `typeset` 用户，
  `/var/lib/typeset/output` 必须可写

**新增的（仅 master/native 才有）**：
- `/render/kami` founders-playbook 数据驱动模式（commit `c6fdf55`）
- `/render/kami` slots 支持中文 key（commit `d9c91c1`，老 docker 镜像里是 ASCII-only bug）
- 20 layout 完整 PPTX schema + 单元测试（commit `98dcdb2`）
- 4 个 long-doc 变体（long-doc-claude / openai / starwars + founders-playbook）

---

## 7. 故障排查

### 7.1 `weasyprint` 起不来报 glib symbol missing

```
OSError: cannot load library 'libpango-1.0-0': ... undefined symbol: g_once_init_leave_pointer
```

→ venv Python 链接到 anaconda 旧 glib 了。**重建 venv 用系统 Python**：

```bash
sudo rm -rf /opt/typeset-native/.venv
sudo -E PYTHON_BIN=/usr/bin/python3.13 bash deploy/native/install.sh
```

### 7.2 `/render/illustrate` 返回 429 RESOURCE_EXHAUSTED

GEMINI key 的项目对 image 模型 free tier 配额 = 0，**必须 billing-enabled** 项目的 key。
报错里 model 名显示 `gemini-2.5-flash-preview-image` 是 Google 服务端计费名，跟代码里
实际传的 `gemini-2.5-flash-image` 不同，**别改代码**。

### 7.3 PPTX `ZeroDivisionError: cols=0`

调用方把 `table` layout 写成嵌套对象 `{"table": {"headers":..., "rows":...}}` 了 →
必须把 `headers` 和 `rows` 直接放 slide 顶层。详见 `scripts/render_pptx.py` docstring。

### 7.4 端口被占

```bash
sudo ss -tlnp | grep :9090
# 如果是 docker-proxy 占着, 先 docker stop
docker stop typeset-engine
sudo systemctl restart typeset
```

### 7.5 想看老 master (docker 时代) 的代码

```bash
git fetch origin
git log origin/legacy-docker --oneline   # 老 master 备份在这里
git show origin/legacy-docker:Dockerfile  # 看老 Dockerfile
```

---

## 8. 回退方案（native 这 1-3 天有问题）

docker 容器和镜像没被 install.sh 动过，**随时可以切回**：

```bash
# 停 native
sudo systemctl stop typeset
sudo systemctl disable typeset

# 起回 docker
docker start typeset-engine
curl http://localhost:9091/health   # 老端口

# 调用方端口改回 9091
```

回退后回头排查 native 问题 → 提 issue：https://github.com/guyiicn/typeset-engine/issues

---

## 9. 删 docker 资产（确认 native 稳定后）

```bash
# 容器
docker rm typeset-engine

# 4 个版本镜像 (释放 ~10GB)
docker rmi typeset-engine:v1 typeset-engine:v2 typeset-engine:v3 typeset-engine:v4

# 如果你还在用 docker-compose
docker compose down --rmi all
```

---

## 10. legacy-docker 分支的角色

```
git checkout legacy-docker    # 看老 master 的所有 docker 时代 commit
```

`legacy-docker` 是 force push 前的 master 备份，包含：
- `Dockerfile` (原镜像 build 脚本)
- `docker-compose.yaml` (bind-mount 过渡方案)
- 5 个独有 commit（含 docker `python:3.12-slim` 自包含基镜像、内置 typeset skill 等）

**不会再有新 commit 进 legacy-docker**。仅用于历史查阅 / 紧急复用 Dockerfile。

---

**问题反馈**：https://github.com/guyiicn/typeset-engine/issues
**主文档**：[`README.md`](../README.md) · [`USAGE.md`](../USAGE.md) · [`deploy/native/README.md`](../deploy/native/README.md)
