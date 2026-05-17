"""以前台进程方式运行健康检查循环（适合生产侧车）。"""

import asyncio

from django.core.management.base import BaseCommand

from transparent_proxy_gateway.services.health_checker import health_checker_loop


class Command(BaseCommand):
    """阻塞运行 ``health_checker_loop``，直至进程退出。"""

    help = "Run upstream health checker loop (for production sidecar)"

    def handle(self, *args, **options):
        self.stdout.write("Starting health checker...")
        asyncio.run(health_checker_loop())
