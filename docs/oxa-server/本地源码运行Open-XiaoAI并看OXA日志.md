# 本地用源码跑 Open-XiaoAI 并看 [OXA] 日志

已在 `xiaomi/open-xiaoai/examples/xiaozhi` 里加上带 **`[OXA]`** 前缀的 `print`，用于排查「唤醒后追问无反应」时，是否连上小智、是否在发音频。

## 一、改动的文件（都在 examples/xiaozhi 下）

| 文件 | 日志含义 |
|------|----------|
| `xiaozhi/utils/config.py` | OTA 请求开始/响应状态；若返回里有 `websocket` 会打 url、token 长度 |
| `xiaozhi/services/protocols/websocket_protocol.py` | 准备连接 / TCP 已连 / hello 成功或超时或连接失败；`open_audio_channel` 被调用；`send_audio` 跳过（通道未打开）或发送异常；心跳失败重连 |
| `xiaozhi/xiaozhi.py` | 初始化时「即将打开小智音频通道」及返回后 `is_audio_channel_opened`；有音频但未发送时的 state、channel_open（最多打 3 次） |
| `xiaozhi/event.py` | `wakeup` 被调用（text/source）、`before_wakeup` 返回值；唤醒会话里「发送 send_start_listening，设置 LISTENING」 |

## 二、本地运行（CLI 模式，支持唤醒词）

### 1. 环境

- Python 3.10+
- 安装 [uv](https://github.com/astral-sh/uv)，以及 [Opus](https://opus-codec.org/)（按官方 README）
- 如需从零安装依赖：在 `examples/xiaozhi` 下执行 `uv sync --locked`

### 2. 配置

把 `examples/xiaozhi/config.py` 里 `xiaozhi` 改成你的自建小智地址（和 NAS 上一致即可）：

```python
"xiaozhi": {
    "OTA_URL": "http://192.168.1.100:18002/xiaozhi/ota/",
    "WEBSOCKET_URL": "ws://192.168.1.100:8000/xiaozhi/v1/",
    "WEBSOCKET_ACCESS_TOKEN": "",
    "DEVICE_ID": "",
    "VERIFICATION_CODE": "",
}
```

### 3. 运行

在 **examples/xiaozhi** 目录下：

```bash
cd /Users/houzirui/Documents/xiaomi/open-xiaoai/examples/xiaozhi
CLI=true uv run main.py
```

终端里会看到常规输出 + 所有 **`[OXA]`** 日志。

### 4. 只看 [OXA] 日志

另开一个终端：

```bash
cd /Users/houzirui/Documents/xiaomi/open-xiaoai/examples/xiaozhi
CLI=true uv run main.py 2>&1 | grep OXA
```

或先跑一段时间，把输出重定向再筛：

```bash
CLI=true uv run main.py 2>&1 | tee /tmp/oxa.log
# 之后: grep OXA /tmp/oxa.log
```

## 三、复现步骤 + 看什么

1. 启动：`CLI=true uv run main.py`，等出现「已启动」「已连接」等。
2. 看启动阶段是否出现：
   - `[OXA] OTA 请求开始`、`OTA 响应 status=200`、若有 `OTA 返回 websocket.url=...`
   - `[OXA] _initialize_xiaozhi: 即将打开小智音频通道`
   - `[OXA] 小智 WebSocket 准备连接 url=...`
   - 要么 `[OXA] 小智 WebSocket 连接成功（hello 已收到）` 和 `is_audio_channel_opened= True`，要么 `连接失败` / `等待 hello 超时`
3. 说唤醒词（如「你好小智」），看是否出现：
   - `[OXA] wakeup 被调用`、`before_wakeup 返回 wakeup=True`
   - 接着说「天气如何」，看是否出现：`[OXA] 唤醒会话: 发送 send_start_listening，设置 LISTENING`
4. 若追问仍无回复，看是否出现：
   - `[OXA] send_audio 跳过：音频通道未打开` → 说明启动时连小智没成功，或连接已断；
   - 或 `[OXA] _handle_input_audio: 有音频但未发送` → 同上，通道未打开。

## 四、如何根据日志判断

- **启动时就没有「小智 WebSocket 连接成功」**：连自建小智失败（网络/认证/地址），后面追问不会发音频。
- **有「连接成功」但追问时出现「send_audio 跳过」或「有音频但未发送」**：连接在中途断了（可看是否有「心跳失败，尝试重连」），或状态未正确变为 LISTENING。
- **有「连接成功」且没有「send_audio 跳过」**：音频应在往小智发，若仍无回复，再查小智端日志（是否收到音频/文本）。

本地跑通并抓到 [OXA] 日志后，把相关片段贴出来即可继续往下排查。
