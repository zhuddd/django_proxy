from ninja import Router
from ninja.errors import HttpError

from gateway.models import NodeStatus
from gateway.schemas.nodes import NodeStatusOut
from gateway.services.health_checker import schedule_health_checks

router = Router()


@router.get("", response=list[NodeStatusOut])
def list_nodes(request):
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
    """Non-blocking: runs in a short-lived background thread."""
    if not schedule_health_checks():
        raise HttpError(409, "Health check already in progress")
    return {"success": True, "message": "Health check scheduled"}
