from __future__ import annotations

import httpx
from django.conf import settings


class HttpClientPool:
    """Shared httpx.AsyncClient — direct upstream only (no system HTTP_PROXY)."""

    _instance: httpx.AsyncClient | None = None

    @classmethod
    def get_client(cls) -> httpx.AsyncClient:
        if cls._instance is None or cls._instance.is_closed:
            connect = float(getattr(settings, "PROXY_CONNECT_TIMEOUT", 10))
            read = float(getattr(settings, "PROXY_READ_TIMEOUT", 300))
            limits = httpx.Limits(
                max_connections=getattr(settings, "HTTPX_MAX_CONNECTIONS", 200),
                max_keepalive_connections=getattr(settings, "HTTPX_MAX_KEEPALIVE", 50),
            )
            cls._instance = httpx.AsyncClient(
                timeout=httpx.Timeout(
                    connect=connect, read=read, write=read, pool=connect
                ),
                limits=limits,
                follow_redirects=False,
                trust_env=False,
                proxy=None,
            )
        return cls._instance

    @classmethod
    async def aclose(cls) -> None:
        if cls._instance and not cls._instance.is_closed:
            await cls._instance.aclose()
            cls._instance = None


def get_http_client() -> httpx.AsyncClient:
    return HttpClientPool.get_client()
