# 小智 Python 开源后台（xiaozhi-esp32-server）接入 Minimax API

## 结论：可以用 Minimax API Key

根据 [xiaozhi-esp32-server](https://github.com/xinnan-tech/xiaozhi-esp32-server) 官方说明：

1. **LLM（大模型）**  
   文档写明：**「实际上，任何支持 openai 接口调用的 LLM 均可接入使用。」**  
   [Minimax 开放平台](https://platform.minimaxi.com/document/guides/chat-pro/API) 提供 **OpenAI 兼容** 的文本对话接口，因此可以作为「自定义 LLM」接入小智后端。

2. **TTS（语音合成）**  
   官方支持的 TTS 列表里**已包含 Minimax**：  
   **MinimaxTTS**（接口调用方式），可直接在配置里使用你的 Minimax API Key。

---

## 一、LLM：用 Minimax 大模型

Minimax 文本 API 的 OpenAI 兼容方式（见 [MiniMax 文档](https://platform.minimaxi.com/document/guides/chat-pro/API)）：

- **base_url**：`https://api.minimaxi.com/v1`
- **api_key**：你在 Minimax 开放平台申请的 API Key
- **model**：如 `MiniMax-M2.5`、`MiniMax-M2.5-highspeed`、`MiniMax-M2.1` 等（按文档填写）

在 xiaozhi-esp32-server 中，通过 **OpenAI 兼容** 的 LLM 实现（`core/providers/llm/openai/`）接入，该实现支持 **`base_url`**、**`api_key`**、**`model_name`**。在 `data/.config.yaml` 中配置：

```yaml
selected_module:
  LLM: OpenAiLLM

LLM:
  OpenAiLLM:
    base_url: https://api.minimaxi.com/v1
    api_key: 你的Minimax_API_Key
    model_name: MiniMax-M2.5   # 或 MiniMax-M2.5-highspeed、MiniMax-M2.1、MiniMax-M2 等
```

Minimax 文本 API 文档：[OpenAI API 兼容 - MiniMax 开放平台](https://platform.minimaxi.com/document/guides/chat-pro/API)。若配置键在仓库默认 `config.yaml` 中为其他名称（如 `OpenaiLLM`），以仓库内 `main/xiaozhi-server/config.yaml` 的 LLM 段为准，把 `OpenAiLLM` 改成实际键名即可。

---

## 二、TTS：用 Minimax 语音合成

官方 README 的 TTS 列表中已支持 **MinimaxTTS**。在 `config.yaml` / `.config.yaml` 中：

- 将 `selected_module.TTS` 设为 **MinimaxTTS**
- 在 **TTS** 段下增加 **MinimaxTTS** 的配置，并填入你的 Minimax API Key（以及文档要求的其他参数，如 model、voice 等，以仓库内示例或 [Minimax TTS 文档](https://platform.minimaxi.com/document) 为准）。

---

## 三、建议步骤

1. 克隆或打开 **xiaozhi-esp32-server** 仓库，查看 **`main/xiaozhi-server/config.yaml`** 中：
   - 所有 **LLM** 相关块（含 `base_url`、`api_key` 的），确认「OpenAI 兼容」的 LLM 名称。
   - 所有 **TTS** 相关块，确认 **MinimaxTTS** 的键名和参数。
2. 在 **`data/.config.yaml`**（或你实际使用的配置）里：
   - 按上面方式配置 LLM（base_url、api_key、model），使用你的 **Minimax API Key**。
   - 按官方示例配置 **MinimaxTTS**，使用同一或单独的 Minimax API Key（视平台规定而定）。
3. 重启 xiaozhi-esp32-server，用「小智同学」对话与语音合成测试。

这样即可在小智 Python 开源后台中完整使用你的 **Minimax API Key**（大模型 + 语音合成）。
