from __future__ import annotations

from datetime import timedelta

from django.db.models import Avg, Count, Max, Q
from django.db.models.functions import TruncDate, TruncHour, TruncMinute
from django.utils import timezone

from gateway.models import ProxyLog


def _since(hours: int):
    hours = max(1, min(hours, 24 * 30))
    return timezone.now() - timedelta(hours=hours)


def _pick_granularity(hours: int) -> str:
    if hours <= 6:
        return "minute"
    if hours <= 72:
        return "hour"
    return "day"


def _trunc_fn(granularity: str):
    if granularity == "minute":
        return TruncMinute("created_at")
    if granularity == "hour":
        return TruncHour("created_at")
    return TruncDate("created_at")


def get_overview(hours: int = 24) -> dict:
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
    since = _since(hours)
    granularity = _pick_granularity(hours)
    trunc = _trunc_fn(granularity)
    rows = (
        ProxyLog.objects.filter(created_at__gte=since)
        .annotate(bucket=trunc)
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
    since = _since(hours)
    rows = (
        ProxyLog.objects.filter(created_at__gte=since)
        .values("method")
        .annotate(count=Count("id"))
        .order_by("-count")
    )
    return [{"method": r["method"] or "?", "count": r["count"]} for r in rows]


def get_top_paths(hours: int = 24, limit: int = 10) -> list[dict]:
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
