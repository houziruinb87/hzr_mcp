# xiaomi

通过 MCP 接入点控制小米/米家 WiFi 设备（如乌龟灯）。流程：小智说「开启 乌龟灯」→ 大模型调用 MCP 工具 → 本目录下脚本 → 对设备发 miIO 命令。

按设备型号与真实指令的说明见 **[设备控制说明.md](设备控制说明.md)**。本文档为环境配置与实现步骤。

## 实现步骤

1. **验证 NAS 上 hzr_mcp 容器能否执行 miiocli**（当前步骤）
2. 验证脚本能控制指定设备（如乌龟灯）
3. 在 hzr_mcp 中增加 MCP 方法，调用本目录脚本

## 第一步：验证容器内 miiocli

依赖已加入 `requirements.txt`（`python-miio`），容器启动时 entrypoint 会执行 `pip install -r requirements.txt`，因此需**重新构建镜像**后，再在容器内验证。

### 1. 在 NAS 上拉代码并重建镜像

```bash
cd /path/to/nas/udata/real/YOUR_USER_ID/docker/mcp
# 若代码在 hzr_mcp 子目录，先拉取
cd hzr_mcp && git pull && cd ..
docker compose build
docker compose up -d
```

### 2. 进入 hzr_mcp 容器执行 miiocli

```bash
docker exec -it hzr_mcp bash
```

在容器内：

```bash
# 查看版本（能输出版本号即说明 miiocli 可用）
miiocli --version

# 发现同网段小米设备（需容器与设备同网；默认桥接网络通常与宿主机同网）
miiocli discover
```

若 `miiocli discover` 能扫到设备并显示 IP、token，说明容器内已具备控制小米设备的能力，可进行第二步（写脚本控制具体设备）。

**若 discover 扫不到设备**：多半是容器与设备不在同一网段（Docker 默认桥接网络）。可尝试在 `docker-compose.yml` 中为 hzr_mcp 增加 `network_mode: host`（与 office 一致），使容器直接用宿主机网络，再执行 `miiocli discover`。

### 3. 若未重建镜像、只想先确认依赖

也可在容器内临时安装后验证：

```bash
docker exec -it hzr_mcp pip install python-miio
docker exec -it hzr_mcp miiocli --version
```

正式使用建议通过 `requirements.txt` + 重建镜像，与代码一起部署。

## Token 与控制说明

- **获取 token**： [Xiaomi-cloud-tokens-extractor](https://github.com/PiotrMachowski/Xiaomi-cloud-tokens-extractor) 只负责从小米云拉取设备列表和 token，README 里没有「如何控制设备」的用法；控制需用本项目的 python-miio / miiocli 或脚本。
- **requirements.txt** 中已固定 `click~=8.0.0`，避免与 python-miio 不兼容导致 miiocli 报错。

## 控制命令（按设备协议区分）

- **经典插座**（如 chuangmi.plug.v3）：  
  `miiocli chuangmiplug --ip <IP> --token <TOKEN> on` / `off`

- **MIOT 设备**（如 cuco.plug.v3、部分第三方插座/开关，报 `undefined command` 时）：走 MIOT 协议，用 `miotdevice`，开关多为 siid=2 piid=1。**参数按 Python 字面量传，布尔用 True/False（大写）**：
  ```bash
  # 开
  miiocli miotdevice --ip 192.168.1.101 --token <TOKEN> raw_command set_properties '[{"siid":2,"piid":1,"value":True}]'
  # 关
  miiocli miotdevice --ip 192.168.1.101 --token <TOKEN> raw_command set_properties '[{"siid":2,"piid":1,"value":False}]'
  ```
  若不对，可用 `miiocli miotdevice --ip <IP> --token <TOKEN> --help` 或查 [python-miio 文档](https://python-miio.readthedocs.io/) 里 MiotDevice / get_properties 的 siid/piid 说明。

各型号设备枚举及本环境验证过的真实指令（含 IP、token）见 **[设备控制说明.md](设备控制说明.md)**。

## 定时开 / 定时关 / 延时开 / 延时关（cuco.plug.v3 等）

这类插座在 MIOT 里通常有**定时/倒计时**能力，对应的是另一组属性，控制方式同样是 `set_properties`，只是 **siid/piid 和 value 不同**。

常见约定（不同型号可能不同，需在本机验证）：

| 含义       | 常见 siid | 常见 piid | 说明 |
|------------|-----------|-----------|------|
| 倒计时     | 4         | 3         | countdown，单位多为**秒**（如 300 = 5 分钟后执行） |
| 定时开时长 | 4         | 1         | on_duration |
| 定时关时长 | 4         | 2         | off_duration |
| 任务开关   | 4         | 4         | task_switch |
| 倒计时信息 | 4         | 5         | countdown_info（只读，用于查询当前倒计时） |

**如何确认本机 siid/piid**：在能跑 miiocli 的环境（如容器内）执行：

```bash
# 读 siid=4 的若干属性，看设备是否支持、返回值含义
miiocli miotdevice --ip <乌龟灯IP> --token <TOKEN> raw_command get_properties '[{"siid":4,"piid":1},{"siid":4,"piid":2},{"siid":4,"piid":3},{"siid":4,"piid":5}]'
```

若返回正常，则可用 **set_properties** 控制，例如（仅供参考，以你设备实际为准）：

- **延时 5 分钟后关灯**（先开灯，再设倒计时 300 秒后关）：  
  `set_properties '[{"siid":2,"piid":1,"value":True}]'` 再  
  `set_properties '[{"siid":4,"piid":3,"value":300}]'`  
  （部分设备倒计时是“当前状态维持多久后切换”，需看说明书或试一次确认语义。）

- **定时开/定时关**：多数由 on_duration / off_duration（或搭配 task_switch）设置，具体语义和取值范围需用上面的 `get_properties` 试一次或查该型号文档。

当前 MCP 只做了「开/关」；若要在小智里支持「X 分钟后关灯」等，可在 `xiaomi/wuguideng/` 下加脚本（如接收 `off_in_minutes=5`），内部调 `set_properties` 的 siid=4 相关 piid，并在 hzr_mcp 里增加对应 MCP 工具。
