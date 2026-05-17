import asyncio

from django.core.management.base import BaseCommand

from gateway.services.health_checker import health_checker_loop


class Command(BaseCommand):
    help = "Run upstream health checker loop (for production sidecar)"

    def handle(self, *args, **options):
        self.stdout.write("Starting health checker...")
        asyncio.run(health_checker_loop())
