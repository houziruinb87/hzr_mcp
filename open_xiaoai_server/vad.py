# VAD 抽象：输入音频流，输出「语音段」起止或分段音频
# 可接 Silero VAD、webrtcvad 等

from abc import ABC, abstractmethod
from typing import List, Tuple


class BaseVAD(ABC):
    @abstractmethod
    def feed(self, chunk: bytes, sample_rate: int = 16000) -> List[Tuple[bool, bytes]]:
        """喂入音频块，返回 [(is_speech, segment_bytes), ...]。"""
        pass

    def reset(self) -> None:
        """清空内部状态。"""
        pass


class DummyVAD(BaseVAD):
    """不切段，仅做占位。实际可由 pipeline 按固定时长或外部 VAD 驱动。"""

    def feed(self, chunk: bytes, sample_rate: int = 16000) -> List[Tuple[bool, bytes]]:
        if not chunk:
            return []
        return [(True, bytes(chunk))]
