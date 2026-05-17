from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from gateway.models import ProxyRoute

if TYPE_CHECKING:
    pass

_lock = asyncio.Lock()
_routes: list[ProxyRoute] | None = None


async def get_routes(force: bool = False) -> list[ProxyRoute]:
    global _routes
    if _routes is not None and not force:
        return _routes

    async with _lock:
        if _routes is not None and not force:
            return _routes
        from asgiref.sync import sync_to_async

        _routes = await sync_to_async(list)(
            ProxyRoute.objects.filter(enabled=True).order_by("-prefix")
        )
        return _routes


def invalidate_route_cache():
    global _routes
    _routes = None


@receiver(post_save, sender=ProxyRoute)
@receiver(post_delete, sender=ProxyRoute)
def _on_route_change(sender, **kwargs):
    invalidate_route_cache()
