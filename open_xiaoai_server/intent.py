# 意图识别 + 分发：规则/关键词 或 LLM，输出 action + slots，由 Handler 执行

import asyncio
import re
from typing import Any, Awaitable, Callable, Dict, List, Optional, Tuple, Union

Handler = Union[Callable[[str, dict], Any], Callable[[str, dict], Awaitable[Any]]]


class IntentRouter:
    """规则意图 + 注册 Handler 分发。"""

    def __init__(self):
        self.rules: List[Tuple[re.Pattern, str, Optional[dict]]] = []
        self.handlers: Dict[str, Handler] = {}

    def add_rule(self, pattern: str, intent: str, default_slots: Optional[dict] = None) -> None:
        self.rules.append((re.compile(pattern), intent, default_slots or {}))

    def register(self, intent: str, handler: Handler) -> None:
        self.handlers[intent] = handler

    async def parse(self, text: str) -> Tuple[str, dict]:
        text = (text or "").strip()
        for pat, intent, default_slots in self.rules:
            m = pat.search(text)
            if m:
                slots = {**default_slots, "raw": text, "match": m.group(0)}
                return intent, slots
        return "unknown", {"raw": text}

    async def dispatch(self, intent: str, slots: dict):
        fn = self.handlers.get(intent)
        if not fn:
            return None
        try:
            out = fn(intent, slots)
            if asyncio.iscoroutine(out):
                return await out
            return out
        except Exception:
            return None
