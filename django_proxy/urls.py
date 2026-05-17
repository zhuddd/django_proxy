"""
项目根 URL 配置：Admin、REST API、演示管理台 SPA、透明代理兜底。
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path

from django_proxy.frontend_urls import build_spa_urlpatterns
from django_proxy.gateway_api import api
from transparent_proxy_gateway.integration import build_proxy_catchall

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", api.urls),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# 演示管理台 SPA（本仓库 frontend/，非网关包职责）
urlpatterns += build_spa_urlpatterns()

# 透明代理 catch-all（须在最后）
urlpatterns.append(build_proxy_catchall())
