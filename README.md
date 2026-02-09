# hzr_mcp

运行于**极空间 NAS 上 office 容器**内的 MCP 服务，提供计算与 adb 能力，对应远端工程：  
https://remote-access-8929.zconnect.cn/ai/hzr_mcp

## 功能

- **calculator**：Python 表达式数学计算（math / random）
- **adb_devices**：列出当前 adb 已连接设备
- **adb_connect**：通过 WiFi（如飞鼠虚拟网 IP）连接 Android 设备
- **install_android_apk**：按人名从 `name_to_ip.json` 解析 IP，向对应手机安装 store 下的 APK

## 环境要求

- Python 3.10+
- 极空间 office 容器内已配置 Android SDK（`source /workspace/tools/env.sh` 或 `.bashrc` 已加载），`adb` 在 PATH 中

## 快速开始

1. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```

2. 运行（stdio，供 MCP 客户端调用）：
   ```bash
   python -m hzr_mcp
   ```

3. 配置人名与手机 IP：编辑 `name_to_ip.json`，或通过环境变量 `ANDROID_NAME_TO_IP` 传入 JSON 字符串。

## 项目结构

- `hzr_mcp.py`：MCP 工具实现
- `mcp_config.json`：本地 stdio 配置示例
- `name_to_ip.json`：人名 → 手机 IP 映射（飞鼠/局域网 IP）
- `requirements.txt`：Python 依赖

## License

MIT
