"""代理路由 API 的输入/输出 Schema。"""

from datetime import datetime

from ninja import Schema


class ProxyRouteIn(Schema):
    """创建代理路由的请求体。"""

    prefix: str
    target_url: str
    enabled: bool = True
    description: str = ""


class ProxyRouteUpdate(Schema):
    """更新代理路由的请求体（字段均可选）。"""

    prefix: str | None = None
    target_url: str | None = None
    enabled: bool | None = None
    description: str | None = None


class ProxyRouteOut(Schema):
    """代理路由详情输出。"""

    id: int
    prefix: str
    target_url: str
    enabled: bool
    description: str
    is_wildcard: bool = False
    created_at: datetime
    updated_at: datetime

    @staticmethod
    def resolve_is_wildcard(obj):
        return obj.is_wildcard
