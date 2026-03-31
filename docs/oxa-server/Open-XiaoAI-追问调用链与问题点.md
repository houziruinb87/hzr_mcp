# Open-XiaoAI 追问调用链与「追问无反应」问题点

本地仓库路径：`/Users/houzirui/Documents/xiaomi/open-xiaoai/examples/xiaozhi/`（以下文件均以此为根）。

---

## 一、入口与整体流程

- **小爱音箱模式**：小爱把音频和识别结果发给 Open-XiaoAI，由 `xiaoai.py` 的 `on_input_data` / `on_event` 处理。
- **关键**：追问「北京天气」时，小爱会发 **指令事件（instruction + RecognizeResult）** 的**文本**，当前实现把**所有带文本的指令都当成一次唤醒**，导致会话被重置，追问不会当作用户输入发给小智。

---

## 二、该看的文件与调用链

### 1. 唤醒入口（小爱指令 → 唤醒/会话）

| 文件 | 作用 |
|------|------|
| **`xiaozhi/xiaoai.py`** | 小爱事件入口，**问题高发处** |

**调用链：**

```
小爱音箱 → on_event(event)  [xiaoai.py 66-88]
  → event_type == "instruction" 且 RecognizeResult
  → 取 text = payload.results[0].text，is_final
  → 若 text 且 is_final：print("🔥 收到指令: {text}")，await EventManager.wakeup(text, "xiaoai")
```

- 「你好小智」→ `wakeup("你好小智", "xiaoai")` ✅ 正确。
- 「北京天气」→ 同样走 `wakeup("北京天气", "xiaoai")` ❌ 被当成**又一次唤醒**，会启动新会话并 abort 当前会话，追问不会发给小智。

**结论**：**`xiaoai.py` 第 74-87 行**：所有「带文本的 instruction」都调用了 `EventManager.wakeup(text, "xiaoai")`，没有区分「唤醒词」和「追问内容」。

---

### 2. 唤醒后的会话流程（等 VAD / 发音频）

| 文件 | 作用 |
|------|------|
| **`xiaozhi/event.py`** | 唤醒后的会话状态机 |
| **`xiaozhi/xiaozhi.py`** | 设备状态、音频入口、发往小智 |

**调用链：**

```
EventManager.wakeup(text, source)  [event.py 164-172]
  → before_wakeup(speaker, text, source)  [config 里播放「你好主人…」]
  → 若返回 True：on_wakeup() → start_session() → __start_session()

__start_session()  [event.py 107-162，仅 get_env("CLI") 为真时执行]
  → set_device_state(IDLE)，send_abort_speaking(ABORT)
  → vad.resume("speech")，wait_next_step(timeout=20)   // 等「有人说话」
  → 若 step == "timeout" → after_wakeup(speaker)（主人再见），return
  → 若 step == Step.on_speech → send_start_listening(MANUAL)，set_device_state(LISTENING)
  → vad.resume("silence")，wait_next_step()   // 等「说完」
  → send_stop_listening()，set_device_state(IDLE)
```

- **Step.on_speech** 由 **VAD** 检测到语音后调用 `EventManager.on_speech(speech_buffer)` [vad/__init__.py 97]。
- 小爱发来的**麦克风音频**经 `on_input_data` → `GlobalStream.input()` → 写入 VAD/Codec 使用的流 [stream.py]；**文本**只通过 `on_event` 的 instruction 过来，不会自动变成「用户正在说话」的 VAD 事件。

因此：  
若先收到 instruction 的「北京天气」文本，会立刻触发 `wakeup("北京天气", "xiaoai")` → 又一次 `__start_session()` → **IDLE + abort**，把当前正在等的会话打断，且不会把「北京天气」当作用户输入发给小智。

---

### 3. 把用户语音发到小智（仅音频路径）

| 文件 | 作用 |
|------|------|
| **`xiaozhi/xiaozhi.py`** | 主循环里调 _handle_input_audio |
| **`xiaozhi/services/protocols/websocket_protocol.py`** | 连小智、发 hello、发音频 |

**调用链：**

```
主循环 _main_loop  [xiaozhi.py 164-178]
  → AUDIO_INPUT_READY_EVENT 置位时 → _handle_input_audio()

_handle_input_audio()  [xiaozhi.py 205-224]
  → 仅当 device_state == DeviceState.LISTENING 才处理
  → encoded_data = audio_codec.read_audio()   // 从 GlobalStream 来的麦克风/小爱音频
  → 若 protocol.is_audio_channel_opened()：protocol.send_audio(encoded_data)
  → 否则打 [OXA] 有音频但未发送 的 log
```

