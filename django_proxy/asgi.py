"""
ASGI 入口：HTTP 走 Django；WebSocket 含管理台日志与透明上游转发。
"""

import os

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "django_proxy.settings")

django_asgi_app = get_asgi_application()

from transparent_proxy_gateway.integration import get_websocket_urlpatterns  # noqa: E402

application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,
        "websocket": AllowedHostsOriginValidator(
            AuthMiddlewareStack(URLRouter(get_websocket_urlpatterns()))
        ),
    }
)
