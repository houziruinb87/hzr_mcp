# NAS（极空间）上从源码运行 Open-XiaoAI（带 [OXA] 日志）

## 一、已完成的步骤

1. **已停掉** 原 `open-xiaoai-xiaozhi` 容器。
2. **已清空** `Open-XiaoAI-Server` 目录。
3. **已在 Mac 上 clone 源码** 并 **rsync 到 NAS** 的 `Open-XiaoAI-Server`，目录内已是完整仓库且包含：
   - 带 **`[OXA]`** 关键日志的修改（`xiaozhi/utils/config.py`、`websocket_protocol.py`、`xiaozhi.py`、`event.py`）；
   - 你的自建小智 **config**（`examples/xiaozhi/config.py`，OTA_URL / WEBSOCKET_URL 指向 192.168.1.100）。

当前 NAS 上路径为：

- 仓库根目录：`/path/to/nas/udata/real/YOUR_USER_ID/docker/Open-XiaoAI-Server/`
- xiaozhi 示例：`Open-XiaoAI-Server/examples/xiaozhi/`

## 二、在 NAS 上“编译运行”的两种方式

### 方式 A：Docker 从源码构建镜像后运行（推荐）

需要 NAS 能访问外网拉取 `python:3.12-slim` 等基础镜像；若拉取超时，可在一台能拉镜像的机器上构建并导出镜像，再在 NAS 上加载。

**在 NAS 上执行（能正常拉镜像时）：**

```bash
cd /path/to/nas/udata/real/YOUR_USER_ID/docker/Open-XiaoAI-Server
docker build -f examples/xiaozhi/Dockerfile -t open-xiaoai-xiaozhi:source .
```

构建成功后运行（端口 4399，挂载当前 config）：

```bash
docker run -d --name open-xiaoai-xiaozhi --restart unless-stopped \
  -p 4399:4399 \
  -v /path/to/nas/udata/real/YOUR_USER_ID/docker/Open-XiaoAI-Server/examples/xiaozhi/config.py:/app/config.py \
  -e CLI=true \
  open-xiaoai-xiaozhi:source
```

查看带 `[OXA]` 的日志：

```bash
docker logs -f open-xiaoai-xiaozhi 2>&1 | grep OXA
```

**若 NAS 拉镜像超时**，可在有 Docker 且能访问外网的电脑上：

```bash
# 1. 构建（在仓库根目录）
docker build -f examples/xiaozhi/Dockerfile -t open-xiaoai-xiaozhi:source .
# 2. 导出
docker save open-xiaoai-xiaozhi:source -o open-xiaoai-xiaozhi-source.tar
# 3. 拷到 NAS 后，在 NAS 上：
docker load -i open-xiaoai-xiaozhi-source.tar
# 再执行上面的 docker run
```

### 方式 B：不用 Docker，直接在 NAS 上 uv 运行（需 Python 3.12 + uv + Rust）

项目要求 **Python ≥3.12**，且需 **Rust** 编译扩展。若 NAS 只有 Python 3.10，需先安装 Python 3.12 和 uv、Rust，再在 `examples/xiaozhi` 下执行：

```bash
cd /path/to/nas/udata/real/YOUR_USER_ID/docker/Open-XiaoAI-Server/examples/xiaozhi
uv sync --locked
CLI=true uv run main.py
```

日志中带 `[OXA]` 的即为关键排查输出。若系统没有 Python 3.12 或 Rust，建议用方式 A。

## 三、复现“唤醒 → 追问”并看 [OXA] 日志

1. 启动服务（Docker 或 uv 二选一）。
2. 音箱连到 NAS 的 4399（或本机测试时直接连本机）。
3. 说「你好小智同学」→ 再说「天气如何」。
4. 在 NAS 上执行（Docker 时）：
   ```bash
   docker logs open-xiaoai-xiaozhi --tail 200 2>&1 | grep OXA
   ```
   关注：是否出现「小智 WebSocket 准备连接」「连接成功」或「send_audio 跳过」「有音频但未发送」等，用于判断是否连上自建小智、是否在发音频。

## 四、恢复为原 Docker 镜像运行

若之后想恢复为官方镜像、不再用源码版：

```bash
docker stop open-xiaoai-xiaozhi
docker rm open-xiaoai-xiaozhi
# 在原先的 Open-XiaoAI-Server 目录放回 docker-compose.yml 和 config.py，再：
docker compose up -d open-xiaoai-xiaozhi
```

当前 NAS 上 `Open-XiaoAI-Server` 已是完整源码（含 [OXA] 日志与你的 config），按上面方式 A 或 B 即可在 NAS 上“编译运行”。
