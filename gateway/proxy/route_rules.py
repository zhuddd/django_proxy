"""
Route prefix normalization and wildcard constraints.

Wildcard routes use a trailing ``/*`` (e.g. ``/*``, ``/robot/*``).
At most one wildcard route per scope (one ``/*``, one ``/robot/*``, etc.).
"""

from __future__ import annotations

WILDCARD_SUFFIX = "/*"


def normalize_path(path: str) -> str:
    if not path:
        return "/"
    if not path.startswith("/"):
        path = "/" + path
    return path


def is_wildcard_prefix(prefix: str) -> bool:
    return prefix.endswith(WILDCARD_SUFFIX)


def wildcard_base(prefix: str) -> str:
    """Base path before ``/*``; ``/*`` -> ``/``."""
    if prefix == WILDCARD_SUFFIX:
        return "/"
    return prefix[: -len(WILDCARD_SUFFIX)]


def effective_prefix(prefix: str) -> str:
    """Prefix used for forwarding / cookie / redirect rewriting."""
    if is_wildcard_prefix(prefix):
        return normalize_path(wildcard_base(prefix))
    return normalize_path(prefix)


def route_specificity(prefix: str) -> int:
    """Higher = more specific (longest-prefix wins)."""
    return len(effective_prefix(prefix))


def normalize_route_prefix(prefix: str) -> str:
    p = prefix.strip()
    if not p.startswith("/"):
        p = "/" + p

    if "*" not in p:
        return normalize_path(p)

    if not p.endswith(WILDCARD_SUFFIX):
        raise ValueError("通配符仅允许出现在路径末尾，格式如 /robot/* 或 /*")
    if p.count("*") > 1:
        raise ValueError("每条路由只能包含一个通配符 /*")
    if p == WILDCARD_SUFFIX:
        return WILDCARD_SUFFIX

    base = p[: -len(WILDCARD_SUFFIX)]
    if not base or base == "/":
        raise ValueError("请使用 /* 表示全局兜底路由")
    return normalize_path(base) + WILDCARD_SUFFIX


def wildcard_scope_key(prefix: str) -> str:
    """Unique scope for wildcard uniqueness (one upstream per scope)."""
    if not is_wildcard_prefix(prefix):
        return ""
    return effective_prefix(prefix)


def validate_wildcard_uniqueness(
    prefix: str,
    *,
    exclude_route_id: int | None = None,
) -> None:
    """
    Enforce at most one wildcard route per scope:
    - only one /*
    - only one /robot/*
    """
    if not is_wildcard_prefix(prefix):
        return

    from gateway.models import ProxyRoute

    scope = wildcard_scope_key(prefix)
    qs = ProxyRoute.objects.filter(prefix__endswith=WILDCARD_SUFFIX)
    if exclude_route_id is not None:
        qs = qs.exclude(pk=exclude_route_id)

    for other in qs.only("id", "prefix"):
        if wildcard_scope_key(other.prefix) == scope:
            raise ValueError(
                f"通配符作用域 {scope or '/'} 已存在路由 {other.prefix}，"
                f"每个 /* 作用域只能配置一个上游"
            )


def validate_no_wildcard_conflict(prefix: str) -> None:
    """Reject literal prefixes covered by a non-global wildcard (e.g. /robot/*)."""
    if is_wildcard_prefix(prefix):
        return

    from gateway.models import ProxyRoute

    norm = normalize_path(prefix)
    for route in ProxyRoute.objects.filter(prefix__endswith=WILDCARD_SUFFIX).only("prefix"):
        base = effective_prefix(route.prefix)
        if base == "/":
            continue
        if norm == base or norm.startswith(base + "/"):
            raise ValueError(
                f"路径 {norm} 已被通配符路由 {route.prefix} 覆盖，"
                f"请删除或调整通配符路由后再添加"
            )


def validate_wildcard_scope_clean(
    prefix: str,
    *,
    exclude_route_id: int | None = None,
) -> None:
    """Adding /robot/* forbids existing literals under /robot (not for global /*)."""
    if not is_wildcard_prefix(prefix):
        return

    base = effective_prefix(prefix)
    if base == "/":
        return

    from gateway.models import ProxyRoute

    qs = ProxyRoute.objects.exclude(prefix__endswith=WILDCARD_SUFFIX)
    if exclude_route_id is not None:
        qs = qs.exclude(pk=exclude_route_id)

    for route in qs.only("prefix"):
        norm = normalize_path(route.prefix)
        if norm == base or norm.startswith(base + "/"):
            raise ValueError(
                f"通配符 {prefix} 与已有路由 {route.prefix} 冲突，"
                f"同一作用域下只能保留一个上游（通配符或精确前缀二选一）"
            )
