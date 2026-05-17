"""
HTTP 代理子包：路由匹配、头处理、流式转发与响应改写。

对外常用入口：``proxy.core.forward_request``。
"""

from transparent_proxy_gateway.proxy.core import forward_request

__all__ = ["forward_request"]

__all__ = ["forward_request"]
