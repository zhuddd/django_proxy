"""上游节点健康状态 REST API。"""

from ninja import Router
from ninja.errors import HttpError

from transparent_proxy_gateway.models import NodeStatus
from transparent_proxy_gateway.schemas.nodes import NodeStatusOut
from transparent_proxy_gateway.services.health_checker import schedule_health_checks

router = Router()


@router.get("", response=list[NodeStatusOut])
def list_nodes(request):
    """列出各路由对应的上游健康状态。"""
    qs = NodeStatus.objects.select_related("route").all()
    return [
        NodeStatusOut(
            id=n.id,
            route_id=n.route_id,
            route_prefix=n.route.prefix,
            target_url=n.route.target_url,
            is_online=n.is_online,
            response_time_ms=n.response_time_ms,
            last_check=n.last_check,
            error_message=n.error_message,
        )
        for n in qs
    ]


@router.post("/check")
def trigger_check(request):
    """触发一次健康检查（后台线程，不阻塞 HTTP 工作进程）。"""
    if not schedule_health_checks():
        raise HttpError(409, "Health check already in progress")
    return {"success": True, "message": "Health check scheduled"}
