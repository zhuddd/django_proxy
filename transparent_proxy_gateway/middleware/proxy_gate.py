"""
代理门禁中间件：为管理 API 等路径设置 ``proxy_skip``，避免被兜底代理视图拦截。

前端静态路径（如 ``/assets/``）由宿主项目在 ``PROXY_EXTRA_SKIP_PREFIXES`` 中配置，
网关包不负责前端资源。
"""

from django.conf import settings
from django.utils.deprecation import MiddlewareMixin

# 网关内置跳过前缀（不含宿主前端路径，见 PROXY_EXTRA_SKIP_PREFIXES）
_DEFAULT_SKIP_PREFIXES = (
    "/api/",
    "/ws/",
    "/media/",
    "/admin/",
)


def get_proxy_skip_prefixes() -> tuple[str, ...]:
    """合并默认前缀与宿主 ``settings.PROXY_EXTRA_SKIP_PREFIXES``。"""
    extra = tuple(getattr(settings, "PROXY_EXTRA_SKIP_PREFIXES", ()) or ())
    return _DEFAULT_SKIP_PREFIXES + extra


class ProxyGateMiddleware(MiddlewareMixin):
    """同步/异步（Daphne）均可用的请求标记中间件。"""

    def process_request(self, request):
        request.proxy_skip = any(
            request.path.startswith(p) for p in get_proxy_skip_prefixes()
        )
        return None
