# Open-XiaoAI + oxa-server 增强（NAS 部署）

基于 [pu-007/oxa-server](https://github.com/pu-007/oxa-server)，在官方 xiaozhi 示例上增加：

- **免唤醒指令**：直接说「打开新风机」「关新风机」等即可执行，无需先说「小爱同学」或「爸爸最帅」
- **爸爸最帅** 唤醒小智，进入连续对话
- **bridge_server**：新风机等指令通过 HTTP 调用你 NAS 上的 `bridge_server`（hzr_mcp）
- **自建 xiaozhi**：对话走 NAS 上的 xiaozhi-esp32-server

## 前置条件

- 小爱音箱已刷 Open-XiaoAI 固件，并已安装运行 Client（连到 NAS 4399）
- NAS 上已运行：Open-XiaoAI Server（4399）、xiaozhi-esp32-server（8000）、bridge_server（8765）

## 在 NAS 上部署增强版

### 1. 上传文件到 NAS

将本目录下这些内容放到 NAS 的 Open-XiaoAI-Server 目录（与现有 `config.py`、`docker-compose.yml` 同级）：

- `config_oxa.py`（增强配置）
- `oxa_ext/` 整个目录（`__init__.py`、`type_defines.py`、`utils.py`、`__main__.py`）

例如 NAS 路径：

```
/path/to/nas/udata/real/YOUR_USER_ID/docker/Open-XiaoAI-Server/
├── config_oxa.py
├── oxa_ext/
│   ├── __init__.py
│   ├── __main__.py
│   ├── type_defines.py
│   └── utils.py
├── config.py          # 可保留作备份
└── docker-compose.yml
```

### 2. 修改 docker-compose 使用增强配置

在 `docker-compose.yml` 中把挂载的 config 改为 `config_oxa.py`，并增加 `oxa_ext` 挂载：

```yaml
services:
  open-xiaoai-xiaozhi:
    image: docker.1ms.run/idootop/open-xiaoai-xiaozhi:latest
    container_name: open-xiaoai-xiaozhi
    restart: always
    ports:
      - "4399:4399"
    volumes:
      - ./config_oxa.py:/app/config.py
      - ./oxa_ext:/app/oxa_ext
    # ... 其余不变
```

### 3. 重启容器

```bash
cd /path/to/nas/udata/real/YOUR_USER_ID/docker/Open-XiaoAI-Server
docker compose down
docker compose up -d
```

### 4. 修改配置（可选）

- **BRIDGE_BASE**：在 `config_oxa.py` 里改为你 NAS 的 IP 和 bridge_server 端口（默认 `http://192.168.1.100:8765`）
- **免唤醒指令**：在 `direct_vad_command_map` 里增删键值对，键为「说出的那句话」，值为动作列表（`bridge_call`、`xiaoai_play`、小爱原生指令等）
- **唤醒词**：`direct_vad_wakeup_keywords` 当前为 `["爸爸最帅"]`，可改或增加
- **xiaozhi**：`xiaozhi_config` 里已是 NAS 自建地址，验证码见 `VERIFICATION_INFO` 说明

## 使用方式

- 说 **「爸爸最帅」**：唤醒小智，进入连续对话（走 NAS xiaozhi-esp32-server）
- 直接说 **「打开新风机」「关新风机」**：免唤醒，调 bridge_server 执行脚本，并可播报「正在打开/关闭新风机」等
- 对小爱说 **「召唤小智」**：抢麦并唤醒小智

## 唤醒无响应 / 从未听到验证码时的排查

根据 [官方 xiaozhi 文档](https://github.com/idootop/open-xiaoai/tree/main/examples/xiaozhi)：

1. **确认音箱已接到 NAS 的 Open-XiaoAI Server**  
   必须先在小爱音箱上运行 **Rust 补丁**，让音箱连到 `NAS_IP:4399`。若未做这一步，说任何唤醒词都不会有反应。

2. **先试「你好小智」**  
   当前配置里已加「你好小智」，若「爸爸最帅」没反应，可先试「你好小智」看是否有回复，用来判断是连接问题还是识别问题。

3. **查验证码**  
   首次与 xiaozhi 建立对话时，验证码会在 **终端/日志** 里打印。在 NAS 上执行：
   ```bash
   docker logs open-xiaoai-xiaozhi
   ```
   在输出里找验证码，再到小智管理后台绑定设备。

4. **提高灵敏度**  
   若确认已连上但仍不唤醒，可在配置里把 `vad.threshold` 再调低（例如 `0.03`），然后重启容器。

5. **用「纯官方」配置排查**  
   若怀疑与 oxa 增强有关，可临时改用 `config_simple.py`（与官方格式一致、不依赖 oxa_ext）：
   - 把 `docker-compose.yml` 里挂载改为 `./config_simple.py:/app/config.py`
   - 去掉 `./oxa_ext:/app/oxa_ext` 这一行
   - `docker compose down && docker compose up -d`
   - 再试「爸爸最帅」或「你好小智」。若这样能唤醒，再切回 `config_oxa.py` + `oxa_ext` 排查。

## 参考

- [open-xiaoai xiaozhi 示例](https://github.com/idootop/open-xiaoai/tree/main/examples/xiaozhi/README.md)
- [pu-007/oxa-server](https://github.com/pu-007/oxa-server)
