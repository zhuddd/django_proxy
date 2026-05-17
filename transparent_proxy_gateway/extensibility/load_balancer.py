"""多上游轮询负载均衡占位（可接入健康状态与权重）。"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class UpstreamTarget:
    """单个上游节点及其权重与健康标记。"""

    url: str
    weight: int = 1
    healthy: bool = True


class LoadBalancer:
    """简单轮询：在健康上游间依次选取。"""

    def __init__(self, targets: list[UpstreamTarget]):
        self.targets = targets
        self._index = 0

    def pick(self) -> str | None:
        """返回下一个可用上游 URL；无健康节点时返回 None。"""
        healthy = [t for t in self.targets if t.healthy]
        if not healthy:
            return None
        target = healthy[self._index % len(healthy)]
        self._index += 1
        return target.url