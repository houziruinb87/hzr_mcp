# Home Assistant + HomePod (Siri) 控制 hzr_mcp 设备

通过「Hi Siri，打开加湿器」等指令，让 HomePod 控制 hzr_mcp 里的小米设备。

## 原理

```
Siri → HomePod → HomeKit → Home Assistant (HomeKit 桥接) → 调用 hzr_mcp 脚本
```

1. 在 Home Assistant 里用 **Command Line** 或 **REST** 触发 hzr_mcp 的 control 脚本
2. 把这些实体通过 **HomeKit 桥接** 暴露给 Apple 家庭
3. HomePod/Siri 即可控制

---

## 方案一：HA 直接执行 docker（推荐，HA 能执行 docker 时）

**前提**：Home Assistant 能执行宿主机上的 `docker`（例如容器启动时挂载了 docker.sock）。

1. 在 HA **配置文件** 或 **设置 → 设备与服务 → 添加集成 → Command Line** 中，添加「加湿器」开关：
   - **开**：`docker exec hzr_mcp python /app/xiaomi/jiashiqi/control.py on`
   - **关**：`docker exec hzr_mcp python /app/xiaomi/jiashiqi/control.py off`
   - 容器名 `hzr_mcp` 请按你实际名称修改。

2. 在 HA：**设置 → 设备与服务 → HomeKit → 添加桥接**，选择刚创建的「加湿器」等实体，暴露到 Apple 家庭。

3. 在 iPhone「家庭」App 里即可用 Siri 或 HomePod 控制。

完整 YAML 示例见 `configuration_example.yaml` 中的「方案一」注释块。

---

## 方案二：HTTP 桥接服务（HA 不能执行 docker 时）

在 NAS 上运行一个小型 HTTP 服务，由它执行 `docker exec`，HA 只负责发 HTTP 请求。

### 1. 在 NAS 上运行桥接服务

```bash
# 安装依赖（若未安装）
pip install flask

# 进入目录并启动（请把路径换成你 NAS 上 hzr_mcp 的路径）
cd /path/to/hzr_mcp/homeassistant
python3 bridge_server.py
```

可选环境变量：
- `HZR_MCP_CONTAINER`：hzr_mcp 容器名，默认 `hzr_mcp`
- `BRIDGE_PORT`：端口，默认 `8765`

建议用 systemd 或 Docker 常驻运行，并确保 NAS 防火墙放行 8765 端口。

### 2. 在 Home Assistant 里配置

- **设置 → 设备与服务 → 辅助元素 → 创建辅助元素 → 开关**：创建两个「开关」分别调用「开/关」服务；
- 或使用 **开发者工具 → 服务** 先测试：
  - 服务选 `rest_command.jiashiqi_on`（需先在 configuration.yaml 里配置 rest_command，见下方）。

在 `configuration.yaml` 里添加（把 `NAS的IP` 换成实际 IP，如 `192.168.1.100`）：

```yaml
rest_command:
  jiashiqi_on:
    url: "http://NAS的IP:8765/jiashiqi/on"
    method: POST
  jiashiqi_off:
    url: "http://NAS的IP:8765/jiashiqi/off"
    method: POST
```

再用 **Template 开关** 或 **辅助元素** 把「加湿器」做成一个开关，开时调用 `rest_command.jiashiqi_on`，关时调用 `rest_command.jiashiqi_off`。

### 3. 暴露给 HomeKit

同方案一：**设置 → 设备与服务 → HomeKit → 添加桥接**，选择该「加湿器」实体。

更多设备（乌龟灯、走廊灯、全屋灯）的 rest_command 与 URL 见 `configuration_example.yaml` 中的「方案二」注释块。

---

## 支持的设备与 URL（方案二）

| 设备   | 开 | 关 |
|--------|-----|-----|
| 加湿器 | POST `/jiashiqi/on`  | POST `/jiashiqi/off`  |
| 乌龟灯 | POST `/wuguideng/on` | POST `/wuguideng/off` |
| 走廊灯 | POST `/zoulangdeng/on` | POST `/zoulangdeng/off` |
| 全屋灯 | POST `/quanwudeng/on` | POST `/quanwudeng/off` |
