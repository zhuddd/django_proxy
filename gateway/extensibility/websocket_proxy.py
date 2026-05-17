"""
Future: ASGI WebSocket bidirectional proxy.
Hook point: ProtocolTypeRouter websocket path -> WebSocketProxyConsumer.
"""


class WebSocketProxyStub:
    """Placeholder for transparent WebSocket upgrade forwarding."""

    async def proxy_connect(self, client_ws, upstream_url: str):
        raise NotImplementedError("WebSocket proxy extension not enabled")
