# ASR 抽象：语音段 → 文字
# 可接 FunASR、火山、豆包、讯飞等

from abc import ABC, abstractmethod


class BaseASR(ABC):
    @abstractmethod
    async def transcribe(self, audio: bytes, sample_rate: int = 16000) -> str:
        """将一段音频转成文字。"""
        pass


class DummyASR(BaseASR):
    """占位，返回空字符串。"""

    async def transcribe(self, audio: bytes, sample_rate: int = 16000) -> str:
        return ""
