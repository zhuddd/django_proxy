"""路由匹配与上游目标 URL 构造（前缀转发，非 path rewrite）。"""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlparse

from transparent_proxy_gateway.models import ProxyRoute
from transparent_proxy_gateway.proxy.route_rules import (
    effective_prefix,
    is_wildcard_prefix,
    normalize_path,
    route_specificity,
    wildcard_base,
)


@dataclass(frozen=True)
class RouteMatch:
    """一次成功的前缀匹配结果。"""

    route: ProxyRoute
    target_url: str


def prefix_matches(request_path: str, prefix: str) -> bool:
    """判断请求路径是否落在给定前缀（含通配符语义）下。"""
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
    """排序键：有效前缀越长越优先；同长度时字面量优于通配。"""
    p = route.prefix
    wild = 1 if is_wildcard_prefix(p) else 0
    return (-route_specificity(p), wild)


def match_route(request_path: str, routes: list[ProxyRoute]) -> RouteMatch | None:
    """在已启用路由中按最长前缀（精确优于通配）匹配一条。"""
    path = normalize_path(request_path)
    enabled = [r for r in routes if r.enabled]
    enabled.sort(key=_route_sort_key)

    for route in enabled:
        if prefix_matches(path, route.prefix):
            return RouteMatch(route=route, target_url=build_target_url(route, path, ""))
    return None


def build_target_url(route: ProxyRoute, path: str, query_string: str) -> str:
    """
    拼接上游 URL（透明转发，保留完整 path）。

    示例：前缀 ``/account``、path ``/account/login`` → ``{target}/account/login``。
    """
    base = route.target_url.rstrip("/")
    full_path = normalize_path(path)
    url = f"{base}{full_path}"
    if query_string:
        if not query_string.startswith("?"):
            url = f"{url}?{query_string.lstrip('?')}"
        else:
            url = f"{url}{query_string}"
    return url


def build_target_from_request(route: ProxyRoute, full_path: str) -> str:
    """从 ``get_full_path()`` 形式的路径（含 query）构造上游 URL。"""
    if "?" in full_path:
        path, _, qs = full_path.partition("?")
        return build_target_url(route, path, qs)
    return build_target_url(route, full_path, "")


def upstream_host_header(target_url: str) -> str:
    """从目标 URL 解析发往上游的 ``Host`` 头（含非默认端口）。"""
    parsed = urlparse(target_url)
    port = parsed.port
    if port and port not in (80, 443):
        return f"{parsed.hostname}:{port}"
    return parsed.hostname or ""