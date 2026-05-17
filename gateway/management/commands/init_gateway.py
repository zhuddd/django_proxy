from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from gateway.models import default_configs


class Command(BaseCommand):
    help = "Initialize system config defaults"

    def handle(self, *args, **options):
        default_configs()
        self.stdout.write(self.style.SUCCESS("Gateway defaults initialized"))
