"""代理访问日志 REST API（含统计子路由）。"""

from ninja import Router, Query

from transparent_proxy_gateway.api.stats import router as stats_router
from transparent_proxy_gateway.models import ProxyLog
from transparent_proxy_gateway.schemas.logs import ProxyLogOut

router = Router()
router.add_router("/stats", stats_router, tags=["Log Stats"])


@router.get("", response=list[ProxyLogOut])
def list_logs(
    request,
    limit: int = Query(50, le=500),
    offset: int = Query(0, ge=0),
    method: str | None = None,
    status_code: int | None = None,
):
    """分页查询访问日志，可按方法与状态码过滤。"""
    qs = ProxyLog.objects.all()
    if method:
        qs = qs.filter(method__iexact=method)
    if status_code is not None:
        qs = qs.filter(status_code=status_code)
    return list(qs[offset : offset + limit])


@router.get("/{log_id}", response=ProxyLogOut)
def get_log(request, log_id: int):
    """按 ID 获取单条日志。"""
    from django.shortcuts import get_object_or_404

    return get_object_or_404(ProxyLog, pk=log_id)
