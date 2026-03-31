# 唤醒判定：基于关键词匹配（可扩展为 KWS 模型）

from typing import List


class KeywordWake:
    """关键词唤醒：文本包含任一关键词即视为唤醒。"""

    def __init__(self, keywords: List[str], strip: bool = True):
        self.keywords = [k.strip() for k in keywords] if strip else list(keywords)

    def is_wake(self, text: str) -> bool:
        if not text:
            return False
        t = text.strip()
        return any(k in t or t in k for k in self.keywords)
