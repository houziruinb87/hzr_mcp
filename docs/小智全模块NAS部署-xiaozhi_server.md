# 小智 Python 后台（xiaozhi-esp32-server）全模块 Docker 部署 - 极空间 NAS

已在你极空间 NAS 上按 **Docker Compose + FunASR** 部署小智全模块（智控台 + Server + MySQL + Redis）。

---

## 一、部署位置与结构

- **目录**：`/path/to/nas/udata/real/YOUR_USER_ID/docker/xiaozhi_server`
- **结构**：
  ```
  xiaozhi_server/
  ├── docker-compose.yml    # 全模块编排（MySQL/Redis 已改为国内镜像）
  ├── data/
  │   └── .config.yaml      # 从智控台拉配置，需填 server.secret
  ├── models/
  │   └── SenseVoiceSmall/
  │       └── model.pt      # FunASR 语音识别模型（已下载）
  ├── uploadfile/           # 智控台上传目录
  └── mysql/data/           # MySQL 数据
  ```

---

## 二、端口与访问

| 服务       | 端口   | 说明 |
|------------|--------|------|
| 智控台     | **18002** | 浏览器打开 `http://NAS的IP:18002`，注册、配置 LLM/TTS、参数管理（避免极空间限制 8002 远程访问） |
| WebSocket  | 8000   | 设备连接用：`ws://NAS的IP:8000/xiaozhi/v1/` |
| HTTP/视觉  | **18003** | 视觉分析等：`http://NAS的IP:18003` |

NAS 局域网 IP 示例：`192.168.1.100`。

---

## 三、首次启动后必做三件事

### 1. 等镜像拉取完成并启动

若 `docker compose up -d` 还在拉取 **xiaozhi-esp32-server-web**（约 3.2GB），请等其完成。在 NAS 上执行：

```bash
cd /path/to/nas/udata/real/YOUR_USER_ID/docker/xiaozhi_server
sg docker -c 'docker compose ps -a'
```

当 4 个容器（db、redis、web、server）均为 **Up** 后再做下面步骤。

### 2. 填好 server.secret（让 Server 连上智控台）

1. 浏览器打开 **http://192.168.1.100:18002**（将 IP 改为你 NAS 实际 IP）。
2. **注册第一个账号**，该账号为超级管理员。
3. 登录后进入 **【参数管理】**，找到参数编码 **`server.secret`**，复制其**参数值**。
4. 在 NAS 上编辑 `data/.config.yaml`，把 `manager-api.secret` 改成刚复制的值，并确认 `manager-api.url` 为：
   ```yaml
   manager-api:
     url: http://xiaozhi-esp32-server-web:8002/xiaozhi
     secret: 这里粘贴复制的server.secret值
   ```
5. 保存后重启 Server：
   ```bash
   sg docker -c 'docker restart xiaozhi-esp32-server'
   ```

### 3. 在智控台配置 LLM（如 Minimax）

- 进入 **【模型配置】** → **大语言模型**，添加或修改为你的 **Minimax**（或智谱等）API Key。
- 若用 Minimax，可选「OpenAI 兼容」类 LLM，base_url 填 `https://api.minimaxi.com/v1`，api_key 填你的 Key，详见 `docs/小智后端接入Minimax说明.md`。

### 4. 在智控台填写对外的 OTA / WebSocket 地址

- **参数管理** 中：
  - **server.ota**：`http://192.168.1.100:18002/xiaozhi/ota/`（改为你的 NAS IP）
  - **server.websocket**：`ws://192.168.1.100:8000/xiaozhi/v1/`（改为你的 NAS IP）

---

## 四、常用命令（在 NAS 上，进入 xiaozhi_server 目录后）

```bash
cd /path/to/nas/udata/real/YOUR_USER_ID/docker/xiaozhi_server

# 查看状态
sg docker -c 'docker compose ps -a'

# 查看 Server 日志（确认 Websocket 地址等）
sg docker -c 'docker logs -f xiaozhi-esp32-server'

# 查看智控台日志
sg docker -c 'docker logs -f xiaozhi-esp32-server-web'

# 重启
sg docker -c 'docker compose restart'

# 停止
sg docker -c 'docker compose down'

# 启动
sg docker -c 'docker compose up -d'
```

---

## 五、与 Open-XiaoAI 的衔接

- 小米音响 Pro 刷好 Open-XiaoAI 后，在设备端配置的 **WebSocket** 填：`ws://192.168.1.100:8000/xiaozhi/v1/`（或你 NAS 的 IP）。
- 若希望「小智同学」走自建小智后台、而「小爱同学」走原厂，则 Open-XiaoAI Server 的 `WEBSOCKET_URL` 需指向**本 NAS 上的小智**：`ws://NAS的IP:8000/xiaozhi/v1/`（具体以 Open-XiaoAI 文档为准）。

---

## 六、本仓库中的文件

- `docs/xiaozhi_server-docker-compose.yml`：Compose 模板（MySQL/Redis 已用国内镜像）。
- `docs/xiaozhi_server-data-config.yaml`：`data/.config.yaml` 模板（含 manager-api 与 vision_explain 占位）。

部署与首次配置按上述步骤即可；FunASR 模型已就绪，无需再下载。
