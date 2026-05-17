"""
通配符路由规则：前缀规范化、作用域唯一性与冲突校验。

仅支持末尾 ``/*``（如 ``/*``、``/robot/*``）。每个作用域最多一条通配路由；
同一作用域不能同时存在通配与更具体的字面量前缀。
"""

from __future__ import annotations

WILDCARD_SUFFIX = "/*"


def normalize_path(path: str) -> str:
    """规范化路径：保证以 ``/`` 开头。"""
    if not path:
        return "/"
    if not path.startswith("/"):
        path = "/" + path
    return path


def is_wildcard_prefix(prefix: str) -> bool:
    """判断前缀是否以 ``/*`` 结尾（通配符路由）。"""
    return prefix.endswith(WILDCARD_SUFFIX)


def wildcard_base(prefix: str) -> str:
    """通配前缀的作用域根路径；``/*`` 的根为 ``/``。"""
    if prefix == WILDCARD_SUFFIX:
        return "/"
    return prefix[: -len(WILDCARD_SUFFIX)]


def effective_prefix(prefix: str) -> str:
    """用于匹配、Cookie Path 与重定向改写的前缀（通配符取 base）。"""
    if is_wildcard_prefix(prefix):
        return normalize_path(wildcard_base(prefix))
    return normalize_path(prefix)


def route_specificity(prefix: str) -> int:
    """前缀有效长度，用于最长前缀优先排序。"""
    return len(effective_prefix(prefix))


def normalize_route_prefix(prefix: str) -> str:
    """保存路由前的前缀规范化与通配符格式校验。"""
    p = prefix.strip()
    if not p.startswith("/"):
        p = "/" + p

    if "*" not in p:
        return normalize_path(p)

    if not p.endswith(WILDCARD_SUFFIX):
        raise ValueError("Wildcard must be suffix /* only, e.g. /robot/* or /*")
    if p.count("*") > 1:
        raise ValueError("Only one wildcard /* per route prefix")
    if p == WILDCARD_SUFFIX:
        return WILDCARD_SUFFIX

    base = p[: -len(WILDCARD_SUFFIX)]
    if not base or base == "/":
        raise ValueError("Use /* for global catch-all route")
    return normalize_path(base) + WILDCARD_SUFFIX


def wildcard_scope_key(prefix: str) -> str:
    """通配路由的作用域键（同键仅允许一条通配上游）。"""
    if not is_wildcard_prefix(prefix):
        return ""
    return effective_prefix(prefix)


def validate_wildcard_uniqueness(
    prefix: str,
    *,
    exclude_route_id: int | None = None,
) -> None:
    """同一通配作用域内不得重复注册通配路由。"""
    if not is_wildcard_prefix(prefix):
        return

    from transparent_proxy_gateway.models import ProxyRoute

    scope = wildcard_scope_key(prefix)
    qs = ProxyRoute.objects.filter(prefix__endswith=WILDCARD_SUFFIX)
    if exclude_route_id is not None:
        qs = qs.exclude(pk=exclude_route_id)

    for other in qs.only("id", "prefix"):
        if wildcard_scope_key(other.prefix) == scope:
            raise ValueError(
                f"Wildcard scope {scope or '/'} already has route {other.prefix}; "
                "only one upstream per wildcard scope"
            )


def validate_no_wildcard_conflict(prefix: str) -> None:
    """注册字面量前缀时，不得落在已有通配作用域之下。"""
    if is_wildcard_prefix(prefix):
        return

    from transparent_proxy_gateway.models import ProxyRoute

    norm = normalize_path(prefix)
    for route in ProxyRoute.objects.filter(prefix__endswith=WILDCARD_SUFFIX).only("prefix"):
        base = effective_prefix(route.prefix)
        if base == "/":
            continue
        if norm == base or norm.startswith(base + "/"):
            raise ValueError(
                f"Path {norm} is covered by wildcard route {route.prefix}; "
                "remove or change the wildcard route first"
            )


def validate_wildcard_scope_clean(
    prefix: str,
    *,
    exclude_route_id: int | None = None,
) -> None:
    """注册通配前缀时，作用域内不得已有更具体的字面量路由。"""
    if not is_wildcard_prefix(prefix):
        return

    base = effective_prefix(prefix)
    if base == "/":
        return

    from transparent_proxy_gateway.models import ProxyRoute

    qs = ProxyRoute.objects.exclude(prefix__endswith=WILDCARD_SUFFIX)
    if exclude_route_id is not None:
        qs = qs.exclude(pk=exclude_route_id)

    for route in qs.only("prefix"):
        norm = normalize_path(route.prefix)
        if norm == base or norm.startswith(base + "/"):
            raise ValueError(
                f"Wildcard {prefix} conflicts with existing route {route.prefix}; "
                "one upstream per scope (wildcard or literal, not both)"
            )