# 火山双流 TTS：小智如何调用 + 配置与测试说明

## 一、小智 server 如何调用火山双流 TTS

小智服务里对应实现是 **`core/providers/tts/huoshan_double_stream.py`**，逻辑概括如下。

### 1. 使用的配置项（来自智控台 → 数据库 → manager-api）

| 参数 | 说明 | 示例（请替换为你控制台中的值） |
|------|------|----------|
| **ws_url** | 双向流 WebSocket 地址 | `wss://openspeech.bytedance.com/api/v3/tts/bidirection` |
| **appid** | 应用 ID（请求头 X-Api-App-Key） | `YOUR_VOLC_APP_ID` |
| **access_token** | 访问令牌（请求头 X-Api-Access-Key） | `YOUR_VOLC_ACCESS_KEY` |
| **resource_id** | 资源 ID（请求头 X-Api-Resource-Id） | **声音复刻2.0** 用 `seed-icl-2.0`；豆包语音合成1.0 用 `volc.service_type.10029` |
| **speaker** | 默认音色 | `S_7JS6dHIV1` |

### 2. 连接方式

- **协议**：WebSocket（wss）
- **建连时请求头**（由小智代码自动带上）：
  - `X-Api-App-Key`: appid
  - `X-Api-Access-Key`: access_token
  - `X-Api-Resource-Id`: resource_id
  - `X-Api-Connect-Id`: 随机 UUID

### 3. 调用流程（二进制自定义协议）

1. **StartConnection**：发空 payload，建立连接。
2. **StartSession**：带 `namespace: "BidirectionalTTS"`、`req_params` 里含 `speaker`、`audio_params`（含 format、sample_rate 等）、`additions`。
3. **TaskRequest**：发送要合成的文本 `text`，以及 `speaker`。
4. **FinishSession**：结束会话。
5. 在会话过程中接收服务端下发的 **TTSResponse** 二进制音频（PCM），再转成 Opus 推给设备。

文档参考：[火山引擎 双向流式 TTS - 1329505](https://www.volcengine.com/docs/6561/1329505?lang=zh)。

### 4. 声音 ID（如 S_7JS6dHIV1）的入参方式（文档对应关系）

在 [WebSocket 双向流式-V3](https://www.volcengine.com/docs/6561/1329505?lang=zh) 文档里，**没有单独写「声音ID」这个参数名**，声音复刻后台的「声音ID」对应的是请求体中的 **`req_params.speaker`**（文档中写的是「**发音人**」）。

- **文档表述**：`req_params.speaker` — “发音人，具体见发音人列表”。
- **实际含义**：发音人列表里既包含预置音色，也包含**声音复刻**里你创建的音色；声音复刻控制台里的 **声音ID**（例如 `S_7JS6dHIV1`）就是该发音人在接口中的取值。
- **入参方式**：在 StartSession / TaskRequest 的 **req_params** 里设置 **`speaker`** 字段为你的声音ID字符串即可，例如：
  ```json
  "req_params": {
    "text": "要合成的文本",
    "speaker": "S_7JS6dHIV1",
    "audio_params": { "format": "pcm", "sample_rate": 16000, ... }
  }
  ```

小智里：智控台「默认音色」填的就是这个声音ID；服务端会把它赋给 `self.voice`，在组包时写入 **req_params.speaker**，因此你在智控台填 **默认音色 = S_7JS6dHIV1** 即表示使用「大dady」这路复刻声音。

---

## 二、智控台配置要点（火山引擎流式）

1. **WebSocket 地址**：`wss://openspeech.bytedance.com/api/v3/tts/bidirection`（若官方改为 `.cc` 域名则按控制台为准）。
2. **应用 ID**：在火山控制台复制应用 ID，填入智控台（勿将真实 ID 提交到公开仓库）。
3. **访问令牌**：在火山控制台生成 access_token，填入智控台（勿泄露）。
4. **资源 ID（按能力选择）**：  
   - **声音复刻 2.0**：**`seed-icl-2.0`**（声音复刻2.0字符版）  
   - 豆包语音合成模型 1.0：`volc.service_type.10029` 或 `seed-tts-1.0`  
   - 豆包语音合成模型 2.0：`seed-tts-2.0`  
   文档说明：豆包语音合成与声音复刻的 resource_id 不同，需与所选音色类型一致。
5. **默认音色**：你当前为 `S_7JS6dHIV1`，按需在智控台选择即可。

---

## 三、使用声音复刻 2.0 时的 resource_id

- 使用**声音复刻 2.0**能力时，**资源 ID** 应为 **`seed-icl-2.0`**（声音复刻2.0字符版），与官方文档一致。
- 智控台「修改模型」→ 火山引擎(流式) 中，**资源 ID** 填 **`seed-icl-2.0`** 并保存即可。

---

## 四、如何验证“是否调通”

1. **智控台**  
   - 模型配置 → 语音合成 → 火山引擎(流式)：确认 appid、访问令牌、**资源 ID 为 `seed-icl-2.0`**（声音复刻2.0）、默认音色 如上。  
   - 智能体管理 → 目标智能体：TTS 选择 **火山引擎(流式)** 并保存。

2. **重启小智服务**（使配置生效）  
   ```bash
   docker restart xiaozhi-esp32-server
   ```

3. **实际对话测试**  
   - Open-XiaoAI 的 config.py 中 xiaozhi 已指向自建小智（OTA_URL、WEBSOCKET_URL 为你的 NAS）。  
   - 对音箱唤醒并说一句话，听是否有语音回复。  
   - 若有正常播报，说明火山双流 TTS（含声音复刻）已调通。

4. **若仍无声音**  
   - 在 NAS 上执行：`docker logs xiaozhi-esp32-server --tail 200`  
   - 查看是否有 TTS/WebSocket/鉴权 相关报错，再根据报错排查（token 过期、resource_id 与音色类型不匹配、网络等）。

---

## 五、小结

- **小智调用方式**：通过 WebSocket 连火山双向流 TTS，用自定义二进制协议发 StartConnection → StartSession → TaskRequest → FinishSession，并接收 PCM 再转 Opus。  
- **配置要点**：使用**声音复刻 2.0** 时 **resource_id** 应为 **`seed-icl-2.0`**；appid、access_token、默认音色在智控台与数据库中保持一致即可。  
- **建议**：智控台里资源 ID 填 **`seed-icl-2.0`**，智能体选用「火山引擎(流式)」后，重启小智并做一次真实对话测试即可确认是否调通。
