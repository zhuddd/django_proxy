"""WebSocket 代理辅助函数测试。"""

from django.test import SimpleTestCase

from transparent_proxy_gateway.proxy.ws_core import (
    http_url_to_ws_url,
    prepare_ws_outgoing_headers,
)


class HttpToWsUrlTests(SimpleTestCase):
    def test_http_to_ws(self):
        self.assertEqual(
            http_url_to_ws_url("http://127.0.0.1:9000/robot/ws"),
            "ws://127.0.0.1:9000/robot/ws",
        )

    def test_https_to_wss(self):
        self.assertEqual(
            http_url_to_ws_url("https://example.com/api?q=1"),
            "wss://example.com/api?q=1",
        )


class PrepareWsHeadersTests(SimpleTestCase):
    def test_strips_handshake_headers(self):
        route = type("R", (), {"target_url": "http://upstream:8000", "prefix": "/robot"})()
        scope = {
            "scheme": "ws",
            "headers": [
                (b"host", b"gateway.local"),
                (b"sec-websocket-key", b"abc"),
                (b"cookie", b"s=1"),
                (b"user-agent", b"test"),
            ],
            "client": ("10.0.0.1", 12345),
            "subprotocols": [],
        }
        headers = dict(
            prepare_ws_outgoing_headers(scope, "http://upstream:8000/robot/ws", route)
        )
        self.assertNotIn("sec-websocket-key", {k.lower() for k in headers})
        self.assertEqual(headers.get("Cookie"), "s=1")
        self.assertEqual(headers.get("Host"), "upstream:8000")
