from datetime import datetime

from ninja import Schema


class NodeStatusOut(Schema):
    id: int
    route_id: int
    route_prefix: str
    target_url: str
    is_online: bool
    response_time_ms: float | None
    last_check: datetime | None
    error_message: str