```
启动时：_initialize_xiaozhi()  [xiaozhi.py 110-127]
  → protocol.open_audio_channel()  [websocket_protocol.py 149-154]
  → connect()：建 WebSocket，发 hello，等服务器 hello
  → _message_handler() 收 TTS/STT/LLM 等
```

- 发到小智的**只有**：`send_audio(encoded_data)`（二进制音频帧）以及协议里的 `send_text`（hello、listen、abort、ping 等）。
- **没有**「把用户文本直接发给小智」的接口；小智端若只支持语音，就必须走「LISTENING + 音频」这条路径。

---

### 4. 小结：追问为什么没回答

1. **小爱把「北京天气」当指令事件（文本）发过来**，在 **`xiaoai.py`** 里被统一当成一次唤醒：`wakeup("北京天气", "xiaoai")`。
2. **`wakeup` 会再次跑 `__start_session()`**：先 IDLE + abort，再等 VAD 的 `on_speech`。  
   - 若此时追问的**音频**还没被 VAD 判成「说话」、或已被前一次 abort 打乱，就进不到 LISTENING，`_handle_input_audio` 不会发音频。
3. 协议层**没有**「把用户文本当一句话发给小智」的发送路径，只能靠「LISTENING + send_audio」；会话被 abort 或一直等不到 on_speech，追问就发不出去。

---

## 三、建议修改方向（不改其他 Open-XiaoAI 逻辑的前提下）

1. **在 `xiaoai.py` 区分「唤醒词」和「追问」**
   - 若当前已在「唤醒后的会话」中（例如 `EventManager` 或 `xiaozhi` 的某状态表示「已唤醒、等用户说话」），且收到的 `text` 不在唤醒词列表里，则**不要**再调 `EventManager.wakeup(text, "xiaoai")`。
   - 可选做法：
     - 把 `text` 交给 `EventManager` 或 `xiaozhi` 的「用户已说话」逻辑：若小智支持文本输入，则加一条「发用户文本」的协议并在这里调用；若只支持音频，则用该 text 触发「等价于 on_speech」的流程（例如直接进入 LISTENING 并依赖后续音频，或若后端支持则发文本）。
   - 这样「北京天气」不会再触发一次 wakeup，不会把当前会话 abort 掉。

2. **若小智 server 支持「文本输入」**
   - 在 **`websocket_protocol.py`**（或 protocol 基类）里增加「发送用户文本」的接口（例如某种 `type: "text"` 或 `user_input` 的 JSON）。
   - 在 **`xiaoai.py`** 的上述分支里，对非唤醒词的 instruction 文本调用该接口，把「北京天气」直接发给小智。

3. **若小智只接受音频**
   - 保证「北京天气」的**音频**能稳定进入 LISTENING 下的 `_handle_input_audio`：
     - 避免 instruction 的 `wakeup("北京天气")` 再次 abort；
     - 必要时调整 VAD 与 `__start_session` 的时序，让第一次 `on_speech` 后进入 LISTENING 时，追问音频仍通过 GlobalStream 被 codec 读到并发送。

---

## 四、文件清单（按调用顺序）

| 序号 | 路径 | 说明 |
|------|------|------|
| 1 | `xiaozhi/xiaoai.py` | 小爱事件入口；**instruction 文本统一走 wakeup 导致追问被当成二次唤醒** |
| 2 | `xiaozhi/event.py` | `wakeup` → `on_wakeup` → `__start_session`；等 VAD on_speech/on_silence |
| 3 | `config.py`（项目根或 xiaozhi 下） | `before_wakeup` / `after_wakeup`、`wakeup.timeout` |
| 4 | `xiaozhi/xiaozhi.py` | `_initialize_xiaozhi`、`_handle_input_audio`、`set_device_state(LISTENING)` |
| 5 | `xiaozhi/services/audio/vad/__init__.py` | VAD 检测到说话 → `EventManager.on_speech(speech_buffer)` |
| 6 | `xiaozhi/services/audio/stream.py` | `GlobalStream`：小爱 `on_input_data` 写入，VAD/Codec 读取 |
| 7 | `xiaozhi/services/audio/codec.py` | `read_audio()`：供 `_handle_input_audio` 发给小智 |
| 8 | `xiaozhi/services/protocols/websocket_protocol.py` | `connect`、`open_audio_channel`、`send_audio`、`is_audio_channel_opened` |
| 9 | `xiaozhi/services/protocols/protocol.py` | `send_start_listening`、`send_stop_listening`、`send_abort_speaking` |

优先看并改：**`xiaoai.py` 的 instruction 分支**，再根据小智是否支持文本决定是否在 protocol 层加「发用户文本」并在该分支调用。
