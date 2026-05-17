from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, re_path
from django.views.static import serve

from gateway.api import api
from gateway.views import proxy_view, spa_view

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", api.urls),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

_frontend_dist = settings.BASE_DIR / "frontend" / "dist"
_assets_root = _frontend_dist / "assets"

urlpatterns += [
    re_path(
        r"^assets/(?P<path>.*)$",
        serve,
        {"document_root": _assets_root},
    ),
    # Vue SPA console routes (sync)
    re_path(r"^login/?$", spa_view, name="spa-login"),
    re_path(r"^routes/?$", spa_view, name="spa-routes"),
    re_path(r"^nodes/?$", spa_view, name="spa-nodes"),
    re_path(r"^logs/?$", spa_view, name="spa-logs"),
    re_path(r"^live/?$", spa_view, name="spa-live"),
    re_path(r"^config/?$", spa_view, name="spa-config"),
    path("", spa_view, name="spa-index"),
    # Transparent proxy (async) — must be last
    re_path(r"^(?P<path>.*)$", proxy_view),
]
