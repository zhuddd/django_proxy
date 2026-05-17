"""Channels WebSocket：管理台实时日志与透明上游转发。"""

from __future__ import annotations

import asyncio
import json
import time

from channels.generic.websocket import AsyncWebsocketConsumer
from django.conf import settings
from loguru import logger
from websockets.asyncio.client import connect as ws_connect
from websockets.exceptions import ConnectionClosed

from transparent_proxy_gateway.proxy.route_cache import get_routes
from transparent_proxy_gateway.proxy.router import build_target_url, match_route
from transparent_proxy_gateway.proxy.ws_core import (
    http_url_to_ws_url,
    prepare_ws_outgoing_headers,
    ssl_context_for_ws_url,
    subprotocols_from_scope,
)
from transparent_proxy_gateway.services.log_broadcaster import broadcast_log, persist_proxy_log


class ProxyLogConsumer(AsyncWebsocketConsumer):
    """订阅 ``proxy_logs`` 频道，接收并转发日志 JSON。"""

    async def connect(self):
        await self.channel_layer.group_add("proxy_logs", self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("proxy_logs", self.channel_name)

    async def proxy_log(self, event):
        """处理 group_send 的 proxy.log 事件。"""
        await self.send(text_data=json.dumps(event["data"]))


class WebSocketProxyConsumer(AsyncWebsocketConsumer):
    """
    透明 WebSocket 反向代理（与 HTTP 共用 ``ProxyRoute`` 前缀表）。

    流程：路由匹配 → 连接上游 ``ws(s)://`` → ``accept`` 客户端 → 双向帧中继。
    关闭连接时写入 ``ProxyLog``（method=WEBSOCKET）并广播至 ``/ws/logs/``。
    受 ``settings.PROXY_WEBSOCKET_ENABLED`` 控制。
    """

    upstream = None
    _relay_task: asyncio.Task | None = None
    _route = None
    _target_ws_url = ""
    _path = ""
    _start = 0.0
    _logged = False
    _accepted = False

    async def connect(self):
        if not getattr(settings, "PROXY_WEBSOCKET_ENABLED", True):
            await self.close(code=1008)
            return

        self._path = self.scope.get("path") or "/"
        self._start = time.perf_counter()

        routes = await get_routes()
        matched = match_route(self._path, routes)
        if not matched:
            await self.close(code=4404)
            return

        self._route = matched.route
        qs = (self.scope.get("query_string") or b"").decode()
        http_target = build_target_url(self._route, self._path, qs)
        ws_target = http_url_to_ws_url(http_target)
        self._target_ws_url = ws_target
        headers = prepare_ws_outgoing_headers(self.scope, http_target, self._route)
        ssl_ctx = ssl_context_for_ws_url(ws_target)
        subprotocols = subprotocols_from_scope(self.scope)

        try:
            self.upstream = await ws_connect(
                ws_target,
                additional_headers=headers,
                ssl=ssl_ctx,
                subprotocols=subprotocols,
                open_timeout=float(getattr(settings, "PROXY_CONNECT_TIMEOUT", 10)),
            )
        except Exception as exc:
            logger.error("WebSocket upstream connect failed {}: {}", ws_target, exc)
            await self._log_close(502, str(exc))
            await self.close(code=1011)
            return

        await self.accept(subprotocol=self.upstream.subprotocol)
        self._accepted = True
        self._relay_task = asyncio.create_task(self._relay_upstream_to_client())

    async def _relay_upstream_to_client(self) -> None:
        try:
            async for message in self.upstream:
                if isinstance(message, str):
                    await self.send(text_data=message)
                else:
                    await self.send(bytes_data=message)
        except ConnectionClosed:
            pass
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            logger.debug("WebSocket upstream read ended {}: {}", self._target_ws_url, exc)
        finally:
            await self.close()

    async def receive(self, text_data=None, bytes_data=None):
        if not self.upstream:
            return
        try:
            if text_data is not None:
                await self.upstream.send(text_data)
            elif bytes_data is not None:
                await self.upstream.send(bytes_data)
        except ConnectionClosed:
            await self.close()
        except Exception as exc:
            logger.debug("WebSocket upstream send failed: {}", exc)
            await self.close()

    async def disconnect(self, close_code):
        if self._relay_task and not self._relay_task.done():
            self._relay_task.cancel()
            try:
                await self._relay_task
            except asyncio.CancelledError:
                pass

        if self.upstream:
            try:
                await self.upstream.close()
            except Exception:
                pass

        if self._accepted:
            await self._log_close(close_code or 101, "")

    async def _log_close(self, status_code: int, error_message: str) -> None:
        if self._logged:
            return
        self._logged = True
        latency_ms = (time.perf_counter() - self._start) * 1000
        client_ip = None
        client = self.scope.get("client")
        if client:
            client_ip = client[0]

        payload = {
            "method": "WEBSOCKET",
            "path": self._path,
            "target_url": self._target_ws_url,
            "status_code": status_code if status_code else None,
            "latency_ms": round(latency_ms, 2),
            "client_ip": client_ip,
            "error_message": error_message,
        }
        await persist_proxy_log(
            method="WEBSOCKET",
            path=self._path,
            target_url=self._target_ws_url,
            status_code=status_code if status_code else None,
            request_headers={},
            response_headers={},
            latency_ms=latency_ms,
            client_ip=client_ip,
            route_id=self._route.id if self._route else None,
            error_message=error_message,
        )
        await broadcast_log(payload)
