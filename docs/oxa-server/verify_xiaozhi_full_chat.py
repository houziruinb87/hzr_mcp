#!/usr/bin/env python3
"""
模拟完整的小智 WebSocket 对话：hello → listen start → 发送语音(opus) → listen stop → 收 TTS/LLM。
用于验证「提问伊朗最新情况」等真实场景是否有正常返回。

依赖：仅标准库 + 可选 edge-tts/ffmpeg 生成语音。
  生成「伊朗最新情况」语音：pip install edge-tts 且系统有 ffmpeg，然后：
    edge-tts --text "伊朗最新情况" --voice zh-CN-YunxiNeural --write-media /tmp/q.wav
    ffmpeg -y -i /tmp/q.wav -acodec libopus -ar 16000 -ac 1 -frame_duration 60 -f opus /tmp/q.opus

用法：
  python3 verify_xiaozhi_full_chat.py --url ws://192.168.1.100:8000/xiaozhi/v1/ --opus-file /tmp/q.opus
  python3 verify_xiaozhi_full_chat.py --url ws://192.168.1.100:8000/xiaozhi/v1/ --text "伊朗最新情况"   # 自动生成 opus
  python3 verify_xiaozhi_full_chat.py --url ws://192.168.1.100:8000/xiaozhi/v1/   # 仅发占位音频，验证链路
"""
import argparse
import base64
import json
import os
import socket
import struct
import subprocess
import sys
import tempfile
import time

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
    first_line = buf.split(b"\r\n\r\n")[0].decode().split("\r\n")[0]
    if "101" not in first_line and "Switching" not in first_line:
        s.close()
        return None, buf.decode(errors="replace")[:500]
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


def send_ws_pong(sock, payload):
    """回复 Pong，payload 为 Ping 发来的数据（不 mask）。"""
    length = len(payload)
    if length < 126:
        hdr = struct.pack(">BB", 0x8A, length)
    else:
        hdr = struct.pack(">BBH", 0x8A, 126, length)
    sock.send(hdr + payload)


def recv_ws_frame(sock, timeout=10):
    sock.settimeout(timeout)
    try:
        h = sock.recv(2)
    except (socket.timeout, TimeoutError):
        return None, None
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


def generate_opus_from_text(text, voice="zh-CN-YunxiNeural"):
    """用 edge-tts 生成 wav，ffmpeg 转 opus（16k, 60ms）。"""
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as fw:
        wav_path = fw.name
    with tempfile.NamedTemporaryFile(suffix=".opus", delete=False) as fo:
        opus_path = fo.name
    try:
        subprocess.run(
            ["edge-tts", "--text", text, "--voice", voice, "--write-media", wav_path],
            check=True,
            capture_output=True,
        )
        subprocess.run(
            [
                "ffmpeg", "-y", "-i", wav_path,
                "-acodec", "libopus", "-ar", "16000", "-ac", "1",
                "-frame_duration", "60", "-f", "opus", opus_path
            ],
            check=True,
            capture_output=True,
        )
        with open(opus_path, "rb") as f:
            return f.read()
    finally:
        for p in (wav_path, opus_path):
            if os.path.exists(p):
                try:
                    os.unlink(p)
                except Exception:
                    pass


def wav_to_opus(wav_path):
    """用 ffmpeg 将 wav 转为 16k 单声道 60ms 帧 opus，返回字节。"""
    with tempfile.NamedTemporaryFile(suffix=".opus", delete=False) as f:
        opus_path = f.name
    try:
        subprocess.run(
            [
                "ffmpeg", "-y", "-i", wav_path,
                "-acodec", "libopus", "-ar", "16000", "-ac", "1",
                "-frame_duration", "60", "-f", "opus", opus_path
            ],
            check=True,
            capture_output=True,
        )
        with open(opus_path, "rb") as f:
            return f.read()
    finally:
        if os.path.exists(opus_path):
            try:
                os.unlink(opus_path)
            except Exception:
                pass


def get_opus_audio(args):
    """返回要发送的 opus 字节：wav 文件 / opus 文件 / TTS 生成 / 占位."""
    if getattr(args, "wav_file", None) and os.path.isfile(args.wav_file):
        try:
            return wav_to_opus(args.wav_file), "wav_file"
        except (FileNotFoundError, subprocess.CalledProcessError) as e:
            print(f"[警告] WAV 转 opus 失败: {e}")
    if args.opus_file and os.path.isfile(args.opus_file):
        with open(args.opus_file, "rb") as f:
            return f.read(), "opus_file"
    if args.text:
        try:
            return generate_opus_from_text(args.text), "tts"
        except (FileNotFoundError, subprocess.CalledProcessError) as e:
            print(f"[警告] 无法用 TTS 生成: {e}，改用占位音频")
    # 占位：最小 opus 静音帧 (2.5ms)，发多帧让 ASR 有一段时间
    # 单帧 1 字节 TOC 0xF8 (code 0)
    placeholder = bytes([0xF8] * 120)
    return placeholder, "placeholder"


