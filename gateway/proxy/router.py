from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlparse

from gateway.models import ProxyRoute
from gateway.proxy.route_rules import (
    effective_prefix,
    is_wildcard_prefix,
    normalize_path,
    route_specificity,
    wildcard_base,
)


@dataclass(frozen=True)
class RouteMatch:
    route: ProxyRoute
    target_url: str


def prefix_matches(request_path: str, prefix: str) -> bool:
    req = normalize_path(request_path)

    if is_wildcard_prefix(prefix):
        base = normalize_path(wildcard_base(prefix))
        if base == "/":
            return True
        return req == base or req.startswith(base + "/")

    pre = normalize_path(prefix)
    if pre == "/":
        return True
    return req == pre or req.startswith(pre + "/")


def _route_sort_key(route: ProxyRoute) -> tuple[int, int]:
    """Longest effective prefix first; literal beats wildcard at same length."""
    p = route.prefix
    wild = 1 if is_wildcard_prefix(p) else 0
    return (-route_specificity(p), wild)


def match_route(request_path: str, routes: list[ProxyRoute]) -> RouteMatch | None:
    """Longest prefix / scope wins; literal routes beat wildcards at same depth."""
    path = normalize_path(request_path)
    enabled = [r for r in routes if r.enabled]
    enabled.sort(key=_route_sort_key)

    for route in enabled:
        if prefix_matches(path, route.prefix):
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
