# MIOT 规格与属性说明（siid / piid）

本文档说明 MIOT 协议里 **siid**、**piid** 的含义，以及从哪里查「某设备型号对应哪些属性、做什么用」的文档。设备控制的具体指令见 [设备控制说明.md](设备控制说明.md)。

---

## siid 和 piid 是什么

- **siid**（Service ID）  
  **服务 ID**，表示设备里的一个**功能模块**（一个「服务」）。  
  例如：`siid=2` 常表示「开关/电源」服务，`siid=4` 常表示「定时/倒计时」服务。不同型号会有不同的 siid 数量和含义。

- **piid**（Property ID）  
  **属性 ID**，表示**该服务下的某一个具体属性**。  
  例如：在「开关服务」(siid=2) 里，`piid=1` 通常就是「开/关」这一路。  
  所以 **`siid=2, piid=1`** 表示「第 2 号服务里的第 1 号属性」，在 cuco.plug.v3 上就是插座/灯的那一路开关，`value: true` 为开，`value: false` 为关。

---

## 有没有「设备 ↔ 属性」的官方文档

**协议层面的规范有**，但**「每个设备型号对应哪些 siid/piid、用来做什么」的官方大表没有**。  
实际使用时需要结合「协议规范」+「按型号查规格/社区映射」。

---

## 官方协议规范（小米 GitHub）

- **仓库**：[MiEcosystem/miot-spec-doc](https://github.com/MiEcosystem/miot-spec-doc)  
- **内容**：讲 MIOT **协议本身**（服务、属性、动作的抽象定义），不按设备型号列 siid/piid。
- **常用文件**：
  - [小米IOT设备规范v2.md](https://github.com/MiEcosystem/miot-spec-doc/blob/master/小米IOT设备规范v2.md)
  - [小米IOT控制端API.md](https://github.com/MiEcosystem/miot-spec-doc/blob/master/小米IOT控制端API.md)

这里能搞清楚 siid/piid 在协议里的含义；**具体到某个型号**（如 cuco.plug.v3）的 siid/piid 对应关系，需要从下面途径查。

---

## 按设备型号查 siid/piid 的途径

### 1. 米家产品规格站（社区/第三方）

- **地址**：<https://home.miot-spec.com/s/>
- **用法**：按**设备型号**搜索（如 `cuco.plug.v3`），进入产品页后点「规格」，可看到该型号的**服务、属性**列表，包含 siid、piid、含义、读写权限等。
- **说明**：数据多来自社区或抓包，不是小米官方文档站，但查具体型号很实用。

### 2. python-miio 代码

- **仓库**：[rytilahti/python-miio](https://github.com/rytilahti/python-miio)
- **用法**：在代码里搜索设备型号或 `miot`，部分型号有写好的 siid/piid 映射（如 `power: siid=2, piid=1`）。
- **说明**：不是所有型号都有，且以代码为准，没有单独的「设备→属性」文档页。

### 3. Home Assistant 相关项目

- 如 **hass-xiaomi-miot**、**Xiaomi Miot Auto** 等，会为大量型号维护可用的 siid/piid 映射。
- **用法**：在对应项目的 issue、wiki 或代码里搜索设备型号（如 `cuco.plug.v3`），可看到该型号的属性和用法。

---

## 小结

| 需求 | 推荐来源 |
|------|----------|
| siid/piid 在协议里是什么意思 | 小米 [MiEcosystem/miot-spec-doc](https://github.com/MiEcosystem/miot-spec-doc) |
| 某型号（如 cuco.plug.v3）的 siid/piid 做什么 | [home.miot-spec.com](https://home.miot-spec.com/s/)、python-miio、hass-xiaomi-miot 等按型号查 |
