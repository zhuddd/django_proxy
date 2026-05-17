"""
网关管理 REST API（仅 ``Router``，不含 ``NinjaAPI``）。

在宿主项目中创建 ``NinjaAPI`` 后挂载，例如::

    from ninja import NinjaAPI
    from transparent_proxy_gateway.api import (
        config_router,
        logs_router,
        nodes_router,
        routes_router,
    )

    api = NinjaAPI(title="My App", version="1.0")
    api.add_router("/routes", routes_router, tags=["Routes"])
    api.add_router("/nodes", nodes_router, tags=["Nodes"])
    api.add_router("/logs", logs_router, tags=["Logs"])
    api.add_router("/config", config_router, tags=["Config"])
"""

from transparent_proxy_gateway.api.config import router as config_router
from transparent_proxy_gateway.api.logs import router as logs_router
from transparent_proxy_gateway.api.nodes import router as nodes_router
from transparent_proxy_gateway.api.routes import router as routes_router

__all__ = [
    "routes_router",
    "nodes_router",
    "logs_router",
    "config_router",
]
