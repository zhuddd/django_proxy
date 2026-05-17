"""
Rewrite upstream response headers for prefix proxying (cookies, redirects).

301/302/303/307/308 responses are passed through with status unchanged; only
Location (and cookies) are rewritten so the browser stays on the gateway URL.
httpx uses follow_redirects=False — the proxy never consumes redirect chains.
"""

from __future__ import annotations

from http.cookies import SimpleCookie
from urllib.parse import urljoin, urlparse

from gateway.proxy.router import normalize_path

# Passed to client unchanged; used for logging / validation.
REDIRECT_STATUS_CODES = frozenset({301, 302, 303, 307, 308})

_LOOPBACK_HOSTS = frozenset({"127.0.0.1", "localhost", "::1", "0.0.0.0", "[::1]"})


def _gateway_origin(request) -> str:
    return f"{request.scheme}://{request.get_host()}"


def _upstream_origin(route) -> str:
    parsed = urlparse(route.target_url)
    return f"{parsed.scheme}://{parsed.netloc}"


def _default_port(scheme: str) -> int:
    return 443 if scheme == "https" else 80


def _port_tuple(parsed) -> tuple[str, int]:
    host = (parsed.hostname or "").lower()
    port = parsed.port
    if port is None:
        port = _default_port(parsed.scheme or "http")
    return host, port


def _netlocs_equivalent(a, b) -> bool:
    """Same upstream authority, including loopback hostname variants."""
    ah, ap = _port_tuple(a)
    bh, bp = _port_tuple(b)
    if ap != bp:
        return False
    if ah == bh:
        return True
    if ah in _LOOPBACK_HOSTS and bh in _LOOPBACK_HOSTS:
        return True
    return False


def _location_points_to_gateway(parsed, request) -> bool:
    gw = urlparse(_gateway_origin(request))
    return _netlocs_equivalent(parsed, gw)


def rewrite_referer_origin(outgoing: dict[str, str], request, route) -> None:
    """Map Referer/Origin from gateway host to upstream host (CSRF / CORS)."""
    gateway = _gateway_origin(request)
    upstream = _upstream_origin(route)

    for key in ("Referer", "referer", "Origin", "origin"):
        val = outgoing.get(key)
        if val and val.startswith(gateway):
            outgoing[key] = upstream + val[len(gateway) :]


def rewrite_set_cookie(header_value: str, route_prefix: str) -> str:
    """
    Strip Domain; prefix Path so cookies work under gateway mount point.
    e.g. Path=/admin/ + prefix /test -> Path=/test/admin/
    """
    prefix = normalize_path(route_prefix)
    parts = [p.strip() for p in header_value.split(";")]
    if not parts:
        return header_value

    rebuilt = [parts[0]]
    path_written = False

    for part in parts[1:]:
        lower = part.lower()
        if lower.startswith("domain="):
            continue
        if lower.startswith("path="):
            old_path = part.split("=", 1)[1].strip()
            new_path = _merge_cookie_path(prefix, old_path)
            rebuilt.append(f"Path={new_path}")
            path_written = True
        elif lower == "path":
            new_path = _merge_cookie_path(prefix, "/")
            rebuilt.append(f"Path={new_path}")
            path_written = True
        else:
            rebuilt.append(part)

    if not path_written and prefix != "/":
        rebuilt.append(f"Path={prefix}/")

    return "; ".join(rebuilt)


def _merge_cookie_path(prefix: str, upstream_path: str) -> str:
    prefix = normalize_path(prefix)
    upstream_path = upstream_path or "/"
    if not upstream_path.startswith("/"):
        upstream_path = "/" + upstream_path
    if upstream_path == "/":
        return prefix if prefix.endswith("/") else prefix + "/"
    if upstream_path.startswith(prefix):
        return upstream_path
    return prefix.rstrip("/") + upstream_path


def _gateway_path_with_prefix(prefix: str, path: str) -> str:
    prefix = normalize_path(prefix)
    path = path or "/"
    if not path.startswith("/"):
        path = "/" + path
    if prefix == "/":
        return path
    if path.startswith(prefix):
        return path
    return prefix.rstrip("/") + path


