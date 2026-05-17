from __future__ import annotations

import time
from collections import defaultdict


class TokenBucketRateLimiter:
    """In-memory token bucket — replace with Redis for multi-worker deployments."""

    def __init__(self, rate: float = 100.0, capacity: float = 200.0):
        self.rate = rate
        self.capacity = capacity
        self._tokens: dict[str, float] = defaultdict(lambda: capacity)
        self._last: dict[str, float] = {}

    def allow(self, key: str) -> bool:
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
