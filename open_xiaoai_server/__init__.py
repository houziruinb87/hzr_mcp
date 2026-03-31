# Open-XiaoAI 自定义后端 Server 库
# 流程：收语音 → VAD → ASR → 唤醒判定 → 唤醒后收新语音 → ASR → 意图 → 分发

from .protocol import Event, Request, Response, Stream, parse_app_message
from .transport import Transport, serve
from .pipeline import Pipeline
from .wake import KeywordWake
from .intent import IntentRouter
from .vad import BaseVAD, DummyVAD
from .asr import BaseASR, DummyASR

__all__ = [
    "Event",
    "Request",
    "Response",
    "Stream",
    "parse_app_message",
    "Transport",
    "serve",
    "Pipeline",
    "KeywordWake",
    "IntentRouter",
    "BaseVAD",
    "DummyVAD",
    "BaseASR",
    "DummyASR",
]
