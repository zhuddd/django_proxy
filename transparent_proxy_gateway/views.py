"""HTTP 透明代理 ASGI 视图（不含前端 SPA 或静态资源）。"""

from django.http import Http404, HttpResponseNotFound

from transparent_proxy_gateway.proxy.core import forward_request


async def proxy_view(request, path: str = ""):
    """
    URL 兜底视图：将请求交给 ``forward_request`` 流式转发到上游。

    若 ``ProxyGateMiddleware`` 已标记 ``request.proxy_skip``，或无一匹配路由，则 404。
    """
    if getattr(request, "proxy_skip", False):
        raise Http404()

    result = await forward_request(request)
    if isinstance(result, HttpResponseNotFound):
        raise Http404("No proxy route matched")
    return result