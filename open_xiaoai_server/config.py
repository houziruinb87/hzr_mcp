# 配置加载：优先 config.yaml，否则使用 config.example.yaml 或默认值

from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False

_BASE = Path(__file__).resolve().parent


def _load_yaml(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    if not HAS_YAML:
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def get_config() -> Dict[str, Any]:
    for name in ("config.yaml", "config.example.yaml"):
        p = _BASE / name
        if p.exists():
            data = _load_yaml(p)
            if data:
                return data
    return {}


def get_server_host_port() -> tuple:
    c = get_config().get("server", {})
    return (
        c.get("host", "0.0.0.0"),
        int(c.get("port", 4399)),
    )


def get_wake_keywords() -> List[str]:
    kw = get_config().get("wake", {}).get("keywords", [])
    if kw:
        return list(kw)
    return ["小智", "小智同学", "爸爸最帅"]


def get_audio_dir() -> Path:
    """音频资源目录。"""
    return _BASE / "audio"


def get_wake_reply_audio_path() -> Optional[Path]:
    """唤醒回复音频文件路径；不存在则返回 None。"""
    audio_dir = get_audio_dir()
    # 优先使用配置
    path_str = get_config().get("wake", {}).get("reply_audio")
    if path_str:
        p = Path(path_str)
        if not p.is_absolute():
            p = audio_dir / path_str
        return p if p.exists() else None
    # 默认文件名
    default = audio_dir / "爸爸最帅收到收到.mp3"
    return default if default.exists() else None
