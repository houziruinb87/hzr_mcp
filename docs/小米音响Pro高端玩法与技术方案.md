 # 小米音响 Pro 高端玩法与技术方案汇总

针对**小米音响 Pro**（含小爱音箱 Pro、Xiaomi Sound Pro 等型号）的第三方接入、Docker 部署、与 MCP/智能家居联动的技术方案与想法汇总。便于后续选型或与 hzr_mcp、Home Assistant 结合使用。

**你当前设备：小米音响 Pro，型号 OH2P（Xiaomi 智能音箱 Pro）** — 无刷机、刷机方案均支持，见下表。

---

## 一、型号与兼容性速查

| 型号/名称 | 说明 | 无刷机方案 | 刷机/固件方案 |
|-----------|------|------------|----------------|
| **小爱音箱 Pro** | 型号 LX06，较早款 | ✅ MiGPT / MiGPT-Next | ✅ Open-XiaoAI（推荐） |
| **小米音响 Pro / Xiaomi 智能音箱 Pro** | **型号 OH2P**（你的设备） | ✅ MiGPT / MiGPT-Next 等 | ✅ Open-XiaoAI |
| **Xiaomi Sound Pro** | 型号 L17A，新款 | ✅ MiGPT 等（需查兼容表） | ⚠️ 以 Open-XiaoAI 文档为准 |
| **小米音响 Pro 2025** | 新品，大模型小爱 | 官方大模型 + 第三方待验证 | 待社区适配 |

- **无刷机**：用小米账号 + 本地/云服务拦截或增强小爱，不拆机、不刷固件。  
- **刷机方案**：需要给音箱刷补丁固件、开 SSH，可完全接管「耳朵和嘴巴」，支持自定义唤醒词、小智、MiGPT、Gemini 等。

---

## 二、方案分类总览

### 1. 不刷机：Docker/本地服务「增强」小爱（推荐先试）

不拆机、不刷固件，在 NAS/服务器上跑 Docker 或 Node 服务，用小爱原有唤醒与 TTS，把「回答」换成大模型或自定义逻辑。

| 项目 | 一句话 | Docker | 与你现有技术栈 |
|------|--------|--------|------------------|
| **MiGPT** | 小爱 → ChatGPT/豆包/DeepSeek 等 | ✅ 官方镜像 | 可和 hzr_mcp 并行：语音入口小爱，设备控制仍走 MCP |
| **MiGPT-Next** | MiGPT 升级版，支持自定义回复、onMessage | ✅ 支持 | 可在 onMessage 里调你的 HTTP/脚本（如 bridge_server） |
| **xiaogpt** | Python 版小爱+ChatGPT | ✅ 有方案 | 同机可跑 hzr_mcp + xiaogpt |

特点：  
- 小爱同学 → 说「小爱同学，请 xxx」→ 请求发到你部署的服务 → 大模型/自定义逻辑 → TTS 播报。  
- **和 Docker 的关系**：这些方案本身就可以跑在 NAS 的 Docker 里，与 Home Assistant、hzr_mcp 容器并列部署。  
- **和 hzr_mcp 的联动**：在 MiGPT-Next 的 `onMessage` 里识别意图（如「打开加湿器」），请求你 NAS 上的 `http://NAS:8765/jiashiqi/on`（即 homeassistant/bridge_server.py），实现「小爱一句话 → 执行 hzr_mcp 脚本」。

### 2. 刷机：Open-XiaoAI（高端玩法，仅限 LX06/OH2P）

