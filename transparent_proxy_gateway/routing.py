"""
Channels WebSocket URL 配置。

顺序重要：``ws/logs/`` 为管理台实时日志；其余路径走透明上游代理。
"""

from django.urls import re_path

from transparent_proxy_gateway.consumers import ProxyLogConsumer, WebSocketProxyConsumer

websocket_urlpatterns = [
    re_path(r"^ws/logs/$", ProxyLogConsumer.as_asgi()),
    re_path(r"^(?P<path>.*)$", WebSocketProxyConsumer.as_asgi()),
]
