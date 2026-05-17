from django.urls import re_path

from gateway.consumers import ProxyLogConsumer

websocket_urlpatterns = [
    re_path(r"ws/logs/$", ProxyLogConsumer.as_asgi()),
]
