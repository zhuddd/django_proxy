from django.db.models.signals import post_save
from django.dispatch import receiver

from gateway.models import NodeStatus, ProxyRoute


@receiver(post_save, sender=ProxyRoute)
def ensure_node_status(sender, instance, created, **kwargs):
    if created:
        NodeStatus.objects.get_or_create(route=instance)
