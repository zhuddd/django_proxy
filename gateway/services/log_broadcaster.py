from __future__ import annotations

import json
from typing import Any

from asgiref.sync import sync_to_async
from channels.layers import get_channel_layer

from gateway.models import ProxyLog


@sync_to_async
def persist_proxy_log(
    *,
    method: str,
    path: str,
    target_url: str,
    status_code: int | None,
    request_headers: dict,
    response_headers: dict,
    latency_ms: float,
    client_ip: str | None,
    route_id: int | None,
    error_message: str = "",
) -> ProxyLog:
    return ProxyLog.objects.create(
        method=method,
        path=path,
        target_url=target_url,
        status_code=status_code,
        request_headers=request_headers,
        response_headers=response_headers,
        latency_ms=latency_ms,
        client_ip=client_ip,
        route_id=route_id,
        error_message=error_message,
    )


async def broadcast_log(payload: dict[str, Any]) -> None:
    layer = get_channel_layer()
    if layer is None:
        return
    await layer.group_send(
        "proxy_logs",
        {"type": "proxy.log", "data": payload},
    )
