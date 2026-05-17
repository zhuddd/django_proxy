from django.conf import settings
from django.db import models


class ProxyRoute(models.Model):
    """Prefix-based transparent proxy route."""

    prefix = models.CharField(max_length=500, unique=True, db_index=True)
    target_url = models.URLField(max_length=2048, help_text="Upstream base URL, e.g. http://192.168.1.2:8000")
    enabled = models.BooleanField(default=True, db_index=True)
    description = models.CharField(max_length=500, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-prefix"]

    def __str__(self):
        return f"{self.prefix} -> {self.target_url}"

    @property
    def normalized_prefix(self) -> str:
        from gateway.proxy.route_rules import effective_prefix, is_wildcard_prefix

        p = self.prefix.strip()
        if not p.startswith("/"):
            p = "/" + p
        if is_wildcard_prefix(p):
            return p
        return p.rstrip("/") or "/"

    @property
    def is_wildcard(self) -> bool:
        from gateway.proxy.route_rules import is_wildcard_prefix

        return is_wildcard_prefix(self.prefix)

    @property
    def effective_prefix(self) -> str:
        from gateway.proxy.route_rules import effective_prefix as eff

        return eff(self.prefix)


class ProxyLog(models.Model):
    method = models.CharField(max_length=16, db_index=True)
    path = models.TextField()
    target_url = models.TextField()
    status_code = models.PositiveIntegerField(null=True, blank=True, db_index=True)
    request_headers = models.JSONField(default=dict)
    response_headers = models.JSONField(default=dict)
    latency_ms = models.FloatField(default=0)
    client_ip = models.GenericIPAddressField(null=True, blank=True)
    route = models.ForeignKey(
        ProxyRoute,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="logs",
    )
    error_message = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["-created_at", "method"]),
        ]


class NodeStatus(models.Model):
    route = models.OneToOneField(ProxyRoute, on_delete=models.CASCADE, related_name="node_status")
    is_online = models.BooleanField(default=False, db_index=True)
    response_time_ms = models.FloatField(null=True, blank=True)
    last_check = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True, default="")

    class Meta:
        verbose_name_plural = "Node statuses"

    def __str__(self):
        state = "online" if self.is_online else "offline"
        return f"{self.route.prefix} [{state}]"


class SystemConfig(models.Model):
    key = models.CharField(max_length=128, unique=True)
    value = models.TextField(blank=True, default="")
    description = models.CharField(max_length=500, blank=True, default="")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "System configuration"

    def __str__(self):
        return self.key

    @classmethod
    def get_value(cls, key: str, default: str = "") -> str:
        try:
            return cls.objects.get(key=key).value
        except cls.DoesNotExist:
            return default


def default_configs():
    defaults = {
        "health_check_interval": str(getattr(settings, "HEALTH_CHECK_INTERVAL", 30)),
        "health_check_timeout": str(getattr(settings, "HEALTH_CHECK_TIMEOUT", 5)),
        "log_retention_days": str(getattr(settings, "LOG_RETENTION_DAYS", 7)),
        "proxy_connect_timeout": str(getattr(settings, "PROXY_CONNECT_TIMEOUT", 10)),
        "proxy_read_timeout": str(getattr(settings, "PROXY_READ_TIMEOUT", 300)),
    }
    for key, value in defaults.items():
        SystemConfig.objects.get_or_create(key=key, defaults={"value": value})
