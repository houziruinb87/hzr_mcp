# 小米音响 + Open-XiaoAI + 小智 server 的关系

## 三者关系（谁连谁）

```
小米音响（小爱同学）
    │
    │  WiFi，把语音/指令发到「你指定的服务器」
    │  （你配置成 NAS 的 Open-XiaoAI，即 NAS:4399）
    ▼
Open-XiaoAI 服务（跑在 NAS 上，如 Docker 容器）
    │
    │  作为「一个设备」连到小智 server
    │  用 WebSocket 发 hello、音频、收 TTS 等
    ▼
小智 server（官网 或 自建 xiaozhi-esp32-server）
```

- **小智 server 只认识「连它的那个客户端」**，也就是 **Open-XiaoAI**。  
- 小智 server **不知道**小米音响的存在，也不知道有多少个音箱；它眼里只有「一个设备」：当前连上来的 Open-XiaoAI（用 device-id 区分）。

所以：  
**小米音响** → 只和 **Open-XiaoAI** 通信；  
**小智 server** → 只和 **Open-XiaoAI** 通信。  
Open-XiaoAI 是「音箱和小智之间的桥」。

---

## 智控台里你绑定的「设备」到底是什么

你在小智智控台（自建 xiaozhi）里看到的、用验证码绑定的那条记录：

- **Mac 地址**：`02:42:c0:a8:90:02`
- **设备型号**：`lc-esp32-s3`（界面上的展示名，可能是默认/兼容显示）

**这条记录 = 你的 Open-XiaoAI 服务**，不是小米音响本身。

- Open-XiaoAI 连小智 WebSocket 时，会带一个 **Device-Id**（在 Docker 里通常用容器的 MAC，所以是 `02:42:c0:a8:90:02`）。
- 小智 server 就把「这个 Device-Id」当成一台设备，在智控台里显示为一条设备记录；你拿验证码绑定的就是**这台「逻辑设备」**，也就是 **Open-XiaoAI**。
- 设备型号写 `lc-esp32-s3` 是服务端/协议里对这类客户端的展示方式，并不代表你家里有一块 ESP32 开发板；实际跑的是 NAS 上的 Open-XiaoAI 容器。

所以可以简单记：

- **智控台里绑定的 = Open-XiaoAI 这台「桥」在小智侧的账号/身份。**
- **小米音响** 只和 Open-XiaoAI 说话；**小智** 只和 Open-XiaoAI 说话；**你绑定的就是这座桥**。

---

## 和「连官方小智没问题」的关系

- 连**官方小智**时：还是 **小米音响 → Open-XiaoAI → 官方小智**；官方小智那边也是把 Open-XiaoAI 当成一个设备，只是那边不需要你在智控台绑验证码（或流程不同）。
- 连**自建小智**时：同样是 **小米音响 → Open-XiaoAI → 自建小智**；自建小智要求「设备」在智控台用验证码绑定，所以你绑定的就是 **Open-XiaoAI**（device-id 02:42:c0:a8:90:02），绑完之后，自建小智才认这台「桥」、愿意和它正常对话。

总结：**绑定的不是小米音响，而是「Open-XiaoAI」在小智 server 上的这条设备记录；小米音响 + Open-XiaoAI + 小智的关系就是「音响 → 桥(Open-XiaoAI) → 小智」，桥在智控台里显示成一台设备（Mac 02:42:c0:a8:90:02，型号可能写 lc-esp32-s3）。**
