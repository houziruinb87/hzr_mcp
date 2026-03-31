# Open-XiaoAI 自定义后端 Server 库

与 Open-XiaoAI 客户端对接的自定义后端：**收语音 → VAD → 转文字 → 唤醒判定 → 唤醒后收新语音 → 转文字 → 意图识别 → 分发执行**。

## 整体流程

```
客户端语音流(Stream "record")
    → VAD 检测（起/止）
    → 语音段 → ASR 转文字
    → 关键词匹配做唤醒判定
    → 若未唤醒：可忽略或提示
    → 若已唤醒：进入会话，收新语音 → ASR → 意图识别
    → 按意图分发：播歌(XiaoMusic)、控制(bridge_server)、对话(LLM) 等
```

## 与官方示例的差异

| 能力         | xiaozhi/migpt/gemini 示例 | 本库目标                     |
|--------------|---------------------------|------------------------------|
| 协议         | 对接各自云端/固定流程     | 与 Open-XiaoAI 客户端同协议   |
| 唤醒         | 多为客户端/云端 KWS       | 服务端 VAD + 关键词唤醒       |
| 意图         | 单一场景（对话/播歌等）   | 可插拔多意图（播歌/控制/对话）|
| 扩展         | 改示例代码                | 配置 + 注册 Handler 即可      |

## 协议要点（与 client-rust 对齐）

- **收**：`Event`（如 instruction）、`Stream`（tag=`record` 为麦克风音频）。
- **发**：`Request` 调用客户端 RPC（如 `start_play`、`start_recording`）；`Stream`（tag=`play`）下发 TTS/播报。
- 消息结构见 `packages/client-rust/src/services/connect/data.rs`：`AppMessage` = Request | Response | Event | Stream。

## 目录结构

```
xiaoai/
├── README.md           # 本说明
├── config.py           # 配置加载（config.yaml / config.example.yaml）
├── config.example.yaml # 配置示例
├── audio_loader.py     # 唤醒回复等音频加载
├── audio/              # 音频资源目录
│   ├── README.md
│   └── 爸爸最帅收到收到.mp3   # 唤醒后播报
├── protocol.py         # AppMessage 解析与构造
├── transport.py        # WebSocket 服务、收发与 RPC
├── pipeline.py         # 流水线：VAD → ASR → 唤醒 → [ASR → 意图 → 分发]
├── vad.py / asr.py     # VAD/ASR 抽象 + 占位实现
├── wake.py / intent.py # 唤醒词、意图识别 + Handler 注册
└── main.py             # 入口：启动 WS + 跑 pipeline
```

## 使用方式

1. 安装依赖：`pip install -r requirements.txt`（VAD/ASR 按需选型）。
2. 复制 `config.example.yaml` 为 `config.yaml`（可选），可配置 `server`、`wake.keywords`、`wake.reply_audio`（唤醒回复音频，默认 `audio/爸爸最帅收到收到.mp3`）等。
3. 在 `main.py` 或自己的入口里注册意图 Handler（`intent_router.register("play_music", your_handler)`），Handler 可返回 `{"tts": audio_bytes}` 用于播报。
4. 运行：在仓库根目录执行 `python -m main`（或 `pip install -r requirements.txt` 后执行），服务监听本机 4399。

## 项目骨架说明

- **protocol.py**：与 client-rust 对齐的 AppMessage（Request/Response/Event/Stream）解析与构造。
- **transport.py**：WebSocket 服务端，收 Event/Stream，发 Request/Stream(play)。
- **pipeline.py**：流水线编排；当前为占位 VAD/ASR，需接入真实实现。
- **vad.py / asr.py**：抽象 + Dummy 实现，便于替换为 Silero、FunASR 等。
- **wake.py**：关键词唤醒；可扩展为 KWS 模型。
- **intent.py**：规则意图 + Handler 注册，可扩展 LLM 兜底。

## 依赖与实现选型

- **VAD**：Silero VAD（与 xiaozhi 一致）或 webrtcvad，可插拔。
- **ASR**：FunASR / 火山 / 豆包 / 其他 HTTP API，抽象接口统一。
- **意图**：规则关键词 + 可选 LLM 兜底，输出 action + 参数供 Handler 执行。
