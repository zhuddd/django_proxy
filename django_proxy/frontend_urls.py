"""
演示项目前端路由：Vue 管理台 SPA 与 ``assets/`` 静态资源。

仅用于本仓库 ``django_proxy`` 演示；嵌入其他项目时请自行处理前端或使用独立站点。
"""

from __future__ import annotations

from pathlib import Path
from typing import Sequence

from django.conf import settings
from django.urls import URLPattern, URLResolver, path, re_path
from django.views.static import serve

from django_proxy.views import spa_view

# 与 frontend/src/router 页面一致
SPA_ROUTE_NAMES: tuple[str, ...] = (
    "routes",
    "nodes",
    "logs",
    "stats",
    "live",
    "config",
)


def _dist_root() -> Path:
    return Path(settings.BASE_DIR) / "frontend" / "dist"


def build_spa_urlpatterns(
    *,
    spa_route_names: Sequence[str] = SPA_ROUTE_NAMES,
    assets_url_prefix: str = "assets",
) -> list[URLPattern | URLResolver]:
    """构建 SPA 壳页面与构建产物静态资源路由。"""
    patterns: list[URLPattern | URLResolver] = []
    patterns.append(
        re_path(
            rf"^{assets_url_prefix}/(?P<path>.*)$",
            serve,
            {"document_root": _dist_root() / "assets"},
        )
    )
    for name in spa_route_names:
        patterns.append(re_path(rf"^{name}/?$", spa_view, name=f"spa-{name}"))
    patterns.append(path("", spa_view, name="spa-index"))
    return patterns
