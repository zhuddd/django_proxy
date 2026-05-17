from ninja import Router, Query

from gateway.models import ProxyLog
from gateway.schemas.logs import ProxyLogOut

router = Router()


@router.get("", response=list[ProxyLogOut])
def list_logs(
    request,
    limit: int = Query(50, le=500),
    offset: int = Query(0, ge=0),
    method: str | None = None,
    status_code: int | None = None,
):
    qs = ProxyLog.objects.all()
    if method:
        qs = qs.filter(method__iexact=method)
    if status_code is not None:
        qs = qs.filter(status_code=status_code)
    return list(qs[offset : offset + limit])


@router.get("/{log_id}", response=ProxyLogOut)
def get_log(request, log_id: int):
    from django.shortcuts import get_object_or_404

    return get_object_or_404(ProxyLog, pk=log_id)
