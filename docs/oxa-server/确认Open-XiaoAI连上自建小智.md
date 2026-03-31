# 确认 Open-XiaoAI 已连上自建小智

## 一、已做操作

- **config.py**：`OTA_URL`、`WEBSOCKET_URL` 已改为指向 NAS（`http://192.168.1.100:18002/xiaozhi/ota/`、`ws://192.168.1.100:8000/xiaozhi/v1/`），并已同步到 NAS、重启 **open-xiaoai-xiaozhi** 容器。

---

## 二、要不要重启小米音响？

**一般不需要。** 音箱始终是连 Open-XiaoAI（NAS:4399），改的是 Open-XiaoAI 连哪个小智。  
若改完后唤醒/对话没反应，再试一次「断电重启音箱」或对音箱说「重启」（若支持）。

---

## 三、如何确认 Open-XiaoAI 连上了本地小智？

### 1. 看小智 server 日志（有连接就有日志）

连接建立时，小智会打一条带客户端 IP 的日志，例如：

```bash
# 在 NAS 上执行
docker logs xiaozhi-esp32-server --tail 100 2>&1 | grep -E "conn - Headers|客户端断开"
```

- 看到 **`<某IP> conn - Headers`**：说明有设备（Open-XiaoAI）连上了小智的 WebSocket。
- 看到 **`客户端断开连接`**：说明该连接已断开（正常结束或超时）。

若你对音箱做了「唤醒 + 说一句话」，再立刻查小智日志，通常能看到一次 `xxx.xxx.xxx.xxx conn - Headers`（xxx 多为 NAS 本机或 Open-XiaoAI 所在机器的 IP）。

### 2. 看 Open-XiaoAI 日志

```bash
docker logs open-xiaoai-xiaozhi --tail 80 2>&1
```

关注是否出现连小智、OTA、WebSocket 或错误信息，便于判断是「没连上」还是「连上但对话失败」。

### 3. 实际体验

- 唤醒词（如「你好小智」）后能听到「你好主人，我是小智…」  
- 再说一句话后有正常语音回复  

说明整条链路（Open-XiaoAI → 自建小智 → LLM/TTS）已通。

---

## 四、小智 server 要不要加日志？

**当前不必加。** 小智 server 在 **新 WebSocket 连接建立时** 已经打了关键日志：

- `{client_ip} conn - Headers: {self.headers}`（连接建立）
- `客户端断开连接`（连接关闭）

用上面 **三、1** 的 `docker logs` 命令即可判断是否连上。若以后要排查更细（例如按 device-id 区分设备），再考虑在 `core/connection.py` 的 `handle_connection` 里加一行带 `device_id` 的日志即可。
