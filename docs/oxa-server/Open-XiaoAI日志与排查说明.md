# Open-XiaoAI 日志与排查说明

当前使用的是**官方预构建镜像** `idootop/open-xiaoai-xiaozhi:latest`，无法修改其内部代码，因此**没有像自建小智那样可加的“详细日志”**。只能通过以下方式尽量利用现有输出做排查。

## 一、已做的改进（尽量看到更多输出）

在 **docker-compose** 里为 Open-XiaoAI 服务增加了环境变量：

- **`PYTHONUNBUFFERED=1`**  
  让容器内 Python 的 stdout/stderr 不缓冲，`print` 或默认日志会尽快出现在 `docker logs` 里，便于实时看连接、OTA、错误等信息。

若你是在 NAS 上单独维护一份 compose，请在该服务的 `environment` 中同样加上：

```yaml
environment:
  - CLI=true
  - PYTHONUNBUFFERED=1
```

然后重启容器：`docker compose up -d open-xiaoai-xiaozhi`（或在 NAS 上你实际使用的重启方式）。

### 在 NAS 上确认是否已开启（请你在 NAS SSH 或终端执行）

**① 看当前容器有没有这个环境变量：**

```bash
docker inspect open-xiaoai-xiaozhi --format '{{range .Config.Env}}{{println .}}{{end}}' | grep -E 'PYTHONUNBUFFERED|CLI'
```

- 若出现 `PYTHONUNBUFFERED=1`，说明已开启，无需改。
- 若没有，需要改 compose 并重启，按下面 ②③ 做。

**② 找到 Open-XiaoAI 的 compose 所在目录（常见是 `Open-XiaoAI-Server`）：**

```bash
# 假设在 /data_n003/.../docker/ 下，按你实际 NAS 路径改
cd /path/to/nas/udata/real/YOUR_USER_ID/docker/Open-XiaoAI-Server
# 或你实际放 docker-compose 的目录
cat docker-compose.yml
```

在 `open-xiaoai-xiaozhi` 的 `environment:` 里加一行 `- PYTHONUNBUFFERED=1`（与 `CLI=true` 并列），保存。

**③ 重启使生效：**

```bash
docker compose up -d open-xiaoai-xiaozhi
```

再执行 ① 确认出现 `PYTHONUNBUFFERED=1`。

## 二、如何看 Open-XiaoAI 的日志

在 NAS 上（或运行 Open-XiaoAI 的机器上）执行：

```bash
# 最近 100 行
docker logs open-xiaoai-xiaozhi --tail 100

# 实时跟踪（排查时常用）
docker logs -f open-xiaoai-xiaozhi
```

关注：

- 启动是否报错（如 config 加载失败、端口占用）。
- 官方示例文档提到：**验证码** 会在终端打印，或写入 `config.py` 的 `VERIFICATION_INFO`，可在日志或挂载的 `config.py` 里查找。
- 若有连小智、OTA、WebSocket 等提示，可辅助判断是否在尝试连自建小智。

**注意**：镜像内部没有我们加的 `[小智]` 这类统一前缀，输出格式和内容完全由官方实现决定，可能不多，也可能几乎没有。

## 三、为什么主要仍靠「小智 server 日志」定位？

因为：

1. **Open-XiaoAI 是客户端**：它去连 OTA 和 WebSocket；是否“真的连上”只有在**服务端（自建小智）**看到连接和请求才能确认。
2. **自建小智已加详细日志**：我们在小智 server 里加了带 `[小智]` 的日志（OTA GET/POST、WebSocket 新连接、收到文本/音频、断开等），能明确看到“有没有请求进来、是谁连的”。

所以：

- **若小智日志里没有 OTA POST / 没有新 WebSocket 连接**  
  → 说明 Open-XiaoAI 没有成功连到自建小智（或连错地址），应检查：
  - Open-XiaoAI 的 `config.py` 里 `OTA_URL`、`WEBSOCKET_URL` 是否指向自建小智（如 `http://NAS:18002/xiaozhi/ota/`、`ws://NAS:8000/xiaozhi/v1/`），
  - 以及 Open-XiaoAI 容器到 NAS 的网络是否通。
- **若小智日志里已有连接和消息**  
  → 问题多半在设备绑定、LLM/TTS 或小智业务逻辑，可继续查小智的 ERROR 日志和智控台配置。

结论：**Open-XiaoAI 这边没有更多“详细日志”可开，定位时以「小智 server 的 `[小智]` 日志」为主，Open-XiaoAI 的 `docker logs` 为辅。** 详见：[小智详细日志说明与问题定位.md](./小智详细日志说明与问题定位.md)。

## 四、若需要更细的 Open-XiaoAI 端日志

只能从**源码本地运行**并自行加日志：

1. 克隆官方仓库：  
   `git clone https://github.com/idootop/open-xiaoai.git`  
   进入 `examples/xiaozhi`。
2. 按官方 README 用 `uv` 安装依赖，在 `main.py` 或连 OTA/WebSocket 的代码里加 `print()` 或 `logging`，然后：
   - 本地：`CLI=true uv run main.py`
   - 或自己构建 Docker 镜像，用带日志的镜像替代官方 `open-xiaoai-xiaozhi`。

这样就不依赖官方镜像，可以随意加详细日志；日常排查仍建议以小智 server 日志为主。
