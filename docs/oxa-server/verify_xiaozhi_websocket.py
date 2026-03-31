#!/usr/bin/env python3
"""
模拟 Open-XiaoAI 用 WebSocket 连小智 server，发 hello 验证链路。
用法：
  从本机连 NAS 上小智：python3 verify_xiaozhi_websocket.py --url ws://192.168.1.100:8000/xiaozhi/v1/
  在 NAS 容器内连：  python3 verify_xiaozhi_websocket.py --url ws://xiaozhi-esp32-server:8000/xiaozhi/v1/
"""
import argparse
import asyncio
import json
import sys

# 与 Open-XiaoAI 一致的 hello 消息
HELLO_MSG = {
    "type": "hello",
    "version": 1,
    "transport": "websocket",
    "audio_params": {
        "format": "opus",
        "sample_rate": 16000,
        "channels": 1,
        "frame_duration": 60,
    },
}


async def run(url: str, device_id: str, client_id: str, token: str, timeout: float):
    try:
        import websockets
    except ImportError:
        print("请先安装: pip install websockets")
        sys.exit(1)

    headers = {
        "Authorization": f"Bearer {token}" if token else "Bearer",
        "Protocol-Version": "1",
        "Device-Id": device_id,
        "Client-Id": client_id,
    }
    print(f"[验证] 连接 {url} ...")
    print(f"[验证] Device-Id={device_id} Client-Id={client_id}")
    try:
        async with websockets.connect(
            url,
            additional_headers=headers,
            open_timeout=timeout,
            close_timeout=5,
        ) as ws:
            print("[验证] WebSocket 已连接，发送 hello ...")
            await ws.send(json.dumps(HELLO_MSG))
            # 收几条服务器响应
            for i in range(5):
                try:
                    msg = await asyncio.wait_for(ws.recv(), timeout=timeout)
                    if isinstance(msg, bytes):
                        print(f"[验证] 收到二进制 len={len(msg)}")
                    else:
                        pre = msg[:200] + "..." if len(msg) > 200 else msg
                        print(f"[验证] 收到: {pre}")
                        data = json.loads(msg)
                        if data.get("type") == "hello":
                            print("[验证] 已收到服务器 hello，链路正常。")
                            return 0
                except asyncio.TimeoutError:
                    print("[验证] 等待服务器消息超时")
                    break
            return 0
    except Exception as e:
        print(f"[验证] 失败: {type(e).__name__}: {e}")
        return 1


def main():
    p = argparse.ArgumentParser(description="模拟 WebSocket 连小智 server 发 hello")
    p.add_argument("--url", default="ws://192.168.1.100:8000/xiaozhi/v1/", help="小智 WebSocket 地址")
    p.add_argument("--device-id", default="02:42:c0:a8:90:02", help="Device-Id")
    p.add_argument("--client-id", default="verify-ws-client", help="Client-Id")
    p.add_argument("--token", default="", help="Bearer token，可选")
    p.add_argument("--timeout", type=float, default=10.0, help="连接/收包超时秒数")
    args = p.parse_args()
    exit(asyncio.run(run(args.url, args.device_id, args.client_id, args.token, args.timeout)))


if __name__ == "__main__":
    main()
