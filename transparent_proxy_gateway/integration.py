"""
将透明代理网关接入 Django 项目的 ``urls.py`` / ``asgi.py`` 的辅助函数。

提供各 ``Router`` 挂载方式、中间件路径、WebSocket 路由与 HTTP 代理兜底；
**不包含** ``NinjaAPI`` 与前端 SPA（均在宿主项目配置）。

数据库：在宿主 ``settings.DATABASES`` 中配置后执行
``migrate transparent_proxy_gateway``。
"""

from __future__ import annotations

from typing import Any

from django.urls import URLPattern, URLResolver, re_path

# 默认挂载路径与 OpenAPI 标签（供宿主 add_router 参考）
DEFAULT_API_MOUNT: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    ("/routes", "routes_router", ("Routes",)),
    ("/nodes", "nodes_router", ("Nodes",)),
    ("/logs", "logs_router", ("Logs",)),
    ("/config", "config_router", ("Config",)),
)


def get_gateway_routers() -> dict[str, Any]:
    """
    返回网关子 ``Router`` 字典，键为 ``routes_router`` 等（与 ``api`` 包导出一致）。

    宿主项目自行 ``NinjaAPI.add_router`` 挂载。
    """
    from transparent_proxy_gateway.api import (
        config_router,
        logs_router,
        nodes_router,
        routes_router,
    )

    return {
        "routes_router": routes_router,
        "nodes_router": nodes_router,
        "logs_router": logs_router,
        "config_router": config_router,
    }


def mount_gateway_routers(ninja_api: Any) -> None:
    """
    便捷方法：将四个子 Router 挂到宿主已创建的 ``NinjaAPI`` 实例上。

    Args:
        ninja_api: 宿主项目中的 ``NinjaAPI`` 实例（类型不在本包内引用）。
    """
    routers = get_gateway_routers()
    for path, attr, tags in DEFAULT_API_MOUNT:
        ninja_api.add_router(path, routers[attr], tags=list(tags))


def get_proxy_gate_middleware() -> str:
    """返回代理门禁中间件的完整 Python 导入路径。"""
    return "transparent_proxy_gateway.middleware.proxy_gate.ProxyGateMiddleware"


def get_websocket_urlpatterns():
    """
    返回 WebSocket URL 模式：``/ws/logs/`` 管理台日志 + 其余路径透明转发上游。

    在 ``asgi.py`` 中挂到 ``ProtocolTypeRouter`` 的 ``websocket`` 键即可。
    """
    from transparent_proxy_gateway.routing import websocket_urlpatterns

    return websocket_urlpatterns


def build_proxy_catchall() -> URLPattern:
    """构建异步代理兜底路由，须放在 ``urlpatterns`` 最后。"""
    from transparent_proxy_gateway.views import proxy_view

    return re_path(r"^(?P<path>.*)$", proxy_view)
