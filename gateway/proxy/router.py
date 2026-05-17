from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlparse

from gateway.models import ProxyRoute


@dataclass(frozen=True)
class RouteMatch:
    route: ProxyRoute
    target_url: str


def normalize_path(path: str) -> str:
    if not path:
        return "/"
    if not path.startswith("/"):
        path = "/" + path
    return path


def prefix_matches(request_path: str, prefix: str) -> bool:
    req = normalize_path(request_path)
    pre = normalize_path(prefix)
    if pre == "/":
        return True
    return req == pre or req.startswith(pre + "/")


def match_route(request_path: str, routes: list[ProxyRoute]) -> RouteMatch | None:
    """Longest prefix wins."""
    path = normalize_path(request_path)
    enabled = [r for r in routes if r.enabled]
    enabled.sort(key=lambda r: len(r.normalized_prefix), reverse=True)

    for route in enabled:
        if prefix_matches(path, route.normalized_prefix):
            return RouteMatch(route=route, target_url=build_target_url(route, path, ""))
    return None


def build_target_url(route: ProxyRoute, path: str, query_string: str) -> str:
    """
    Prefix forwarding: /account/login on proxy -> {target}/account/login
    No path rewrite — full request path is appended to upstream base.
    """
    base = route.target_url.rstrip("/")
    full_path = normalize_path(path)
    url = f"{base}{full_path}"
    if query_string:
        sep = "&" if "?" in url else "?"
        if not query_string.startswith("?"):
            url = f"{url}?{query_string.lstrip('?')}"
        else:
            url = f"{url}{query_string}"
    return url


def build_target_from_request(route: ProxyRoute, full_path: str) -> str:
    if "?" in full_path:
        path, _, qs = full_path.partition("?")
        return build_target_url(route, path, qs)
    return build_target_url(route, full_path, "")


def upstream_host_header(target_url: str) -> str:
    parsed = urlparse(target_url)
    port = parsed.port
    if port and port not in (80, 443):
        return f"{parsed.hostname}:{port}"
    return parsed.hostname or ""
