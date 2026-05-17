"""令牌桶限流占位实现（可替换为 Redis 等分布式方案）。"""

from __future__ import annotations

import time
from collections import defaultdict


class TokenBucketRateLimiter:
    """按 key 维度的内存令牌桶限流器。"""

    def __init__(self, rate: float = 100.0, capacity: float = 200.0):
        """
        Args:
            rate: 每秒补充令牌数。
            capacity: 桶容量上限。
        """
        self.rate = rate
        self.capacity = capacity
        self._tokens: dict[str, float] = defaultdict(lambda: capacity)
        self._last: dict[str, float] = {}

    def allow(self, key: str) -> bool:
        """消耗一枚令牌；不足时返回 False。"""
        now = time.monotonic()
        last = self._last.get(key, now)
        elapsed = now - last
        self._last[key] = now
        tokens = min(self.capacity, self._tokens[key] + elapsed * self.rate)
        if tokens < 1:
            self._tokens[key] = tokens
            return False
        self._tokens[key] = tokens - 1
        return True