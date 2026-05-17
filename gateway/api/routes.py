from django.shortcuts import get_object_or_404
from ninja import Router

from gateway.models import NodeStatus, ProxyRoute
from gateway.proxy.route_cache import invalidate_route_cache
from gateway.schemas.routes import ProxyRouteIn, ProxyRouteOut, ProxyRouteUpdate

router = Router()


def _normalize_prefix(prefix: str) -> str:
    p = prefix.strip()
    if not p.startswith("/"):
        p = "/" + p
    return p.rstrip("/") or "/"


@router.get("", response=list[ProxyRouteOut])
def list_routes(request):
    return list(ProxyRoute.objects.all().order_by("-prefix"))


@router.post("", response=ProxyRouteOut)
def create_route(request, payload: ProxyRouteIn):
    route = ProxyRoute.objects.create(
        prefix=_normalize_prefix(payload.prefix),
        target_url=payload.target_url.rstrip("/"),
        enabled=payload.enabled,
        description=payload.description,
    )
    NodeStatus.objects.get_or_create(route=route)
    invalidate_route_cache()
    return route


@router.get("/{route_id}", response=ProxyRouteOut)
def get_route(request, route_id: int):
    return get_object_or_404(ProxyRoute, pk=route_id)


@router.put("/{route_id}", response=ProxyRouteOut)
def update_route(request, route_id: int, payload: ProxyRouteUpdate):
    route = get_object_or_404(ProxyRoute, pk=route_id)
    data = payload.dict(exclude_unset=True)
    if "prefix" in data and data["prefix"] is not None:
        data["prefix"] = _normalize_prefix(data["prefix"])
    if "target_url" in data and data["target_url"] is not None:
        data["target_url"] = data["target_url"].rstrip("/")
    for k, v in data.items():
        setattr(route, k, v)
    route.save()
    invalidate_route_cache()
    return route


@router.delete("/{route_id}")
def delete_route(request, route_id: int):
    route = get_object_or_404(ProxyRoute, pk=route_id)
    route.delete()
    invalidate_route_cache()
    return {"success": True}
