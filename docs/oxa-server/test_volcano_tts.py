#!/usr/bin/env python3
"""
火山双向流 TTS 调用测试脚本
使用环境变量 VOLC_APP_ID、VOLC_ACCESS_KEY，以及 speaker、resource_id(seed-icl-2.0) 等调用合成。
"""
import asyncio
import json
import os
import sys
import uuid
import websockets

# 与 huoshan_double_stream.py 一致的协议常量
PROTOCOL_VERSION = 0b0001
DEFAULT_HEADER_SIZE = 0b0001
FULL_CLIENT_REQUEST = 0b0001
AUDIO_ONLY_RESPONSE = 0b1011
FULL_SERVER_RESPONSE = 0b1001
MsgTypeFlagWithEvent = 0b100
JSON = 0b0001
COMPRESSION_NO = 0b0000
EVENT_Start_Connection = 1
EVENT_FinishConnection = 2
EVENT_ConnectionStarted = 50
EVENT_ConnectionFailed = 51
EVENT_StartSession = 100
EVENT_FinishSession = 102
EVENT_SessionStarted = 150
EVENT_SessionFailed = 153
EVENT_SessionFinished = 152
EVENT_TaskRequest = 200
EVENT_TTSResponse = 352


def make_header(message_type, with_event=True, serial_json=True):
    flags = MsgTypeFlagWithEvent if with_event else 0
    serial = JSON if serial_json else 0
    return bytes([
        (PROTOCOL_VERSION << 4) | DEFAULT_HEADER_SIZE,
        (message_type << 4) | flags,
        (serial << 4) | COMPRESSION_NO,
        0,
    ])


def make_optional(event, session_id=None):
    buf = bytearray()
    buf.extend(event.to_bytes(4, "big", signed=True))
    if session_id:
        sid = session_id.encode("utf-8")
        buf.extend(len(sid).to_bytes(4, "big", signed=True))
        buf.extend(sid)
    return bytes(buf)


def make_req_params(text="", speaker="", event=0, audio_format="pcm", sample_rate=16000):
    req = {
        "text": text,
        "speaker": speaker,
        "audio_params": {"format": audio_format, "sample_rate": sample_rate, "speech_rate": 0, "loudness_rate": 0},
        "additions": "{}",
    }
    payload = {
        "user": {"uid": "1234"},
        "event": event,
        "namespace": "BidirectionalTTS",
        "req_params": req,
    }
    return json.dumps(payload).encode("utf-8")


async def send_event(ws, event, session_id=None, text="", speaker=""):
    header = make_header(FULL_CLIENT_REQUEST)
    optional = make_optional(event, session_id)
    if event == EVENT_Start_Connection:
        payload = b"{}"
    elif event == EVENT_StartSession:
        payload = make_req_params(speaker=speaker, event=EVENT_StartSession)
    elif event == EVENT_TaskRequest:
        payload = make_req_params(text=text, speaker=speaker, event=EVENT_TaskRequest)
    elif event == EVENT_FinishSession:
        payload = b"{}"
    else:
        payload = b"{}"
    msg = header + optional + len(payload).to_bytes(4, "big", signed=True) + payload
    await ws.send(msg)


MsgTypeFlagWithEvent = 0b100

def parse_response(data):
    """与服务端协议一致：EVENT_TTSResponse 等先有 sessionId(4+len) 再 payload(4+len)。"""
    if len(data) < 8:
        return None, None, None
    msg_type = (data[1] >> 4) & 0x0F
    flags = data[1] & 0x0F
    event = int.from_bytes(data[4:8], "big", signed=True)
    offset = 8
    payload = None
    if flags != MsgTypeFlagWithEvent:
        return msg_type, event, None
    # ConnectionStarted / ConnectionFailed 等只有 content，无 payload
    if event in (EVENT_ConnectionStarted, EVENT_ConnectionFailed):
        if len(data) > offset + 4:
            clen = int.from_bytes(data[offset : offset + 4], "big", signed=True)
            offset += 4 + max(0, clen)
        return msg_type, event, None
    # SessionStarted / SessionFailed / SessionFinished: sessionId + response_meta_json
    if event in (EVENT_SessionStarted, EVENT_SessionFailed, EVENT_SessionFinished):
        return msg_type, event, None
    # TTSResponse 等：先 sessionId，再 payload（音频数据）
    if event == EVENT_TTSResponse and len(data) > offset + 4:
        clen = int.from_bytes(data[offset : offset + 4], "big", signed=True)
        offset += 4 + max(0, clen)
        if len(data) > offset + 4:
            plen = int.from_bytes(data[offset : offset + 4], "big", signed=True)
            offset += 4
            if plen > 0 and len(data) >= offset + plen:
                payload = data[offset : offset + plen]
    return msg_type, event, payload


