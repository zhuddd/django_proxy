"""初始化网关默认系统配置的管理命令。"""

from django.core.management.base import BaseCommand

from transparent_proxy_gateway.models import default_configs


class Command(BaseCommand):
    """将 settings 中的默认值写入 SystemConfig 表。"""

    help = "Initialize system config defaults"

    def handle(self, *args, **options):
        default_configs()
        self.stdout.write(self.style.SUCCESS("Gateway defaults initialized"))
