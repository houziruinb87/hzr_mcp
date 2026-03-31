# 小智 server 正确连接指南

让 Open-XiaoAI 能正确连上自建 xiaozhi-esp32-server（OTA + WebSocket），并能在智控台绑定设备。

---

## 一、Open-XiaoAI 里要配对两个地址

小智有两类接口，**不能混用**：

| 用途 | 该连哪个服务 | 端口 | 在 config.py 里对应 |
|------|--------------|------|---------------------|
| **OTA**（拿配置、验证码、设备激活） | **智控台 web**（xiaozhi-esp32-server-**web**） | 8002（容器内）/ 宿主机 18002 | `OTA_URL` |
| **对话**（WebSocket 收发语音/文本） | **主服务**（xiaozhi-esp32-server） | 8000 | `WEBSOCKET_URL` |

- **错误**：把 `OTA_URL` 指到主服务 8000 → OTA 可能失败或拿不到验证码。
- **正确**：OTA 指 web（8002/18002），WebSocket 指主服务（8000）。

---

## 二、按你的部署方式二选一

### 方式 A：Open-XiaoAI 和 xiaozhi 不在同一 Docker 网络（常见）

Open-XiaoAI 单独一个 compose、和 xiaozhi 不在同一个 compose 里时，用 **NAS 宿主机 IP**，方便音箱和 Open-XiaoAI 都能访问。

在 Open-XiaoAI 的 **config.py** 里：

```python
"xiaozhi": {
    "OTA_URL": "http://192.168.1.100:18002/xiaozhi/ota/",
    "WEBSOCKET_URL": "ws://192.168.1.100:8000/xiaozhi/v1/",
    "WEBSOCKET_ACCESS_TOKEN": "",
    "DEVICE_ID": "",
    "VERIFICATION_CODE": "",
},
```

- 把 `192.168.1.100` 换成你 NAS 的实际 IP。
- docker-compose 只保留默认网络即可，**不需要**加入 xiaozhi 的网络。

### 方式 B：Open-XiaoAI 和 xiaozhi 在同一 Docker 网络

如果你把 Open-XiaoAI 和 xiaozhi 放在同一个 compose 里，或者让 Open-XiaoAI 加入了 xiaozhi 的 network（如 `xiaozhi_server_default`），可以用**容器名**：

在 Open-XiaoAI 的 **config.py** 里：

```python
"xiaozhi": {
    "OTA_URL": "http://xiaozhi-esp32-server-web:8002/xiaozhi/ota/",
    "WEBSOCKET_URL": "ws://xiaozhi-esp32-server:8000/xiaozhi/v1/",
    "WEBSOCKET_ACCESS_TOKEN": "",
    "DEVICE_ID": "",
    "VERIFICATION_CODE": "",
},
```

docker-compose 里需要让 Open-XiaoAI 加入 xiaozhi 的网络，例如：

```yaml
services:
  open-xiaoai-xiaozhi:
    # ...
    networks:
      - default
      - xiaozhi_net

networks:
  xiaozhi_net:
    external: true
    name: xiaozhi_server_default
```

这样既能让音箱通过宿主机访问 4399，又能用容器名访问小智。

---

## 三、小智 server 端要保证的

1. **主服务**（xiaozhi-esp32-server）监听 **8000**，宿主机端口映射一致（如 `8000:8000`）。
2. **智控台 web**（xiaozhi-esp32-server-web）监听 **8002**，宿主机映射到 **18002**（如 `18002:8002`）。
3. **智控台「参数管理」**里，OTA/WebSocket 的地址要和实际访问方式一致：
   - 若 Open-XiaoAI 用 IP 访问：填 `http://NAS的IP:18002/xiaozhi/ota/`、`ws://NAS的IP:8000/xiaozhi/v1/`。
   - 若 Open-XiaoAI 用容器名访问：填容器内可访问的地址（如 web:8002、主服务:8000）。
4. **认证**：若小智开了 `server.auth.enabled`，要么在智控台绑定设备后用下发的 token，要么先关闭认证做连通性测试。

---

## 四、怎么算「正确连接」

1. **OTA 成功**：Open-XiaoAI 启动或首次唤醒时，能向 `OTA_URL` 发起请求并拿到返回（含 websocket 信息或验证码）。  
   - 看小智 **web** 或主服务日志是否有 OTA 请求；Open-XiaoAI 日志里是否出现验证码或「请登录控制面板，输入 xxxxxx」。
2. **WebSocket 连上**：Open-XiaoAI 能连上 `WEBSOCKET_URL` 并发 hello。  
   - 看小智**主服务**日志是否有「新 WebSocket 连接」、device-id、收到 hello。
3. **设备绑定**：在智控台 **设备管理** 用验证码绑定该 device-id 后，对话才可能正常（未绑定时常会只播验证码或要求先绑定）。

---

## 五、快速自检

- 在 Open-XiaoAI 容器里能解析/访问到 OTA 和 WebSocket 的地址（用 IP 时是 NAS:18002、NAS:8000；用容器名时是 `xiaozhi-esp32-server-web:8002`、`xiaozhi-esp32-server:8000`）。
- 小智主服务日志里能看到来自 Open-XiaoAI 的 WebSocket 连接和 hello。
- 智控台里能看到该设备（device-id/MAC）并可绑定。

按上面配好后，一般就能正确连接；若验证码不播报，再按《现在该咋改-操作清单》检查自建 server 的 TTS 是否先发 `tts` + `state: "start"`。
