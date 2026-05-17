"""WebSocket 透明代理：URL 转换、请求头构造与上游 SSL。"""

from __future__ import annotations

import ssl
from urllib.parse import urlparse

from transparent_proxy_gateway.proxy.headers import is_hop_by_hop
from transparent_proxy_gateway.proxy.router import upstream_host_header
from transparent_proxy_gateway.proxy.ssl_config import get_proxy_ssl_verify

# WebSocket 握手头由客户端库生成，不应原样转发
_WS_HANDSHAKE_HEADERS = frozenset(
    {
        "sec-websocket-key",
        "sec-websocket-version",
        "sec-websocket-extensions",
        "sec-websocket-protocol",
        "sec-websocket-accept",
        "upgrade",
        "connection",
        "host",
        "content-length",
    }
)


def http_url_to_ws_url(http_url: str) -> str:
    """将上游 HTTP(S) URL 转为 WS(S) URL（路径与 query 保持不变）。"""
    parsed = urlparse(http_url)
    if parsed.scheme in ("ws", "wss"):
        return http_url
    scheme = "wss" if parsed.scheme == "https" else "ws"
    netloc = parsed.netloc
    path = parsed.path or "/"
    query = f"?{parsed.query}" if parsed.query else ""
    fragment = f"#{parsed.fragment}" if parsed.fragment else ""
    return f"{scheme}://{netloc}{path}{query}{fragment}"


def _header_map(scope: dict) -> dict[str, str]:
    return {
        name.decode().lower(): value.decode()
        for name, value in scope.get("headers", [])
    }


def _client_ip_from_scope(scope: dict) -> str | None:
    headers = _header_map(scope)
    if forwarded := headers.get("x-forwarded-for"):
        return forwarded.split(",")[0].strip()
    client = scope.get("client")
    if client:
        return client[0]
    return None


def _gateway_http_origin(scope: dict) -> str:
    headers = _header_map(scope)
    host = headers.get("host", "")
    if scope.get("scheme") in ("wss", "https"):
        return f"https://{host}"
    return f"http://{host}"


def _rewrite_referer_origin_ws(outgoing: dict[str, str], scope: dict, route) -> None:
    """将 Referer/Origin 从网关地址改写为上游 HTTP 源（与 HTTP 代理一致）。"""
    gateway = _gateway_http_origin(scope)
    upstream = urlparse(route.target_url)
    upstream_origin = f"{upstream.scheme}://{upstream.netloc}"
    for key in ("Referer", "referer", "Origin", "origin"):
        val = outgoing.get(key)
        if val and val.startswith(gateway):
            outgoing[key] = upstream_origin + val[len(gateway) :]


def prepare_ws_outgoing_headers(scope: dict, target_http_url: str, route) -> list[tuple[str, str]]:
    """构造发往上游 WebSocket 的附加头（不含握手密钥）。"""
    outgoing: dict[str, str] = {}
    for name, value in scope.get("headers", []):
        key = name.decode().lower()
        if key in _WS_HANDSHAKE_HEADERS or is_hop_by_hop(key):
            continue
        outgoing[name.decode()] = value.decode()

    host = upstream_host_header(target_http_url)
    if host:
        outgoing["Host"] = host

    client_ip = _client_ip_from_scope(scope)
    if client_ip:
        prior = outgoing.get("X-Forwarded-For", "")
        outgoing["X-Forwarded-For"] = f"{prior}, {client_ip}".strip(", ")

    headers = _header_map(scope)
    if host_hdr := headers.get("host"):
        outgoing["X-Forwarded-Host"] = host_hdr

    outgoing["X-Forwarded-Proto"] = (
        "https" if scope.get("scheme") in ("wss", "https") else "http"
    )
    if client_ip:
        outgoing["X-Real-IP"] = client_ip

    _rewrite_referer_origin_ws(outgoing, scope, route)
    return list(outgoing.items())


def ssl_context_for_ws_url(ws_url: str) -> ssl.SSLContext | None:
    """为 ``wss://`` 返回 SSL 上下文；``ws://`` 返回 None。"""
    if urlparse(ws_url).scheme != "wss":
        return None

    verify = get_proxy_ssl_verify()
    if verify is False:
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        return ctx
    if isinstance(verify, str):
        return ssl.create_default_context(cafile=verify)
    return ssl.create_default_context()


def subprotocols_from_scope(scope: dict) -> list[str] | None:
    """从 ASGI scope 解析客户端请求的 Sec-WebSocket-Protocol 列表。"""
    protos: list[str] = []
    for item in scope.get("subprotocols", []):
        protos.append(item.decode() if isinstance(item, bytes) else item)
    return protos or None