def rewrite_location(
    location: str,
    request,
    route,
    *,
    target_url: str | None = None,
) -> str:
    """
    Rewrite upstream Location to a gateway URL (nginx proxy_redirect style).

    Supports absolute paths, relative paths, absolute URLs (incl. loopback
    aliases), and protocol-relative URLs.
    """
    location = (location or "").strip()
    if not location:
        return location

    prefix = route.effective_prefix
    gateway = _gateway_origin(request)
    up = urlparse(route.target_url)
    target = urlparse(target_url or route.target_url)

    # Protocol-relative: //host/path
    if location.startswith("//"):
        location = f"{request.scheme}:{location}"

    # Relative to current resource (e.g. "login", "../x")
    if not location.startswith("/") and "://" not in location:
        base_path = normalize_path(request.path_info)
        if not base_path.endswith("/"):
            base_path = base_path.rsplit("/", 1)[0] + "/"
        path = normalize_path(urljoin(base_path, location))
        return f"{gateway}{path}"

    if location.startswith("/"):
        path = _gateway_path_with_prefix(prefix, location)
        return f"{gateway}{path}"

    parsed = urlparse(location)
    if not parsed.scheme or not parsed.netloc:
        return location

    if _location_points_to_gateway(parsed, request):
        path = parsed.path or "/"
        qs = f"?{parsed.query}" if parsed.query else ""
        frag = f"#{parsed.fragment}" if parsed.fragment else ""
        return f"{gateway}{path}{qs}{frag}"

    path = parsed.path or "/"
    host_related = _netlocs_equivalent(parsed, up) or _netlocs_equivalent(parsed, target)
    path_related = prefix != "/" and path.startswith(prefix)

    if host_related or path_related:
        if not path.startswith(prefix) and prefix != "/":
            path = _gateway_path_with_prefix(prefix, path)
        qs = f"?{parsed.query}" if parsed.query else ""
        frag = f"#{parsed.fragment}" if parsed.fragment else ""
        return f"{gateway}{path}{qs}{frag}"

    return location


def is_redirect_status(status_code: int) -> bool:
    return status_code in REDIRECT_STATUS_CODES


def apply_response_rewrites(
    headers,
    request,
    route,
    *,
    target_url: str | None = None,
) -> list[tuple[str, str]]:
    """Return (name, value) pairs ready for StreamingHttpResponse."""
    from gateway.proxy.headers import is_hop_by_hop

    prefix = route.effective_prefix
    pairs: list[tuple[str, str]] = []

    if hasattr(headers, "multi_items"):
        items = headers.multi_items()
    else:
        items = list(headers.items())

    for name, value in items:
        if is_hop_by_hop(name):
            continue
        lower = name.lower()
        if lower == "set-cookie":
            value = rewrite_set_cookie(value, prefix)
        elif lower == "location":
            value = rewrite_location(value, request, route, target_url=target_url)
        pairs.append((name, value))

    return pairs


def _apply_set_cookie_header(response, header_value: str) -> None:
    """Parse Set-Cookie into Django response.cookies (supports multiple cookies)."""
    jar = SimpleCookie()
    jar.load(header_value)
    for name, morsel in jar.items():
        max_age = morsel.get("max-age")
        response.set_cookie(
            key=name,
            value=morsel.value,
            path=morsel.get("path") or "/",
            domain=morsel.get("domain") or None,
            secure=bool(morsel.get("secure")),
            httponly=bool(morsel.get("httponly")),
            samesite=morsel.get("samesite"),
            max_age=int(max_age) if max_age and str(max_age).isdigit() else None,
            expires=morsel.get("expires"),
        )


def set_response_headers(response, header_pairs: list[tuple[str, str]]) -> None:
    """Apply header list to Django response (multiple Set-Cookie via set_cookie)."""
    for name, value in header_pairs:
        if name.lower() == "set-cookie":
            _apply_set_cookie_header(response, value)
        else:
            response[name] = value
