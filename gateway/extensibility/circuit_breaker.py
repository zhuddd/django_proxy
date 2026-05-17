from __future__ import annotations

import time
from enum import Enum


class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, recovery_timeout: float = 30.0):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failures = 0
        self.state = CircuitState.CLOSED
        self.opened_at: float | None = None

    def allow_request(self) -> bool:
        if self.state == CircuitState.CLOSED:
            return True
        if self.state == CircuitState.OPEN:
            if self.opened_at and time.monotonic() - self.opened_at >= self.recovery_timeout:
                self.state = CircuitState.HALF_OPEN
                return True
            return False
        return True

    def record_success(self):
        self.failures = 0
        self.state = CircuitState.CLOSED
        self.opened_at = None

    def record_failure(self):
        self.failures += 1
        if self.failures >= self.failure_threshold:
            self.state = CircuitState.OPEN
            self.opened_at = time.monotonic()
