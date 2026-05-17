"""Django 应用配置：应用就绪时注册信号并启动健康检查（数据库由宿主项目配置）。"""

import os
import sys

from django.apps import AppConfig
from loguru import logger


class GatewayConfig(AppConfig):
    """透明代理网关应用入口。"""

    default_auto_field = "django.db.models.BigAutoField"
    name = "transparent_proxy_gateway"
    verbose_name = "Transparent Proxy Gateway"

    def ready(self):
        """应用加载完成后初始化路由缓存与健康检查（使用宿主 DATABASES）。"""
        import transparent_proxy_gateway.signals  # noqa: F401
        import transparent_proxy_gateway.proxy.route_cache  # noqa: F401

        if "migrate" in sys.argv or "makemigrations" in sys.argv:
            return
        # StatReloader 会起父子进程，仅在子进程启动一次
        if "runserver" in sys.argv and os.environ.get("RUN_MAIN") != "true":
            return
        if "runserver" in sys.argv or "daphne" in sys.argv or "uvicorn" in sys.argv:
            try:
                from transparent_proxy_gateway.services.health_checker import start_health_checker

                start_health_checker()
            except Exception:
                logger.exception("Failed to start health checker")
