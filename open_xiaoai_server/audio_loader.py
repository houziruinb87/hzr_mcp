# 音频文件加载：读取为 bytes，供下发播放（客户端协议若要求 PCM 需在调用方转换）

import logging
from pathlib import Path
from typing import Optional

from .config import get_wake_reply_audio_path

logger = logging.getLogger(__name__)


def load_audio_bytes(path: Optional[Path] = None) -> bytes:
    """加载音频文件为字节。未传 path 时使用配置的唤醒回复音频。"""
    if path is None:
        path = get_wake_reply_audio_path()
    if not path or not path.exists():
        return b""
    try:
        return path.read_bytes()
    except Exception as e:
        logger.warning("load_audio_bytes %s: %s", path, e)
        return b""


def get_wake_reply_audio_bytes() -> bytes:
    """获取唤醒回复音频内容（缓存可选，当前每次读取）。"""
    return load_audio_bytes()
