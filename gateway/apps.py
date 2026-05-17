import os
import sys

from django.apps import AppConfig
from loguru import logger


class GatewayConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "gateway"
    verbose_name = "Transparent Proxy Gateway"

    def ready(self):
        import gateway.signals  # noqa: F401
        import gateway.proxy.route_cache  # noqa: F401

        if "migrate" in sys.argv or "makemigrations" in sys.argv:
            return
        # Avoid starting twice under StatReloader (parent + child process).
        if "runserver" in sys.argv and os.environ.get("RUN_MAIN") != "true":
            return
        if "runserver" in sys.argv or "daphne" in sys.argv or "uvicorn" in sys.argv:
            try:
                from gateway.services.health_checker import start_health_checker

                start_health_checker()
            except Exception:
                logger.exception("Failed to start health checker")
