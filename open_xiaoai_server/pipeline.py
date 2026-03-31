# 流水线：收语音 → VAD → ASR → 唤醒判定 → [唤醒后] 收新语音 → ASR → 意图 → 分发

import asyncio
import logging
from typing import Callable, Optional

from .protocol import Request, Response, Stream

logger = logging.getLogger(__name__)


class Pipeline:
    """串联 VAD → ASR → 唤醒 → 意图 的可插拔流水线。"""

    def __init__(
        self,
        vad,
        asr,
        wake_detector,
        intent_router,
        *,
        on_play_audio: Optional[Callable] = None,
        on_start_listening: Optional[Callable] = None,
        on_stop_listening: Optional[Callable] = None,
        wake_reply_audio: Optional[bytes] = None,
    ):
        self.vad = vad
        self.asr = asr
        self.wake_detector = wake_detector
        self.intent_router = intent_router
        self.on_play_audio = on_play_audio
        self.on_start_listening = on_start_listening
        self.on_stop_listening = on_stop_listening
        self.wake_reply_audio = wake_reply_audio or b""
        self._wake = False
        self._audio_buffer: bytearray = bytearray()

    def feed_audio(self, chunk: bytes) -> None:
        self._audio_buffer.extend(chunk)

    async def on_audio_segment(self, pcm_or_opus: bytes, sample_rate: int = 16000) -> None:
        """收到一整段语音（VAD 切好的）。"""
        if not pcm_or_opus:
            return
        text = await self.asr.transcribe(pcm_or_opus, sample_rate)
        if not text:
            return
        if not self._wake:
            if self.wake_detector.is_wake(text):
                self._wake = True
                logger.info("wake detected, text=%s", text)
                if self.wake_reply_audio and self.on_play_audio:
                    await self.on_play_audio(self.wake_reply_audio)
                if self.on_start_listening:
                    await self.on_start_listening()
            return
        # 已唤醒：做意图识别并分发
        intent, slots = await self.intent_router.parse(text)
        logger.info("intent=%s slots=%s", intent, slots)
        result = await self.intent_router.dispatch(intent, slots)
        if result and result.get("tts") and self.on_play_audio:
            await self.on_play_audio(result["tts"])
        if self.on_stop_listening:
            await self.on_stop_listening()

    def reset_wake(self) -> None:
        self._wake = False
        self._audio_buffer.clear()


# 占位实现，便于先跑通流程

class DummyVAD:
    def feed(self, chunk: bytes) -> list[bytes]:
        return []  # 不切段，由调用方按时间或长度切


class DummyASR:
    async def transcribe(self, audio: bytes, sample_rate: int = 16000) -> str:
        return ""


class DummyWake:
    def __init__(self, keywords: list[str]):
        self.keywords = [k.strip() for k in keywords]

    def is_wake(self, text: str) -> bool:
        t = (text or "").strip()
        return any(k in t for k in self.keywords)


class DummyIntent:
    async def parse(self, text: str) -> tuple[str, dict]:
        return "unknown", {}

    async def dispatch(self, intent: str, slots: dict):
        return None
