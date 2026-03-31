# Open-XiaoAI Server (examples/xiaozhi) 配置文件
# 唤醒词：小智同学；后端先用小智云体验
# 部署在 NAS，端口 4399

import asyncio


async def before_wakeup(speaker, text, source):
    """
    处理收到的用户消息，并决定是否唤醒小智 AI
    - source: 'kws' 关键字唤醒 | 'xiaoai' 小爱同学收到用户指令
    """
    if source == "kws":
        await speaker.play(text="你好主人，我是小智，请问有什么吩咐？")
        return True

    if source == "xiaoai" and text == "召唤小智":
        await speaker.abort_xiaoai()
        await asyncio.sleep(2)
        await speaker.play(text="小智来了，主人有什么吩咐？")
        return True


async def after_wakeup(speaker):
    """退出唤醒状态"""
    await speaker.play(text="主人再见，拜拜")


APP_CONFIG = {
    "wakeup": {
        "keywords": ["小智同学"],
        "timeout": 20,
        "before_wakeup": before_wakeup,
        "after_wakeup": after_wakeup,
    },
    "vad": {
        "threshold": 0.10,
        "min_speech_duration": 250,
        "min_silence_duration": 500,
    },
    "xiaozhi": {
        "OTA_URL": "https://api.tenclass.net/xiaozhi/ota/",
        "WEBSOCKET_URL": "wss://api.tenclass.net/xiaozhi/v1/",
        "WEBSOCKET_ACCESS_TOKEN": "",
        "DEVICE_ID": "",
        "VERIFICATION_CODE": "",
    },
}
