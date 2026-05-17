from datetime import datetime
from typing import Any

from ninja import Schema


class ProxyLogOut(Schema):
    id: int
    method: str
    path: str
    target_url: str
    status_code: int | None
    request_headers: dict[str, Any]
    response_headers: dict[str, Any]
    latency_ms: float
    client_ip: str | None
    route_id: int | None
    error_message: str
    created_at: datetime
