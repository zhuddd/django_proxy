"""
transparent-proxy-gateway — Django 透明 HTTP/WebSocket 反向代理网关。

- 前缀转发（支持 ``/*`` 通配）、流式 HTTP、响应头改写
- Django-Ninja 管理 API、访问日志与统计
- 使用宿主 ``settings.DATABASES``；不管理数据库连接与前端资源

集成入口见 ``transparent_proxy_gateway.integration``。
"""

__version__ = "0.2.0"
__all__ = ["__version__"]

default_app_config = "transparent_proxy_gateway.apps.GatewayConfig"
