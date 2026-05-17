from django.contrib import admin

from gateway.models import NodeStatus, ProxyLog, ProxyRoute, SystemConfig


@admin.register(ProxyRoute)
class ProxyRouteAdmin(admin.ModelAdmin):
    list_display = ("prefix", "target_url", "enabled", "updated_at")
    list_filter = ("enabled",)
    search_fields = ("prefix", "target_url")


@admin.register(ProxyLog)
class ProxyLogAdmin(admin.ModelAdmin):
    list_display = ("method", "path", "status_code", "latency_ms", "client_ip", "created_at")
    list_filter = ("method", "status_code")
    readonly_fields = ("created_at",)


@admin.register(NodeStatus)
class NodeStatusAdmin(admin.ModelAdmin):
    list_display = ("route", "is_online", "response_time_ms", "last_check")


@admin.register(SystemConfig)
class SystemConfigAdmin(admin.ModelAdmin):
    list_display = ("key", "value", "updated_at")
