"""系统配置 REST API。"""

from django.shortcuts import get_object_or_404
from ninja import Router

from transparent_proxy_gateway.models import SystemConfig
from transparent_proxy_gateway.schemas.config import ConfigIn, ConfigOut

router = Router()


@router.get("", response=list[ConfigOut])
def list_config(request):
    """列出全部系统配置项。"""
    return list(SystemConfig.objects.all())


@router.put("/{key}", response=ConfigOut)
def update_config(request, key: str, payload: ConfigIn):
    """按键更新或创建配置项。"""
    obj, _ = SystemConfig.objects.get_or_create(key=key)
    obj.value = payload.value
    if payload.description is not None:
        obj.description = payload.description
    obj.save()
    return obj
