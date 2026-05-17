"""模型信号：新建代理路由时自动创建对应的节点健康状态记录。"""

from django.db.models.signals import post_save
from django.dispatch import receiver

from transparent_proxy_gateway.models import NodeStatus, ProxyRoute


@receiver(post_save, sender=ProxyRoute)
def ensure_node_status(sender, instance, created, **kwargs):
    """路由首次创建时确保存在 NodeStatus 行。"""
    if created:
        NodeStatus.objects.get_or_create(route=instance)