def main():
    p = argparse.ArgumentParser(description="模拟完整小智对话（hello + listen + 音频 + 收回复）")
    p.add_argument("--url", default="ws://192.168.1.100:8000/xiaozhi/v1/")
    p.add_argument("--device-id", default="02:42:c0:a8:90:02")
    p.add_argument("--client-id", default="verify-full-chat")
    p.add_argument("--wav-file", default="", help="本地 WAV 文件，脚本用 ffmpeg 转为 opus 后发送")
    p.add_argument("--opus-file", default="", help="可选 opus 文件路径（16k 单声道）")
    p.add_argument("--text", default="", help="用 TTS 生成该文本的 opus（需 edge-tts 和 ffmpeg）")
    p.add_argument("--timeout", type=float, default=15.0)
    args = p.parse_args()

    host, port, path = parse_ws_url(args.url)
    headers = {
        "Authorization": "Bearer",
        "Protocol-Version": "1",
        "Device-Id": args.device_id,
        "Client-Id": args.client_id,
    }

    print("[1/5] 连接 WebSocket ...")
    sock, err = websocket_connect(host, port, path, headers, args.timeout)
    if err:
        print(f"[失败] 握手: {err}")
        return 1

    print("[2/5] 发送 hello ...")
    send_ws_text(sock, json.dumps(HELLO_MSG))

    session_id = None
    recv_timeout = 5.0
    while True:
        op, payload = recv_ws_frame(sock, recv_timeout)
        if op is None:
            print("[失败] 未收到服务器 hello")
            sock.close()
            return 1
        if op == 0x01 and payload:
            try:
                data = json.loads(payload.decode("utf-8"))
                if data.get("type") == "hello":
                    session_id = data.get("session_id", "")
                    print(f"[OK] 服务器 hello, session_id={session_id[:20]}...")
                    break
            except Exception:
                pass
        if op == 0x08:
            print("[失败] 服务器关闭连接")
            sock.close()
            return 1

    print("[3/5] 发送 listen start ...")
    listen_start = {
        "session_id": session_id or "",
        "type": "listen",
        "state": "start",
        "mode": "auto",
    }
    send_ws_text(sock, json.dumps(listen_start))

    opus_bytes, source = get_opus_audio(args)
    print(f"[4/5] 发送音频 ({source}), {len(opus_bytes)} 字节 ...")
    # 按约 60ms 一帧切分发送二进制 opus（小智 server 收 binary 进 ASR）
    chunk = 200
    for i in range(0, len(opus_bytes), chunk):
        frame = opus_bytes[i : i + chunk]
        mask = os.urandom(4)
        payload = bytes(b ^ mask[j % 4] for j, b in enumerate(frame))
        length = len(frame)
        if length < 126:
            hdr = struct.pack(">BB", 0x82, 0x80 | length)
        else:
            hdr = struct.pack(">BBH", 0x82, 0x80 | 126, length)
        sock.send(hdr + mask + payload)
        time.sleep(0.06)
    # 停止监听
    listen_stop = {"session_id": session_id or "", "type": "listen", "state": "stop"}
    send_ws_text(sock, json.dumps(listen_stop))

    print("[5/5] 等待服务器回复（JSON / 二进制）...")
    deadline = time.time() + args.timeout
    count = 0
    received = []
    while time.time() < deadline:
        remaining = max(1.0, deadline - time.time())
        try:
            op, payload = recv_ws_frame(sock, remaining)
        except (socket.timeout, TimeoutError):
            break
        if op is None:
            break
        count += 1
        if op == 0x01 and payload:
            try:
                text = payload.decode("utf-8")
                data = json.loads(text)
                msg_type = data.get("type", "")
                if msg_type == "stt":
                    line = f"[STT] {data.get('text', '')}"
                elif msg_type == "tts":
                    line = f"[TTS] state={data.get('state')} text={data.get('text', '')[:80]}"
                elif msg_type == "llm":
                    line = f"[LLM] {data.get('text', '')[:80]}"
                else:
                    line = f"[JSON] {text[:500]}"
                received.append(line)
                print(f"  {line}", flush=True)
            except Exception as e:
                line = f"[text] {payload[:200]} (decode err: {e})"
                received.append(line)
                print(f"  {line}", flush=True)
        elif op == 0x02 and payload:
            line = f"[二进制] len={len(payload)} (TTS 音频)"
            received.append(line)
            print(f"  {line}", flush=True)
        elif op == 0x08:
            received.append("[服务器关闭]")
            print("  [服务器关闭]", flush=True)
            break
        elif op == 0x09:
            send_ws_pong(sock, payload or b"")
            received.append("[Ping→已回 Pong]")
            print("  [Ping→已回 Pong]", flush=True)
        else:
            line = f"[其他] opcode={op} len={len(payload) if payload else 0}"
            received.append(line)
            print(f"  {line}", flush=True)

    print(f"\n共收到 {count} 条消息")
    if received:
        print("--- 服务器回复摘要 ---")
        for r in received:
            print(" ", r)
    sock.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
