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
    return name.lower() in HOP_BY_HOP_HEADERS


def filter_hop_by_hop(headers) -> dict[str, str]:
    return {k: v for k, v in headers.items() if not is_hop_by_hop(k)}


def prepare_outgoing_headers(request, target_url: str) -> dict[str, str]:
    """Forward client headers; set Host + X-Forwarded-* for upstream."""
    from gateway.proxy.router import upstream_host_header

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

    return outgoing


def _client_ip_from_request(request) -> str | None:
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")
