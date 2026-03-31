# 备份：当前可用配置（连接远端小智官方服务 tenclass.net 正常）
# 备份时间可参考文件修改时间；恢复时复制为 config.py 即可
# 完全按官方 README：https://github.com/idootop/open-xiaoai/blob/main/examples/xiaozhi/README.md
# 使用小智官方 server（tenclass.net），暂不接自建小智
import asyncio


async def before_wakeup(speaker, text, source):
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
            "豆包豆包",
            "你好小智",
            "小智同学",
            "hi siri",
        ],
        "timeout": 20,
        "before_wakeup": before_wakeup,
        "after_wakeup": after_wakeup,
    },
    "vad": {
        "boost": 150,        # 小爱录音音量较小，需放大（见 GitHub Issue 反馈）
        "threshold": 0.05,
    },
    "xiaozhi": {
        "OTA_URL": "https://api.tenclass.net/xiaozhi/ota/",
        "WEBSOCKET_URL": "wss://api.tenclass.net/xiaozhi/v1/",
        "WEBSOCKET_ACCESS_TOKEN": "",
        "DEVICE_ID": "",
        "VERIFICATION_CODE": "",
    },
}
