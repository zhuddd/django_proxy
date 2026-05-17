from datetime import datetime

from ninja import Schema


class ProxyRouteIn(Schema):
    prefix: str
    target_url: str
    enabled: bool = True
    description: str = ""


class ProxyRouteUpdate(Schema):
    prefix: str | None = None
    target_url: str | None = None
    enabled: bool | None = None
    description: str | None = None


class ProxyRouteOut(Schema):
    id: int
    prefix: str
    target_url: str
    enabled: bool
    description: str
    created_at: datetime
    updated_at: datetime
