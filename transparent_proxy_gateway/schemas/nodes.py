"""节点健康状态 API 输出 Schema。"""

from datetime import datetime

from ninja import Schema


class NodeStatusOut(Schema):
    """上游节点健康状态（含关联路由信息）。"""

    id: int
    route_id: int
    route_prefix: str
    target_url: str
    is_online: bool
    response_time_ms: float | None
    last_check: datetime | None
    error_message: str
