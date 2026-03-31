# 入口：启动 WebSocket 服务，挂载流水线（VAD → ASR → 唤醒 → 意图）

import asyncio
import logging
from typing import Optional

from .asr import BaseASR, DummyASR
from .audio_loader import get_wake_reply_audio_bytes
from .config import get_wake_keywords, get_server_host_port
from .intent import IntentRouter
from .pipeline import Pipeline
from .transport import serve
from .vad import BaseVAD, DummyVAD
from .wake import KeywordWake

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 客户端通常发 opus 16kHz 60ms/帧
DEFAULT_SAMPLE_RATE = 16000


def make_pipeline(
    vad: Optional[BaseVAD] = None,
    asr: Optional[BaseASR] = None,
    keywords: Optional[list] = None,
    intent_router: Optional[IntentRouter] = None,
    wake_reply_audio: Optional[bytes] = None,
):
    vad = vad or DummyVAD()
    asr = asr or DummyASR()
    wake = KeywordWake(keywords or get_wake_keywords())
    intent = intent_router or IntentRouter()
    intent.add_rule(r"播放|放一首|来首", "play_music", {})
    intent.add_rule(r"开灯|关灯|打开|关闭", "iot_control", {})
    return Pipeline(
        vad=vad,
        asr=asr,
        wake_detector=wake,
        intent_router=intent,
        wake_reply_audio=wake_reply_audio or get_wake_reply_audio_bytes(),
    )


def on_connect(transport):
    pipeline = make_pipeline()
    pipeline.on_play_audio = transport.send_play_stream  # async (audio_bytes) -> None
    transport.on_stream = _make_on_stream(pipeline, transport)
    transport.on_event = _make_on_event(pipeline)


def _make_on_stream(pipeline: Pipeline, transport):
    async def on_stream(stream):
        if stream.tag != "record":
            return
        segments = pipeline.vad.feed(stream.bytes, DEFAULT_SAMPLE_RATE)
        for is_speech, seg in segments:
            if is_speech and seg:
                await pipeline.on_audio_segment(seg, DEFAULT_SAMPLE_RATE)
    return on_stream


def _make_on_event(pipeline: Pipeline):
    async def on_event(ev):
        if ev.event == "instruction" and ev.data:
            text = (ev.data.get("text") or ev.data.get("content") or "").strip()
            if text:
                await pipeline.on_audio_segment(b"", DEFAULT_SAMPLE_RATE)
    return on_event


if __name__ == "__main__":
    host, port = get_server_host_port()
    asyncio.run(serve(host=host, port=port, on_connect=on_connect))
