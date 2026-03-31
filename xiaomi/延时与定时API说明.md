# 延时与定时 API 说明（基于官方协议）

本文档只写**官方协议里的 API 约定**和**在本机上的发现步骤**，不猜测具体 siid/piid 或取值。最终可用的「延时 30 秒后开启」等指令，需在完成发现步骤、拿到设备真实响应后再确定。

---

## 一、官方 API 是什么（协议层）

小米 MIOT 设备与控端之间通过 **miIO 协议** 通信，规范见：

- [小米IoT设备协议规范（MIoT-Spec）](https://iot.mi.com/new/doc/tools-and-resources/design/spec/overall)（iot.mi.com）
- 仓库 [MiEcosystem/miot-spec-doc](https://github.com/MiEcosystem/miot-spec-doc) 中的《小米IOT设备规范》等

与「属性」和「方法」相关的**三种标准调用**如下（与 python-miio 中 `Device.send()` / `MiotDevice` 一致）：

| 方法 | 用途 | 参数大致格式 |
|------|------|----------------|
| **get_properties** | 读取属性 | `[{ "siid": 服务ID, "piid": 属性ID }]`，可带 `did` 便于区分返回 |
| **set_properties** | 写入属性 | `[{ "siid", "piid", "value": 值 }]` |
| **action** | 调用动作 | 单条 `{ "siid", "aiid": 动作ID, "in": 参数列表 }` |

- 延时/定时在具体设备上可能用**属性**（如倒计时秒数）实现，也可能用**动作**（如「设置倒计时」）实现，需看该型号的规格或本机发现结果。
- **cuco.plug.v3** 在官方文档中没有逐条列出「延时开/定时关」对应的 siid/piid 或 aiid，因此必须通过下面的发现步骤在本机确认。

---

## 二、发现步骤（必须先做）

以下命令均为**官方支持的调用方式**（miiocli 对应 `raw_command` → `send(method, params)`），用于确认设备实际支持哪些服务/属性/动作。

### 1. 确认设备型号

```bash
miiocli device --ip 192.168.1.101 --token YOUR_MIOT_DEVICE_TOKEN info
```

确认输出中的 `model` 为 `cuco.plug.v3`（或你实际使用的型号）。

### 2. 用 get_properties 查询属性（官方格式）

协议规定：`get_properties` 的 parameters 为**数组**，每项为包含 **siid**、**piid** 的对象（可选带 `did`）。  
下面用乌龟灯 IP/token 举例，一次查询**开关服务**和**常见定时相关**的 (siid, piid)：

```bash
miiocli miotdevice --ip 192.168.1.101 --token YOUR_MIOT_DEVICE_TOKEN raw_command get_properties '[{"siid":2,"piid":1},{"siid":3,"piid":1},{"siid":3,"piid":2},{"siid":4,"piid":1},{"siid":4,"piid":2},{"siid":4,"piid":3},{"siid":4,"piid":4},{"siid":4,"piid":5}]'
```

- **siid=2, piid=1**：开关（已验证过）。
- **siid=3**：常见为指示灯/用电等；**siid=4**：常见为定时/倒计时相关（不同型号可能没有或 piid 不同）。

请在本机执行上述命令，把**完整返回**保存下来。

- 若某 (siid, piid) 返回错误或不存在，说明该设备没有该属性。
- 若返回正常，记下：**siid、piid、返回的 value 类型和含义**（例如是否为秒数、是否只读等），便于后面写 set_properties 或判断需要改哪个属性。

### 3. 若延时/定时是「动作」：action 调用格式

若规格或文档标明是**动作**（例如「设置倒计时」），则应用 **action**，而不是 set_properties。  
python-miio 中 `call_action_by(siid, aiid, params)` 对应协议：

- **method**：`action`
- **parameters**：单条对象，例如 `{ "did": "call-4-1", "siid": 4, "aiid": 1, "in": [] }`（aiid 和 in 以规格为准）

miiocli 示例（aiid、in 需按规格或尝试填写）：

```bash
miiocli miotdevice --ip 192.168.1.101 --token YOUR_MIOT_DEVICE_TOKEN raw_command action '{"did":"call-4-1","siid":4,"aiid":1,"in":[30]}'
```

是否支持、aiid 与 in 的语义需查该型号规格（如 [home.miot-spec.com](https://home.miot-spec.com/s/) 搜 `cuco.plug.v3`）或结合 get_properties 结果判断。

---

## 三、如何得到「延时 30 秒后开启」的最终指令

1. **先完成第二节**：跑完 `get_properties`（必要时多试几组 siid/piid），拿到设备真实返回。
2. **根据返回判断**：  
   - 若有「倒计时/延时」类属性（如秒数），则用 **set_properties**，value 格式与 get 到的类型、单位一致（例如整型秒）。  
   - 若规格写明是动作，则用 **action**，aiid 与 in 按规格或小范围试。
3. **再写具体命令**：在确认 siid/piid 或 aiid、value/in 格式后，再写出像「延时 30s 后开启」的最终 `set_properties` 或 `action` 示例，放入 [设备控制说明.md](设备控制说明.md) 作为已验证指令。

当前**不**在文档中写未验证的 set_properties/action，避免再次出现设备无反应的情况。你完成发现步骤后，把 get_properties（以及若有 action 尝试）的返回贴出，即可据此给出可验证的「延时 30 秒后开启」等命令。

---

## 四、本机发现结果（乌龟灯 cuco.plug.v3）

在同网机器上执行第二节的 `get_properties` 后，得到如下返回（已整理）：

| siid | piid | code | value | 说明 |
|------|------|------|-------|------|
| 2 | 1 | 0 | False | 开关状态（已验证开/关） |
| 3 | 1 | -4001 | — | 设备不支持 |
| 3 | 2 | 0 | False | 可读，含义以规格为准 |
| 4 | 1 | 0 | False | **延时开启开关**（False=未开启），需设为 True 才会执行延时 |
| 4 | 2 | 0 | 2 | 定时相关，数值（如时长/档位） |
| 4 | 3 | 0 | 5 | **延时时长**，数值（写 5 后米家 App 显示为 5 分钟，单位疑为分钟） |
| 4 | 4 | -4001 | — | 设备不支持 |
| 4 | 5 | -4001 | — | 设备不支持 |

结论：**siid=4** 下 **piid=1** = 延时开启开关（开/关），**piid=3** = 延时时长（写 5 对应 App 里 5 分钟）；仅设 piid=3 不会触发延时，需同时把 **piid=1 设为 True** 才会启动「延时开启」。

### 请验证：延时开启（时长 + 开关同时设置）

先确保乌龟灯为**关**，再执行下面命令（**同时设延时时长 piid=3 与延时开启开关 piid=1=True**），观察是否在设定时间后自动开灯：

```bash
miiocli miotdevice --ip 192.168.1.101 --token YOUR_MIOT_DEVICE_TOKEN raw_command set_properties '[{"siid":4,"piid":3,"value":1},{"siid":4,"piid":1,"value":True}]'
```

- **piid=3**：延时时长（若单位是分钟，1=1 分钟后开；若你确认 5=5 分钟，可改为 5 做 5 分钟测试）。
- **piid=1**：延时开启开关，True=开启该功能。

验证通过后，可将最终结论与可复现命令记入 [设备控制说明.md](设备控制说明.md)。

---

## 五、验证记录

- **2025-02**：在灯为**关**态下执行 `set_properties [{"siid":4,"piid":3,"value":5}]`，等待 5 秒，**设备未开启**。  
  说明：仅设 piid=3 在关态下不会触发「延时开」；可能 piid=3 表示「多少秒后**关**」（仅对当前开态有效），或需配合其他属性/动作。

- **最新发现（米家 App 对照）**：执行上述命令后，在米家 App 中看到该设备的**延迟时间被改为 5 分钟**，但**「延时开启」的开关仍为关闭**。  
  结论：**piid=3** 负责的是**延时时长**（写 5 对应 App 里 5 分钟），**没有单独触发「延时开启」**；需要再有一个「延时开启开关」被打开才会真正执行延时。  
  结合 get_properties 结果，**siid=4, piid=1** 当前为 False，推断 **piid=1 = 延时开启开关**（True=开启延时功能）。因此「延时 X 分钟后开启」应**同时设置**：piid=3 为时长、piid=1 为 True。

- **再反馈**：同时设 piid=3=1、piid=1=True 仍无效果；米家 App 里延时时间**没有变化**，可能之前 5 分钟只是默认值。需要分步再验证「配置延时开始时间」与各属性的对应关系。

---

## 六、再验证：分步确认 siid=4 各属性（请按顺序执行并看 App）

请按下面步骤依次执行，每步后**立刻看米家 App** 里该设备的「延时」相关项是否变化，并记下结果（有/无变化、变成什么）。

### 步骤 1：读取当前状态（便于对照）

执行后记下输出里 siid=4 的 piid=1、2、3 的 value，并看此时 App 里「延时时间」「延时开启」开关各是什么。

```bash
miiocli miotdevice --ip 192.168.1.101 --token YOUR_MIOT_DEVICE_TOKEN raw_command get_properties '[{"siid":4,"piid":1},{"siid":4,"piid":2},{"siid":4,"piid":3}]'
```

### 步骤 2：只改延时时长（确认 piid=3 是否驱动 App 显示）

把 **piid=3** 设为 **2**（与当前 5 不同），看 App 里「延时时间」是否变成 2 分钟。

```bash
miiocli miotdevice --ip 192.168.1.101 --token YOUR_MIOT_DEVICE_TOKEN raw_command set_properties '[{"siid":4,"piid":3,"value":2}]'
```

- 若 App 变成 2 分钟 → piid=3 确认是延时时长（单位分钟）。
- 若 App 无变化 → 可能 piid=3 只读、或不是「延时开始时间」对应的属性，需再查其他 piid 或 action。

### 步骤 3：只改「延时开启」开关（确认 piid=1 是否对应开关）

把 **piid=1** 设为 **True**，看 App 里「延时开启」开关是否打开。

```bash
miiocli miotdevice --ip 192.168.1.101 --token YOUR_MIOT_DEVICE_TOKEN raw_command set_properties '[{"siid":4,"piid":1,"value":True}]'
```

- 若 App 里开关打开 → piid=1 确认是延时开启开关。
- 若 App 无变化 → 可能 piid=1 不是该开关，或需先设 piid=3 再设 piid=1；也可尝试 **piid=2**（get 到的是 2）是否为「延时开启」开关。

### 步骤 4：若步骤 2 或 3 有反应，再试「先时长后开关」

若某一步能让 App 变化，再试：先设 piid=3 为 1，再设 piid=1 为 True（分两条命令或一条里两个对象），看 1 分钟后灯是否自动开。

请把四步的**命令输出**和**App 是否有变化**反馈过来，再根据结果写最终可用的「配置延时开始时间」指令。

### 步骤 1 反馈（当前状态）

执行 get_properties 得到：

| siid | piid | code | value |
|------|------|------|-------|
| 4 | 1 | 0 | **True** |
| 4 | 2 | 0 | 2 |
| 4 | 3 | 0 | **10** |

**与 App 不一致**：此时米家 App 里显示 **延迟时间 5 分钟、延时开启 关闭**，与设备返回的 piid=1=True、piid=3=10 不对应。可能：(1) **piid=1 语义相反**（True=延时开启关，False=延时开启开），(2) piid 与 App 不是一一对应，或 (3) App 与设备有缓存/不同步。

**建议反向验证**（先确认谁驱动谁）：
- 设 **piid=1=False**，立刻看 App 里「延时开启」是否变为**打开**；若会，则 piid=1 为「反向」开关（False=开）。
- 设 **piid=3=5**，立刻看 App 里「延迟时间」是否变为 **5 分钟**；若会，则 piid=3 对应时长且单位应为分钟。

**反馈**：执行 `set_properties [{"siid":4,"piid":1,"value":False}]` 后，**App 里「延时开启」没有变成打开**。→ piid=1 很可能不是 App 上的「延时开启」开关。

**反馈**：执行 `set_properties [{"siid":4,"piid":3,"value":2}]` 后（code 0 成功），**App 里「延迟时间」没有变成 2 分钟**。→ piid=3 的写入未驱动 App 显示，可能 App 的「延迟时间」来自云端/缓存或由**动作（action）**下发，而非本地 set_properties；或该型号延时功能主要走云端逻辑。

**当前结论（cuco.plug.v3）**：siid=4 下 piid=1、2、3 均可读且 piid=1/3 可写（code 0），但**我们测试的 set 均未使米家 App 的「延时开启」「延迟时间」产生可见变化**，也未观察到设备在设定时间后自动开/关。延时功能在本机上可能需通过 **action** 或 App/云端路径配置，或需查阅该型号在 [home.miot-spec.com](https://home.miot-spec.com/s/) 的完整规格（含 action 列表）再试。

---

## 七、联网查阅结论（cuco.plug.v3 延时/定时 用什么调用）

以下为联网检索后的**有据结论**，不猜测。

### 1. 设备与协议

- **cuco.plug.v3** 为小米生态 WiFi 智能插座（常见为网购/第三方品牌接入米家），走 **MIOT 协议**，开关已确认用 `set_properties`，siid=2, piid=1。
- 小米 IoT 平台下发方式有三种：**get_properties**、**set_properties**、**action**（见 [小米 IoT 模组串口通信说明](https://blakadder.github.io/miot/)：`get_down` 可返回 `set_properties` 或 **action**）。延时/定时可能由**属性**或**动作**实现。

### 2. 公开资料中与「插座 + 定时/延时」相关的说法

- **python-miio Issue #1860**（[链接](https://github.com/rytilahti/python-miio/issues/1860)）：有人用与当前相同的 siid=4 映射（on_duration piid 1、off_duration piid 2、countdown piid 3、task_switch piid 4、countdown_info piid 5）对**小米智能插座**执行 `set_properties`（如 siid=4, piid=3, value=False），结果 **“doesn’t have much effect”**，与我们在 cuco.plug.v3 上的现象一致。
- 多份资料（含 MIOT 规范、hass-xiaomi-miot 等）提到插座类定时常用 **siid=4**，属性名包括 on_duration、off_duration、countdown 等，但**未给出 cuco.plug.v3 的「延时开启」可成功调用的具体方法（set 哪几个属性、或调用哪个 action、aiid 与 in 格式）**。
- **home.miot-spec.com** 按型号提供完整规格（含 Services/Actions），是查 siid/piid/aiid 的常用来源；检索时该站对 cuco.plug.v3 的页面请求超时，未能拿到该型号的**动作（action）列表与 aiid**。

### 3. 结论（对应能力用什么调用）

- **开关（开/关）**：已明确，用 **set_properties**，siid=2, piid=1, value=True/False。
- **延时开启 / 延迟时间（米家 App 里可见的「延时开启」「延迟时间」）**：  
  **在公开文档与社区讨论中，未找到 cuco.plug.v3 的、经实测可用的调用方式**。  
  可能情况包括：（1）由 **action** 触发（需规格中的 siid/aiid 及 in 参数），（2）由 App/云端写属性或发指令、设备仅同步状态而本地 set 不直接驱动 UI/行为，（3）固件或型号差异导致与通用插座映射不一致。  
  当前**不能**根据公开资料给出「延时开启」或「设置延迟时间」的确定 API（set_properties 具体写哪些项，或 action 的 aiid 与 in）。

### 4. 建议的下一步（不猜测、需用户侧可操作信息）

1. **查完整规格**：在浏览器打开 [home.miot-spec.com/s/](https://home.miot-spec.com/s/) 搜索 **cuco.plug.v3**，进入产品页后查看「规格」中的 **Services** 与 **Actions**，若有「延时」/「倒计时」相关 action，记下 siid、aiid 及参数说明，再在本机用 `raw_command action '{"siid":...,"aiid":...,"in":[...]}'` 验证。
2. **问厂商/卖家**：向该款小米 WiFi 插座的品牌或卖家索要「局域网控制」或「开发者」文档，问清延时/定时是属性还是 action、以及具体 siid/piid/aiid 与参数格式。
3. **抓包对比**：在米家 App 中操作「延时开启」或修改「延迟时间」时抓包，对比云端/App 下发的 method（set_properties 还是 action）及参数，再在本地用 miiocli 复现相同调用。

若你从规格站或厂商处拿到 cuco.plug.v3 的 action 列表或延时相关说明，可把 siid/aiid/in 或属性定义贴出，再据此写出可复现的调用命令并更新本文档。

### 补充：全网搜索结果（包括中英文论坛、博客、GitHub）

1. **有人提到 countdown 可写**（[来源](https://www.smyz.net/pc/11167.html)）：siid=4, piid=3，value 为秒数；格式为 `set_properties "[{'did': 'countdown', 'siid': 4, 'piid': 3, 'value': <秒数>}]"`。  
   **但**：你本机用相同 siid/piid 试过（value=5），App 未响应、设备未执行；其他人（[python-miio #1860](https://github.com/rytilahti/python-miio/issues/1860)）用相同方式也 "doesn't have much effect"。

2. **产品功能存在**（[来源](https://bk.taobao.com/k/zhinengchazuo_13189/86c1a72d42cd0bfbbec1a43b7e7e9d48.html)、[来源](https://v2ex.com/t/876935)）：米家智能插座 3 支持**本地计时**，即使断网也能执行倒计时关；App 里可设「延时 X 分钟后开/关」。  
   **但**：多数讨论是「App 里手动设」；命令行控制的文章里「虽然搜索结果中没有直接的定时/延时命令示例」（[来源](https://blog.csdn.net/Edward1027/article/details/144564941)）。

3. **Home Assistant 里的延时**（[来源](https://nolebase.ayaka.io/zh-cn/%E7%AC%94%E8%AE%B0/%F0%9F%A7%B1%20%E5%9F%BA%E7%A1%80%E8%AE%BE%E6%96%BD/%F0%9F%8F%A0%20%E7%89%A9%E8%81%94%E7%BD%91/%F0%9F%8C%B3%20home%20assistant/%E7%B1%B3%E5%AE%B6%E8%AE%BE%E5%A4%87%E8%81%94%E5%8A%A8%20home%20assistant%20%E8%87%AA%E5%8A%A8%E5%8C%96%E6%97%B6%E5%BB%B6%E8%BF%9F%E5%BE%88%E9%AB%98)）：用 HA automation + `delay` 动作实现「延时开启」，即外部脚本等 X 秒后发开命令，**不是调设备本身的倒计时功能**。

4. **chuangmi.plug.v3 的 python-miio 类**（[源码](https://raw.githubusercontent.com/rytilahti/python-miio/master/miio/integrations/chuangmi/plug/chuangmi_plug.py)）：只有 `on()` / `off()` / `usb_on()` / `set_led()`，**没有 countdown / delay 相关方法**。

**结论（全网搜索后）**：  
- **功能存在**：米家插座 3 支持延时/倒计时，App 里可用，设备本地能执行（断网也行）。  
- **本地 API 调用方式未公开或不可用**：全网（中英文社区、博客、GitHub issue）里，**没有找到「用 miiocli 或 python-miio 在局域网设置插座的延时开启/倒计时，设备按时自动开/关」的成功案例或可复现命令**。  
- 多数延时方案是：(1) 米家 App 里手动设，或 (2) 外部脚本 sleep + 发开关命令（不调设备自己的倒计时）。  
- 你在本机验证时：siid=4 的 piid=1/2/3 均可读可写（code 0），但写入后 App 无反应、设备未按时执行。

**若必须用「设备本身的延时开启」**：需要从厂商/卖家那里获取开发者文档，或在米家 App 里抓包看设「延时开启」时的下发内容（可能是云端 API 或特殊格式的 action），目前公开资料里查不到可用的本地调用方式。

---

## 八、抓包验证结论（2026-02-10）

### 抓包发现

在 iPhone 米家 App 里点击「延时关闭」，通过 Charles 抓包到两个 HTTPS 请求：

1. **`https://core.api.mijia.tech/app/device/batchdevicedatas`**  
   查询设备当前状态（准备创建场景）

2. **`https://api.mijia.tech/app/scene/edit`**  
   **创建/编辑场景**（定时场景）

### 关键信息

- **Header**：`miot-encrypt-algorithm: ENCRYPT-RC4`，请求体用 RC4 加密
- **认证**：需要 `serviceToken`（在 Cookie 里）
- **请求体**：`data=` 后面是加密的密文，无法直接看到参数

### 结论

**米家 App 的「延时开启/关闭」功能，不是直接调用设备的 miot 属性（siid=4），而是通过米家云端 API 创建定时场景实现的。**

具体流程：
1. App 调用云端 API `/app/scene/edit`，创建一个「X 分钟后执行开/关」的场景
2. 场景由**云端计时**（不是设备本地）
3. 到时间后，云端下发 `set_properties` 开/关命令给设备
4. 设备执行开/关动作

这就是为什么：
- ❌ 本地 `miiocli` 写 siid=4 属性无效（设备收到了但不会触发倒计时逻辑）
- ✅ App 里能用（走的是云端场景 API，需要联网、需要 serviceToken）

### 本地实现延时的两种方案

#### 方案 1：调用米家云端 API（复杂）
- 需要用 `python-miio` 的 `miio.cloud` 模块登录获取 `serviceToken`
- 模拟 `/app/scene/edit` 请求，创建定时场景
- 需要逆向 RC4 加密算法（或参考 python-miio 源码）
- **优点**：使用设备本身的倒计时功能
- **缺点**：依赖云端、需要联网、实现复杂

#### 方案 2：外部脚本实现延时（简单，推荐）
既然设备的倒计时功能无法通过本地 API 直接触发，可以用外部脚本实现：

```python
#!/usr/bin/env python3
import sys, time, subprocess, os

def delayed_control(ip: str, token: str, action: str, delay_seconds: int):
    """延时开/关：等待指定秒数后执行"""
    print(f"将在 {delay_seconds} 秒后{action}设备...")
    time.sleep(delay_seconds)
    
    value = "True" if action == "开启" else "False"
    bin_dir = os.path.dirname(os.path.abspath(sys.executable))
    miiocli = os.path.join(bin_dir, "miiocli")
    if not os.path.isfile(miiocli):
        miiocli = "miiocli"
    
    cmd = [
        miiocli, "miotdevice",
        "--ip", ip, "--token", token,
        "raw_command", "set_properties",
        f'[{{"siid":2,"piid":1,"value":{value}}}]'
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
    if result.returncode == 0:
        print(f"✓ 设备已{action}")
    else:
        print(f"✗ 失败: {result.stderr or result.stdout}")

if __name__ == "__main__":
    # 示例：延时30秒后开启乌龟灯
    delayed_control(
        ip="192.168.1.101",
        token="YOUR_MIOT_DEVICE_TOKEN",
        action="开启",  # 或 "关闭"
        delay_seconds=30
    )
```

**优点**：
- 简单、本地运行、不依赖云端
- 不需要联网（只要设备在局域网）
- 可集成到 `hzr_mcp.py`，通过语音「30 秒后开启乌龟灯」触发

**缺点**：
- 计时在脚本运行的机器上（不是设备本身）
- 脚本进程必须一直运行（直到延时时间到）
