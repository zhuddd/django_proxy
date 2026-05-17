from pathlib import Path

from django.conf import settings
from django.http import FileResponse, Http404, HttpResponseNotFound

from gateway.proxy.core import forward_request


def _spa_index_path() -> Path:
    return Path(settings.BASE_DIR) / "frontend" / "dist" / "index.html"


def spa_view(request):
    """Serve Vue SPA entry (sync — safe under Daphne + WhiteNoise)."""
    index = _spa_index_path()
    if not index.exists():
        raise Http404(
            "Frontend not built. Run: cd frontend && npm install && npm run build"
        )
    return FileResponse(index.open("rb"), content_type="text/html")


async def proxy_view(request, path: str = ""):
    """ASGI async catch-all transparent proxy for registered prefixes."""
    if getattr(request, "proxy_skip", False):
        raise Http404()

    result = await forward_request(request)
    if isinstance(result, HttpResponseNotFound):
        raise Http404("No proxy route matched")
    return result
