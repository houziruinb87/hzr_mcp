# xiaomi

通过 MCP 接入点控制小米/米家 WiFi 设备（如乌龟灯）。流程：小智说「开启 乌龟灯」→ 大模型调用 MCP 工具 → 本目录下脚本 → 对设备发 miIO 命令。

## 实现步骤

1. **验证 NAS 上 hzr_mcp 容器能否执行 miiocli**（当前步骤）
2. 验证脚本能控制指定设备（如乌龟灯）
3. 在 hzr_mcp 中增加 MCP 方法，调用本目录脚本

## 第一步：验证容器内 miiocli

依赖已加入 `requirements.txt`（`python-miio`），容器启动时 entrypoint 会执行 `pip install -r requirements.txt`，因此需**重新构建镜像**后，再在容器内验证。

### 1. 在 NAS 上拉代码并重建镜像

```bash
cd /data_n003/data/udata/real/18510411307/docker/mcp
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
  miiocli miotdevice --ip 192.168.50.220 --token <TOKEN> raw_command set_properties '[{"siid":2,"piid":1,"value":True}]'
  # 关
  miiocli miotdevice --ip 192.168.50.220 --token <TOKEN> raw_command set_properties '[{"siid":2,"piid":1,"value":False}]'
  ```
  若不对，可用 `miiocli miotdevice --ip <IP> --token <TOKEN> --help` 或查 [python-miio 文档](https://python-miio.readthedocs.io/) 里 MiotDevice / get_properties 的 siid/piid 说明。
