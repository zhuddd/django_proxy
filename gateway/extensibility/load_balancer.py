from __future__ import annotations

from dataclasses import dataclass


@dataclass
class UpstreamTarget:
    url: str
    weight: int = 1
    healthy: bool = True


class LoadBalancer:
    """Round-robin / weighted selection — plug in before httpx forward."""

    def __init__(self, targets: list[UpstreamTarget]):
        self.targets = targets
        self._index = 0

    def pick(self) -> str | None:
        healthy = [t for t in self.targets if t.healthy]
        if not healthy:
            return None
        target = healthy[self._index % len(healthy)]
        self._index += 1
        return target.url
