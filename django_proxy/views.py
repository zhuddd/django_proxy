"""演示项目视图：Vue 管理台 SPA（网关包不负责前端）。"""

from pathlib import Path

from django.conf import settings
from django.http import FileResponse, Http404


def spa_index_path() -> Path:
    """管理台构建产物 index.html 路径。"""
    return Path(settings.BASE_DIR) / "frontend" / "dist" / "index.html"


def spa_view(request):
    """返回 Vue SPA 壳页面（需先 npm run build）。"""
    index = spa_index_path()
    if not index.exists():
        raise Http404(
            "Frontend not built. Run: cd frontend && npm install && npm run build"
        )
    return FileResponse(index.open("rb"), content_type="text/html")