- **项目**：[idootop/open-xiaoai](https://github.com/idootop/open-xiaoai)  
- **适用**：小爱音箱 Pro（LX06）、**Xiaomi 智能音箱 Pro（OH2P）**。你的 **OH2P 在官方支持列表内**，可按文档刷机后接入小智、自定义唤醒词、MiGPT、Gemini 等。其他型号（如 L17A）需查 Open-XiaoAI 最新文档。  
- **能力**：  
  - 刷补丁固件 + 跑 Client 端，直接接管麦克风/扬声器。  
  - 接入**小智 AI**、**自定义唤醒词**（open-xiaoai-kws）、**MiGPT**、**Gemini Live API** 等。  
  - 立体声组队、本地化能力更强，可玩性最高。  
- **代价**：需按文档刷机、开 SSH，有变砖/保修风险，仅建议爱折腾的用户在 LX06/OH2P 上使用。

### 3. 小爱 + Home Assistant / 智能家居

- **Xiaomi Miot Auto（HACS）**：小爱进 HA 后成 `media_player`，可 TTS、执行语音指令、conversation 传感器。  
- **巴法云**：最简单，小爱里「添加其他平台设备」→ 巴法 → 同步 HA 设备，语音即可控制。  
- **自定义指令**：HA 的 conversation 传感器 + Node-RED/自动化，根据对小爱说的话触发脚本或 REST 调用（可调用你的 bridge_server 或 hzr_mcp 相关接口）。  

这样：**小爱语音 → HA → 调用 NAS 上的脚本或 HTTP**，和「HomePod + HA + bridge_server」是同一类思路，只是入口从小爱进来。

### 4. 小爱 + MCP / Webhook（语音通知与 Agent）

- **xiaoi**（据报导）：开源工具，让小爱支持 **MCP 协议** 和 **Webhook**。  
  - 能力：CLI、TUI、Webhook、MCP；可把音箱接到 Codex 等本地 Agent，任务完成时语音播报；Webhook 可做监控报警、自动化触发。  
  - 来源：[Linux.do 讨论](https://linux.do/t/topic/1594256)、[80aj 介绍](https://www.80aj.com/2026/02/11/xiaoi-mcp-webhook-support/)。可搜索「xiaoi 小爱 MCP」获取最新仓库与文档。  
- **与 hzr_mcp 的联想**：若 xiaoi 在局域网暴露 MCP 或 Webhook，理论上可让同一网络下的 hzr_mcp 或其它 MCP 服务把「执行结果」用语音从小爱播报，或由小爱触发 Webhook 再执行你的脚本。

### 5. 官方与半官方

- **小米小爱开放平台**：[developers.xiaoai.mi.com](https://developers.xiaoai.mi.com) — 自定义技能、HTTPS 回调。适合做「关键词 → 你的后端 API」类技能，后端可再调 Docker 里的脚本或 hzr_mcp。  
- **大模型小爱**：部分型号（如 LX06、L17A）已支持官方大模型；若只需「更聪明的对话」可先升级固件与 App 使用官方能力，再叠加上述第三方做「执行脚本/设备控制」。

---

## 三、和 Docker / NAS 的结合方式（简要）

1. **MiGPT / MiGPT-Next 跑在 NAS Docker**  
   - 与 hzr_mcp、Home Assistant 同机部署。  
   - 在 MiGPT-Next 的 `onMessage` 里解析指令，用 HTTP 调 `bridge_server` 或直接调你写的「设备控制 API」，实现「小爱一句话控制加湿器/灯」。

2. **bridge_server（你已有）**  
   - 已提供 `http://NAS:8765/jiashiqi/on|off` 等。  
   - 小爱侧只要能把「打开加湿器」变成一次 HTTP 请求即可：  
     - 通过 HA 的 conversation + 自动化调用 rest_command；或  
     - 通过 MiGPT-Next 的 onMessage 调用；或  
     - 通过小爱自定义技能回调你的 Flask/FastAPI。

3. **Open-XiaoAI（刷机后）**  
   - 音箱上跑 Client，Server 端可跑在 NAS（Docker 或裸机），实现小智/MiGPT/Gemini 等，逻辑里同样可调你 NAS 上的 HTTP 接口或 MCP。

---

## 四、推荐路线（按你的情况）

- **先不刷机**  
  1. 在 NAS 上 Docker 跑 **MiGPT-Next**，小爱用「小爱同学，请 xxx」走大模型 + 自定义回复。  
  2. 在 `onMessage` 里加简单关键词（如「打开加湿器」「关闭加湿器」），请求 `http://NAS:8765/jiashiqi/on` 或 `/off`。  
  3. 需要 Siri/HomePod 时，继续用现有 **Home Assistant + HomeKit + bridge_server** 方案。

- **若想玩到底（你的 OH2P 支持）**  
  - 考虑 **Open-XiaoAI**：OH2P 在支持列表内，刷机后接入小智、自定义唤醒词、MiGPT 等，Server 端放 NAS，同样可调 bridge_server 或 hzr_mcp 相关接口。

- **关注 xiaoi**  
  - 若后续确认支持 MCP/Webhook 且稳定，可把「小爱」当作 MCP 语音前端或 Webhook 触发器，与 hzr_mcp、Home Assistant 组成统一工作流。

---

## 五、链接与仓库速查

| 项目/资源 | 链接 |
|-----------|------|
| MiGPT | https://github.com/idootop/mi-gpt |
| MiGPT-Next | https://github.com/idootop/migpt-next |
| Open-XiaoAI | https://github.com/idootop/open-xiaoai |
| Open-XiaoAI 唤醒词 (open-xiaoai-kws) | https://github.com/idootop/open-xiaoai-kws |
| xiaogpt | https://github.com/yihong0618/xiaogpt |
| 小爱开放平台 | https://developers.xiaoai.mi.com |
| MiGPT 兼容型号表 | https://github.com/idootop/mi-gpt/blob/main/docs/compatibility.md |
| xiaoi 介绍（MCP/Webhook） | https://www.80aj.com/2026/02/11/xiaoi-mcp-webhook-support/ 、Linux.do 对应讨论 |

---

## 六、小结

- **小米音响 Pro** 可通过 **MiGPT/MiGPT-Next** 在 **Docker** 里接入大模型和自定义逻辑，无需刷机。  
- **高端玩法**：**Open-XiaoAI**（仅 LX06/OH2P）刷机后接入小智、自定义唤醒词、MiGPT、Gemini 等，与 NAS 上服务配合。  
- **和 hzr_mcp 的联动**：小爱（或 Siri）→ HA / MiGPT-Next / 自定义技能 → 调用 NAS 上的 **bridge_server** 或其它 HTTP 接口 → 执行 hzr_mcp 里同一套控制脚本（如加湿器、灯）。  
- 后续可关注 **xiaoi** 的 MCP/Webhook 能力，用于语音通知和与 MCP 生态的深度整合。

如果你确定音箱型号（如 LX06 / OH2P / L17A），可以再细化一份「该型号下的最小可行方案」（例如只做：小爱 → MiGPT-Next → bridge_server → 加湿器）。
