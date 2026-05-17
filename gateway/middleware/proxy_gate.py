"""
Mark admin/API/static paths so the catch-all proxy view can skip them.
"""

from django.utils.deprecation import MiddlewareMixin

PROXY_SKIP_PREFIXES = (
    "/api/",
    "/static/",
    "/assets/",
    "/ws/",
    "/media/",
    "/admin/",
)


class ProxyGateMiddleware(MiddlewareMixin):
    """Works in both sync (test client) and async (Daphne) modes."""

    def process_request(self, request):
        request.proxy_skip = any(
            request.path.startswith(p) for p in PROXY_SKIP_PREFIXES
        )
        return None
