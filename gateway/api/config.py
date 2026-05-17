from django.shortcuts import get_object_or_404
from ninja import Router

from gateway.models import SystemConfig
from gateway.schemas.config import ConfigIn, ConfigOut

router = Router()


@router.get("", response=list[ConfigOut])
def list_config(request):
    return list(SystemConfig.objects.all())


@router.put("/{key}", response=ConfigOut)
def update_config(request, key: str, payload: ConfigIn):
    obj, _ = SystemConfig.objects.get_or_create(key=key)
    obj.value = payload.value
    if payload.description is not None:
        obj.description = payload.description
    obj.save()
    return obj
