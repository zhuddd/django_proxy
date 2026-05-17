"""共享 httpx 异步客户端池（禁用系统 HTTP_PROXY，统一 TLS 配置）。"""

from __future__ import annotations

import httpx
from django.conf import settings
from loguru import logger

from transparent_proxy_gateway.proxy.ssl_config import get_proxy_ssl_verify, log_ssl_verify_mode


class HttpClientPool:
    """进程内单例 ``httpx.AsyncClient``，供 HTTP 代理与健康检查复用。"""

    _instance: httpx.AsyncClient | None = None

    @classmethod
    def get_client(cls) -> httpx.AsyncClient:
        """获取或懒创建全局 httpx 客户端。"""
        if cls._instance is None or cls._instance.is_closed:
            connect = float(getattr(settings, "PROXY_CONNECT_TIMEOUT", 10))
            read = float(getattr(settings, "PROXY_READ_TIMEOUT", 300))
            limits = httpx.Limits(
                max_connections=getattr(settings, "HTTPX_MAX_CONNECTIONS", 200),
                max_keepalive_connections=getattr(settings, "HTTPX_MAX_KEEPALIVE", 50),
            )
            verify = get_proxy_ssl_verify()
            log_ssl_verify_mode()
            cls._instance = httpx.AsyncClient(
                timeout=httpx.Timeout(
                    connect=connect, read=read, write=read, pool=connect
                ),
                limits=limits,
                follow_redirects=False,
                trust_env=False,
                proxy=None,
                verify=verify,
            )
            if verify is False:
                logger.debug("Proxy httpx client created with verify=False")
        return cls._instance

    @classmethod
    async def aclose(cls) -> None:
        """关闭并释放全局客户端（测试或进程退出时调用）。"""
        if cls._instance and not cls._instance.is_closed:
            await cls._instance.aclose()
            cls._instance = None


def get_http_client() -> httpx.AsyncClient:
    """返回共享 httpx 异步客户端。"""
    return HttpClientPool.get_client()