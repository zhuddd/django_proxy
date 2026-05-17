from django.shortcuts import get_object_or_404
from ninja import Router
from ninja.errors import HttpError

from gateway.models import NodeStatus, ProxyRoute
from gateway.proxy.route_cache import invalidate_route_cache
from gateway.proxy.route_rules import (
    normalize_route_prefix,
    validate_no_wildcard_conflict,
    validate_wildcard_scope_clean,
    validate_wildcard_uniqueness,
)
from gateway.schemas.routes import ProxyRouteIn, ProxyRouteOut, ProxyRouteUpdate

router = Router()


def _prepare_prefix(prefix: str, *, route_id: int | None = None) -> str:
    try:
        normalized = normalize_route_prefix(prefix)
        validate_wildcard_uniqueness(normalized, exclude_route_id=route_id)
        validate_wildcard_scope_clean(normalized, exclude_route_id=route_id)
        validate_no_wildcard_conflict(normalized)
    except ValueError as exc:
        raise HttpError(400, str(exc)) from exc
    return normalized


@router.get("", response=list[ProxyRouteOut])
def list_routes(request):
    return list(ProxyRoute.objects.all().order_by("-prefix"))


@router.post("", response=ProxyRouteOut)
def create_route(request, payload: ProxyRouteIn):
    prefix = _prepare_prefix(payload.prefix)
    route = ProxyRoute.objects.create(
        prefix=prefix,
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
        data["prefix"] = _prepare_prefix(data["prefix"], route_id=route_id)
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