async def test_volcano_tts():
    ws_url = "wss://openspeech.bytedance.com/api/v3/tts/bidirection"
    appid = os.environ.get("VOLC_APP_ID", "").strip()
    token = os.environ.get("VOLC_ACCESS_KEY", "").strip()
    if not appid or not token:
        print(
            "请设置环境变量 VOLC_APP_ID（火山控制台应用 ID）与 VOLC_ACCESS_KEY（访问令牌）后再运行。",
            file=sys.stderr,
        )
        raise SystemExit(1)
    resource_id = "seed-icl-2.0"
    speaker = "S_7JS6dHIV1"
    text = "你好，这是火山语音合成测试。"

    headers = {
        "X-Api-App-Key": appid,
        "X-Api-Access-Key": token,
        "X-Api-Resource-Id": resource_id,
        "X-Api-Connect-Id": str(uuid.uuid4()),
    }
    print("连接中...", ws_url)
    async with websockets.connect(ws_url, additional_headers=headers, max_size=10_000_000) as ws:
        # 1. StartConnection
        await send_event(ws, EVENT_Start_Connection)
        r = await ws.recv()
        _, ev, _ = parse_response(r)
        if ev == EVENT_ConnectionFailed:
            print("FAIL: 建连失败(鉴权/资源ID等)")
            return
        if ev != EVENT_ConnectionStarted:
            print("WARN: 建连响应 event =", ev)

        session_id = uuid.uuid4().hex
        # 2. StartSession
        await send_event(ws, EVENT_StartSession, session_id=session_id, speaker=speaker)
        r = await ws.recv()
        _, ev, meta = parse_response(r)
        if ev == EVENT_SessionFailed:
            print("FAIL: 会话启动失败", meta.decode("utf-8", errors="ignore") if meta else "")
            return
        if ev != EVENT_SessionStarted:
            print("WARN: StartSession 响应 event =", ev)

        # 3. TaskRequest
        await send_event(ws, EVENT_TaskRequest, session_id=session_id, text=text, speaker=speaker)
        # 4. FinishSession
        await send_event(ws, EVENT_FinishSession, session_id=session_id)

        audio_chunks = []
        while True:
            try:
                r = await asyncio.wait_for(ws.recv(), timeout=10.0)
            except asyncio.TimeoutError:
                break
            msg_type, ev, payload = parse_response(r)
            if ev == EVENT_TTSResponse and payload:
                audio_chunks.append(payload)
            if ev == EVENT_SessionFinished:
                break
        print("OK: 火山语音合成成功，收到", len(audio_chunks), "帧音频。")
        return b"".join(audio_chunks)


def save_wav(pcm_data: bytes, path: str, sample_rate: int = 16000, channels: int = 1, sample_width: int = 2):
    """PCM 转 WAV 并写入文件"""
    import struct
    n = len(pcm_data) // sample_width
    wav_header = struct.pack(
        "<4sI4s4sIHHIIHH4sI",
        b"RIFF", 36 + n * sample_width, b"WAVE", b"fmt ", 16,
        1, channels, sample_rate, sample_rate * channels * sample_width,
        channels * sample_width, 16, b"data", n * sample_width,
    )
    with open(path, "wb") as f:
        f.write(wav_header)
        f.write(pcm_data)


if __name__ == "__main__":
    import sys
    out_dir = sys.argv[1] if len(sys.argv) > 1 else "/tmp"
    pcm_path = out_dir.rstrip("/") + "/volcano_tts_test.pcm"
    wav_path = out_dir.rstrip("/") + "/volcano_tts_test.wav"
    pcm_data = asyncio.run(test_volcano_tts())
    if pcm_data:
        with open(pcm_path, "wb") as f:
            f.write(pcm_data)
        save_wav(pcm_data, wav_path)
        print("已保存:", pcm_path, wav_path)
