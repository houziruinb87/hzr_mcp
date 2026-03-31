#!/usr/bin/env python3
"""
仅用标准库模拟 WebSocket 连小智 server，发 hello 验证链路。
不依赖 websockets 包，可在 NAS 或容器内运行。
用法：python3 verify_xiaozhi_websocket_stdlib.py [--url ws://IP:8000/xiaozhi/v1/]
"""
import argparse
import base64
import json
import os
import socket
import struct
import sys

# 与 Open-XiaoAI 一致的 hello
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


def parse_ws_url(url):
    assert url.startswith("ws://"), "仅支持 ws://"
    url = url[5:]
    if "/" in url:
        host_port, path = url.split("/", 1)
        path = "/" + path
    else:
        host_port, path = url, "/"
    if ":" in host_port:
        host, port = host_port.rsplit(":", 1)
        port = int(port)
    else:
        host, port = host_port, 80
    return host, port, path


def websocket_connect(host, port, path, headers, timeout=10):
    key = base64.b64encode(os.urandom(16)).decode()
    req = (
        f"GET {path} HTTP/1.1\r\n"
        f"Host: {host}:{port}\r\n"
        "Upgrade: websocket\r\n"
        "Connection: Upgrade\r\n"
        f"Sec-WebSocket-Key: {key}\r\n"
        "Sec-WebSocket-Version: 13\r\n"
    )
    for k, v in headers.items():
        req += f"{k}: {v}\r\n"
    req += "\r\n"

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(timeout)
    s.connect((host, port))
    s.send(req.encode())
    buf = b""
    while b"\r\n\r\n" not in buf:
        buf += s.recv(4096)
        if not buf:
            s.close()
            return None, "无响应"
    head, _ = buf.split(b"\r\n\r\n", 1)
    first_line = head.decode().split("\r\n")[0]
    if "101" not in first_line and "Switching" not in first_line:
        s.close()
        return None, head.decode()[:500]
    return s, None


def send_ws_text(sock, text):
    data = text.encode("utf-8")
    mask = os.urandom(4)
    payload = bytes(b ^ mask[i % 4] for i, b in enumerate(data))
    length = len(data)
    if length < 126:
        hdr = struct.pack(">BB", 0x81, 0x80 | length)
    else:
        hdr = struct.pack(">BBH", 0x81, 0x80 | 126, length)
    sock.send(hdr + mask + payload)


def recv_ws_frame(sock, timeout=10):
    sock.settimeout(timeout)
    h = sock.recv(2)
    if len(h) < 2:
        return None, None
    opcode = h[0] & 0x0F
    masked = (h[1] & 0x80) != 0
    length = h[1] & 0x7F
    if length == 126:
        length = struct.unpack(">H", sock.recv(2))[0]
    elif length == 127:
        length = struct.unpack(">Q", sock.recv(8))[0]
    if masked:
        mask = sock.recv(4)
        payload = sock.recv(length)
        payload = bytes(b ^ mask[i % 4] for i, b in enumerate(payload))
    else:
        payload = sock.recv(length)
    return opcode, payload


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--url", default="ws://192.168.1.100:8000/xiaozhi/v1/")
    p.add_argument("--device-id", default="02:42:c0:a8:90:02")
    p.add_argument("--client-id", default="verify-ws-client")
    p.add_argument("--timeout", type=float, default=10.0)
    args = p.parse_args()

    host, port, path = parse_ws_url(args.url)
    headers = {
        "Authorization": "Bearer",
        "Protocol-Version": "1",
        "Device-Id": args.device_id,
        "Client-Id": args.client_id,
    }
    print(f"[验证] 连接 {host}:{port}{path} ...")
    sock, err = websocket_connect(host, port, path, headers, args.timeout)
    if err:
        print(f"[验证] 握手失败: {err}")
        return 1
    print("[验证] WebSocket 已连接，发送 hello ...")
    send_ws_text(sock, json.dumps(HELLO_MSG))
    for _ in range(5):
        op, payload = recv_ws_frame(sock, args.timeout)
        if op is None:
            break
        if op == 0x01 and payload:
            try:
                text = payload.decode("utf-8")
                pre = text[:300] + "..." if len(text) > 300 else text
                print(f"[验证] 收到: {pre}")
                data = json.loads(text)
                if data.get("type") == "hello":
                    print("[验证] 已收到服务器 hello，链路正常。")
                    sock.close()
                    return 0
            except Exception:
                print(f"[验证] 收到二进制 len={len(payload)}")
        elif op == 0x08:
            print("[验证] 服务器关闭连接")
            break
    sock.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
