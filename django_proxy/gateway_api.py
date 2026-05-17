"""
演示项目 Django-Ninja 根 API：在此创建 ``NinjaAPI`` 并挂载网关 Router。

网关包 ``transparent_proxy_gateway`` 仅提供 ``Router``，不包含 ``NinjaAPI``。
"""

from ninja import NinjaAPI

from transparent_proxy_gateway.integration import mount_gateway_routers

api = NinjaAPI(
    title="Transparent Proxy Gateway",
    version="0.2.0",
    urls_namespace="gateway-api",
)

mount_gateway_routers(api)
