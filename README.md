# hzr_mcp

运行于**极空间 NAS 上 office 容器**内的 MCP 服务，提供计算与 adb 能力，对应远端工程：  
https://remote-access-8929.zconnect.cn/ai/hzr_mcp

## 功能

- **calculator**：Python 表达式数学计算（math / random）
- **adb_devices**：列出当前 adb 已连接设备
- **adb_connect**：通过 WiFi（如飞鼠虚拟网 IP）连接 Android 设备
- **install_android_apk**：按人名从 `name_to_ip.json` 解析 IP，向对应手机安装 store 下的 APK

## 环境要求

- Python 3.10+
- 极空间 office 容器内已配置 Android SDK（`source /workspace/tools/env.sh` 或 `.bashrc` 已加载），`adb` 在 PATH 中

## tools 统一环境（JAVA / ADB / Python venv）

adb、Java 通过挂载 `office/tools` 使用；**Python 环境（含 python-miio）** 也可放在同一 `tools/` 下，使 **NAS 本机、office 容器、hzr_mcp 容器** 使用相同环境变量、指向同一目录。

- **tools 目录结构示例**：`tools/jdk-17`、`tools/android-sdk`、`tools/venv`（Python venv，含 `requirements.txt` 依赖）。
- **统一环境变量（一套放 office/tools）**：  
  - `tools/env-common.sh`：JAVA、ANDROID_HOME、ADB_PATH、venv 的 PATH（与 entrypoint 同逻辑）。  
  - `tools/env-host.sh`：供 NAS 本机 source，内部 source env-common.sh 并处理 adb 所需的 HOME。  
  NAS 本机只 source `env-host.sh`；office 容器 source `env-common.sh`；hzr_mcp 容器由 entrypoint 应用相同逻辑。  
  **上述两个脚本仅放在 NAS 的 `docker/office/tools/` 下维护，本仓库不包含。**
- **一次性创建 tools/venv**（在 NAS 上）：  
  `export TOOLS_DIR=/data_n003/data/udata/real/18510411307/docker/office/tools`  
  `./scripts/install-venv-to-tools.sh`  
  完成后 `tools/venv/bin` 下有 `python`、`miiocli` 等；hzr_mcp 容器若挂载该 tools，会优先使用此 venv。

详见 `scripts/install-venv-to-tools.sh`。

## 快速开始

1. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```

2. 运行（stdio，供 MCP 客户端调用）：
   ```bash
   python hzr_mcp.py
   ```

3. 配置人名与手机 IP：编辑 `name_to_ip.json`，或通过环境变量 `ANDROID_NAME_TO_IP` 传入 JSON 字符串。

## 小智 MCP 接入（长连接）

本仓库通过 **小智后台提供的 MCP 接入点**（WebSocket）保持长连接，由 **mcp_pipe** 将云端与小智的通信桥接到本地 stdio 版 hzr_mcp，与 only_branch_use 仓库下的 bbt_mcp 用法一致。

- **接入点示例**：`wss://api.xiaozhi.me/mcp/?token=<你的JWT>`
- **接入文档**：<https://my.feishu.cn/wiki/HiPEwZ37XiitnwktX13cEM5KnSb>

### 配置

1. 复制环境配置并填入小智 JWT：
   ```bash
   cp .env.example .env
   # 编辑 .env，设置 MCP_BASE_URL=wss://api.xiaozhi.me/mcp/ 与 MCP_TOKEN=你的JWT
   ```

2. 安装依赖（需包含 `websockets`、`python-dotenv`）：
   ```bash
   pip install -r requirements.txt
   ```

### 在 NAS 上常驻运行

**推荐：用 Docker 单独起一个容器**，隔离环境、重启策略统一（`restart: unless-stopped`），NAS 重启后也会自动拉起。  
容器内**不打包代码**，而是挂载你在 NAS 上从 GitLab clone 的工程目录；**每次启动/重启都会先放弃本地改动、拉取最新代码，再启动长连接**。

1. 在 NAS 上 clone 工程（若尚未 clone）：
   ```bash
   git clone <你的 NAS GitLab 上 hzr_mcp 的地址> /path/to/data/hzr_mcp
   cd /path/to/data/hzr_mcp
   ```
2. 复制编排并配置 token：
   ```bash
   cp docker-compose.example.yml docker-compose.yml
   cp .env.example .env
   # 编辑 .env：MCP_BASE_URL=wss://api.xiaozhi.me/mcp/ 与 MCP_TOKEN=你的JWT
   ```
3. 构建并后台运行（必须在 clone 出来的目录执行，以便挂载到容器 /app）：
   ```bash
   docker compose up -d
   docker compose logs -f   # 看日志确认已拉取最新并连上小智
   ```

如需指定拉取分支（默认 `main`），在 `docker-compose.yml` 中设置环境变量 `GIT_BRANCH=你的分支`。如需挂载 `name_to_ip.json` 等，在 `volumes` 中追加挂载即可。

---

也可在 NAS 上不用 Docker，直接跑进程：

- **直接运行**（前台）：`./scripts/run_mcp_pipe.sh` 或 `python mcp_pipe.py hzr_mcp.py`
- **后台常驻**：nohup / screen / systemd，例如  
  `nohup ./scripts/run_mcp_pipe.sh >> /tmp/hzr_mcp_pipe.log 2>&1 &`

mcp_pipe 会**自动重连**小智 WebSocket，断线后按指数退避重试，无需额外守护。

### 命令行覆盖 token

```bash
python mcp_pipe.py hzr_mcp.py -t 你的JWT
```

## 项目结构

- `hzr_mcp.py`：MCP 工具实现（stdio）
- `mcp_pipe.py`：小智 MCP 桥接（WebSocket ↔ stdio），与 bbt_mcp 同源
- `scripts/run_mcp_pipe.sh`：一键启动 mcp_pipe + hzr_mcp（供 NAS 常驻）
- `scripts/entrypoint.sh`：Docker 入口，每次启动时拉取最新代码再启动 mcp_pipe
- `mcp_config.json`：本地 stdio / mcp_pipe 所用配置
- `name_to_ip.json`：人名 → 手机 IP 映射（飞鼠/局域网 IP）
- `requirements.txt`：Python 依赖

## License

MIT
