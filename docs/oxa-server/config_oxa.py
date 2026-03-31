# -*- coding: utf-8 -*-
# oxa-server 增强配置：免唤醒指令 + 爸爸最帅唤醒 + NAS 自建 xiaozhi + bridge_server 新风机
# 部署到 NAS 时复制到 Open-XiaoAI-Server 目录，并挂载 oxa_ext 后启动容器

from oxa_ext.utils import (
    map_all_to,
    map_the_switches,
    off,
    on,
    bridge_call,
    AppConfigBuilder,
    xiaoai_play,
)

# NAS 上 bridge_server 地址（与 homeassistant/bridge_server.py 一致，默认端口 8765）
BRIDGE_BASE = "http://192.168.1.100:8765"  # 改为你的 NAS IP 与 bridge_server 端口

APP_CONFIG = AppConfigBuilder(
    # 1. 唤醒小智、进入连续对话的关键词（多写几个方便测试，官方示例里「豆包豆包」识别较好）
    direct_vad_wakeup_keywords=["爸爸最帅", "你好小智", "豆包豆包"],
    # 2. 免唤醒指令：直接说即可执行，无需先说「小爱同学」或「爸爸最帅」
    direct_vad_command_map={
        # 新风机（通过 NAS bridge_server 调 hzr_mcp/airproce 脚本）
        "打开新风机": [bridge_call(BRIDGE_BASE, "/xinfengji/on"), xiaoai_play("正在打开新风机")],
        "关闭新风机": [bridge_call(BRIDGE_BASE, "/xinfengji/off"), xiaoai_play("正在关闭新风机")],
        "开新风机": [bridge_call(BRIDGE_BASE, "/xinfengji/on"), xiaoai_play("好的")],
        "关新风机": [bridge_call(BRIDGE_BASE, "/xinfengji/off"), xiaoai_play("好的")],
        "新风机开": [bridge_call(BRIDGE_BASE, "/xinfengji/on")],
        "新风机关": [bridge_call(BRIDGE_BASE, "/xinfengji/off")],
        # 可按需增加：加湿器、灯等，例如
        # **map_the_switches("加湿器", "台灯"),
    },
    # 3. 对小爱说「召唤小智」时抢麦并唤醒小智
    xiaoai_wakeup_keywords=["召唤小智"],
    # 4. 与小爱对话时拦截执行的扩展指令（可选）
    xiaoai_extension_command_map={
        "开新风机": [bridge_call(BRIDGE_BASE, "/xinfengji/on")],
        "关新风机": [bridge_call(BRIDGE_BASE, "/xinfengji/off")],
    },
    on_wakeup_play_text="哎，爸爸最帅，有什么吩咐？",
    on_execute_play_text="",
    on_exit_play_text="主人再见，拜拜",
    wakeup_timeout=20,
    vad_config={
        "threshold": 0.03,       # 调低更灵敏，唤醒词更容易触发
        "min_speech_duration": 200,
        "min_silence_duration": 700,  # 稍大一点，等你说完一整句再判定
    },
    xiaozhi_config={
        "OTA_URL": "http://192.168.1.100:8000/xiaozhi/ota/",
        "WEBSOCKET_URL": "ws://192.168.1.100:8000/xiaozhi/v1/",
        "WEBSOCKET_ACCESS_TOKEN": "",
        "DEVICE_ID": "",
        "VERIFICATION_INFO": "首次登录时验证码会在此更新；也可在 NAS 上执行 docker logs open-xiaoai-xiaozhi 查看",
        "VERIFICATION_CODE": "",
    },
).build()
