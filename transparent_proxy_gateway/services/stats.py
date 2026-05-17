"""代理访问日志统计：概览、时间线、状态/方法分布与热门路径（跨数据库 ORM）。"""

from __future__ import annotations

from datetime import timedelta

from django.conf import settings
from django.db.models import Avg, Count, Max, Q
from django.db.models.functions import TruncDate, TruncHour, TruncMinute
from django.utils import timezone

from transparent_proxy_gateway.orm_compat import supports_filtered_aggregates
from transparent_proxy_gateway.models import ProxyLog


def _since(hours: int):
    """将小时数限制在合理范围并返回查询起始时间。"""
    hours = max(1, min(hours, 24 * 30))
    return timezone.now() - timedelta(hours=hours)


def _pick_granularity(hours: int) -> str:
    """根据时间窗口选择聚合粒度（分钟/小时/天）。"""
    if hours <= 6:
        return "minute"
    if hours <= 72:
        return "hour"
    return "day"


def _trunc_tzinfo():
    """USE_TZ 时传入当前时区，避免 MySQL/PostgreSQL 时间桶偏移。"""
    if not settings.USE_TZ:
        return None
    return timezone.get_current_timezone()


def _trunc_fn(granularity: str):
    """返回对应粒度的 Django ORM 截断函数（带时区）。"""
    tz = _trunc_tzinfo()
    if granularity == "minute":
        return TruncMinute("created_at", tzinfo=tz)
    if granularity == "hour":
        return TruncHour("created_at", tzinfo=tz)
    return TruncDate("created_at", tzinfo=tz)


def _timeline_points_python(qs, granularity: str) -> list[dict]:
    """无 filter= 条件聚合时的 Python 侧分桶（兼容 MySQL 5.7）。"""
    from collections import defaultdict

    buckets: dict = defaultdict(
        lambda: {"total": 0, "success": 0, "error": 0, "latency_sum": 0.0, "latency_n": 0}
    )
    for row in qs.only("created_at", "status_code", "error_message", "latency_ms").iterator(
        chunk_size=2000
    ):
        dt = row.created_at
        if granularity == "minute":
            key = dt.replace(second=0, microsecond=0)
        elif granularity == "hour":
            key = dt.replace(minute=0, second=0, microsecond=0)
        else:
            key = dt.date()
        b = buckets[key]
        b["total"] += 1
        if row.status_code is not None and row.status_code < 400:
            b["success"] += 1
        elif row.status_code is not None and row.status_code >= 400:
            b["error"] += 1
        elif row.error_message:
            b["error"] += 1
        if row.latency_ms:
            b["latency_sum"] += row.latency_ms
            b["latency_n"] += 1

    points = []
    for key in sorted(buckets.keys()):
        b = buckets[key]
        label = key.isoformat() if hasattr(key, "isoformat") else str(key)
        avg = (b["latency_sum"] / b["latency_n"]) if b["latency_n"] else 0.0
        points.append(
            {
                "bucket": label,
                "total": b["total"],
                "success": b["success"],
                "error": b["error"],
                "avg_latency_ms": round(avg, 2),
            }
        )
    return points


def get_overview(hours: int = 24) -> dict:
    """汇总指定时间窗口内的请求量、错误分类与延迟指标。"""
    since = _since(hours)
    qs = ProxyLog.objects.filter(created_at__gte=since)
    total = qs.count()
    success = qs.filter(status_code__lt=400).count()
    client_error = qs.filter(status_code__gte=400, status_code__lt=500).count()
    server_error = qs.filter(status_code__gte=500).count()
    other_error = qs.filter(Q(status_code__isnull=True) | Q(error_message__gt="")).count()
    agg = qs.aggregate(avg_lat=Avg("latency_ms"), max_lat=Max("latency_ms"))
    avg_latency = float(agg["avg_lat"] or 0)
    max_latency = float(agg["max_lat"] or 0)
    success_rate = round((success / total * 100) if total else 100.0, 2)
    return {
        "hours": hours,
        "total": total,
        "success": success,
        "client_error": client_error,
        "server_error": server_error,
        "other_error": other_error,
        "avg_latency_ms": round(avg_latency, 2),
        "max_latency_ms": round(max_latency, 2),
        "success_rate": success_rate,
    }


def get_timeline(hours: int = 24) -> dict:
    """按时间桶聚合请求量、成功/失败数与平均延迟。"""
    since = _since(hours)
    granularity = _pick_granularity(hours)
    trunc = _trunc_fn(granularity)
    base_qs = ProxyLog.objects.filter(created_at__gte=since)

    if not supports_filtered_aggregates():
        points = _timeline_points_python(base_qs, granularity)
        return {"hours": hours, "granularity": granularity, "points": points}

    rows = (
        base_qs.annotate(bucket=trunc)
        .values("bucket")
        .annotate(
            total=Count("id"),
            success=Count("id", filter=Q(status_code__lt=400)),
            error=Count(
                "id",
                filter=Q(status_code__gte=400)
                | Q(status_code__isnull=True)
                | Q(error_message__gt=""),
            ),
            avg_latency_ms=Avg("latency_ms"),
        )
        .order_by("bucket")
    )
    points = []
    for row in rows:
        b = row["bucket"]
        label = b.isoformat() if hasattr(b, "isoformat") else str(b)
        points.append(
            {
                "bucket": label,
                "total": row["total"],
                "success": row["success"],
                "error": row["error"],
                "avg_latency_ms": round(float(row["avg_latency_ms"] or 0), 2),
            }
        )
    return {"hours": hours, "granularity": granularity, "points": points}


def get_status_distribution(hours: int = 24) -> list[dict]:
    """按 2xx/3xx/4xx/5xx/其他 统计状态码分布。"""
    since = _since(hours)
    qs = ProxyLog.objects.filter(created_at__gte=since)
    buckets = [
        ("2xx", Q(status_code__gte=200, status_code__lt=300)),
        ("3xx", Q(status_code__gte=300, status_code__lt=400)),
        ("4xx", Q(status_code__gte=400, status_code__lt=500)),
        ("5xx", Q(status_code__gte=500)),
        ("其他", Q(status_code__isnull=True) | Q(error_message__gt="")),
    ]
    result = []
    for label, q in buckets:
        count = qs.filter(q).count()
        if count:
            result.append({"label": label, "count": count})
    return result


def get_method_distribution(hours: int = 24) -> list[dict]:
    """按 HTTP 方法统计请求次数。"""
    since = _since(hours)
    rows = (
        ProxyLog.objects.filter(created_at__gte=since)
        .values("method")
        .annotate(count=Count("id"))
        .order_by("-count")
    )
    return [{"method": r["method"] or "?", "count": r["count"]} for r in rows]


def get_top_paths(hours: int = 24, limit: int = 10) -> list[dict]:
    """返回访问次数最多的路径及平均延迟。"""
    since = _since(hours)
    limit = max(1, min(limit, 50))
    rows = (
        ProxyLog.objects.filter(created_at__gte=since)
        .values("path")
        .annotate(count=Count("id"), avg_latency_ms=Avg("latency_ms"))
        .order_by("-count")[:limit]
    )
    return [
        {
            "path": r["path"],
            "count": r["count"],
            "avg_latency_ms": round(float(r["avg_latency_ms"] or 0), 2),
        }
        for r in rows
    ]
