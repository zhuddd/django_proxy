"""请求/响应头处理：过滤逐跳头、构造发往上游的请求头。"""

# RFC 2616 逐跳头，不应在代理链中透传
HOP_BY_HOP_HEADERS = frozenset(
    {
        "connection",
        "keep-alive",
        "proxy-authenticate",
        "proxy-authorization",
        "te",
        "trailers",
        "transfer-encoding",
        "upgrade",
    }
)

BODYLESS_METHODS = frozenset({"GET", "HEAD", "OPTIONS", "TRACE", "CONNECT"})


def is_hop_by_hop(name: str) -> bool:
    """判断头名是否为逐跳头。"""
    return name.lower() in HOP_BY_HOP_HEADERS


def filter_hop_by_hop(headers) -> dict[str, str]:
    """移除逐跳头，返回可持久化/下发的头字典。"""
    return {k: v for k, v in headers.items() if not is_hop_by_hop(k)}


def prepare_outgoing_headers(request, target_url: str, route=None) -> dict[str, str]:
    """转发客户端头，并设置 Host、X-Forwarded-* 等上游所需头。"""
    from transparent_proxy_gateway.proxy.router import upstream_host_header
    from transparent_proxy_gateway.proxy.response_rewrite import rewrite_referer_origin

    outgoing = filter_hop_by_hop(dict(request.headers))
    for key in ("Host", "host", "Content-Length", "content-length"):
        outgoing.pop(key, None)

    host = upstream_host_header(target_url)
    if host:
        outgoing["Host"] = host

    client_ip = _client_ip_from_request(request)
    if client_ip:
        prior = outgoing.get("X-Forwarded-For", "")
        outgoing["X-Forwarded-For"] = f"{prior}, {client_ip}".strip(", ")

    outgoing["X-Forwarded-Host"] = request.get_host()
    outgoing["X-Forwarded-Proto"] = request.scheme
    if client_ip:
        outgoing["X-Real-IP"] = client_ip

    if route is not None:
        rewrite_referer_origin(outgoing, request, route)

    return outgoing


def _client_ip_from_request(request) -> str | None:
    """从 X-Forwarded-For 或 REMOTE_ADDR 解析客户端 IP。"""
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")
