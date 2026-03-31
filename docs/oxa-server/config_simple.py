# -*- coding: utf-8 -*-
# 完全按官方 config 格式，使用官方小智云端（tenclass.net），不连 NAS 自建 xiaozhi。
# 不依赖 oxa_ext，只挂载此文件为 /app/config.py 即可。
# 参考：https://github.com/idootop/open-xiaoai/tree/main/examples/xiaozhi

import asyncio


async def before_wakeup(speaker, text, source):
    """处理收到的用户消息，并决定是否唤醒小智 AI。source: 'kws'=关键词唤醒, 'xiaoai'=小爱收到指令"""
    if source == "kws":
        await speaker.play(text="你好主人，我是小智，请问有什么吩咐？")
        return True
    if source == "xiaoai" and text == "召唤小智":
        await speaker.abort_xiaoai()
        await asyncio.sleep(2)
        await speaker.play(text="小智来了，主人有什么吩咐？")
        return True
    return False


async def after_wakeup(speaker):
    await speaker.play(text="主人再见，拜拜")


APP_CONFIG = {
    "wakeup": {
        "keywords": [
            "爸爸最帅",
            "你好小智",
            "豆包豆包",
        ],
        "timeout": 20,
        "before_wakeup": before_wakeup,
        "after_wakeup": after_wakeup,
    },
    "vad": {
        "threshold": 0.05,
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
