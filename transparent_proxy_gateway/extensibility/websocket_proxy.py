"""
WebSocket 双向透明代理。

实现类：``transparent_proxy_gateway.consumers.WebSocketProxyConsumer``；
在 ASGI ``ProtocolTypeRouter`` 中通过 ``integration.get_websocket_urlpatterns()`` 注册。
"""

from transparent_proxy_gateway.consumers import WebSocketProxyConsumer

__all__ = ["WebSocketProxyConsumer"]
