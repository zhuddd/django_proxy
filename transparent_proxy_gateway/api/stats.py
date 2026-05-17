"""代理日志统计 REST API（概览、时间线、分布与热门路径）。"""

from ninja import Router, Query

from transparent_proxy_gateway.schemas.stats import (
    MethodBucketOut,
    StatsOverviewOut,
    StatsTimelineOut,
    StatusBucketOut,
    TopPathOut,
)
from transparent_proxy_gateway.services import stats as stats_service

router = Router()


@router.get("/overview", response=StatsOverviewOut)
def overview(request, hours: int = Query(24, ge=1, le=720)):
    """指定时间窗口内的访问概览指标。"""
    return stats_service.get_overview(hours)


@router.get("/timeline", response=StatsTimelineOut)
def timeline(request, hours: int = Query(24, ge=1, le=720)):
    """按时间桶聚合的请求量与延迟时间线。"""
    return stats_service.get_timeline(hours)


@router.get("/status", response=list[StatusBucketOut])
def status_distribution(request, hours: int = Query(24, ge=1, le=720)):
    """HTTP 状态码分布。"""
    return stats_service.get_status_distribution(hours)


@router.get("/methods", response=list[MethodBucketOut])
def method_distribution(request, hours: int = Query(24, ge=1, le=720)):
    """HTTP 方法分布。"""
    return stats_service.get_method_distribution(hours)


@router.get("/top-paths", response=list[TopPathOut])
def top_paths(
    request,
    hours: int = Query(24, ge=1, le=720),
    limit: int = Query(10, ge=1, le=50),
):
    """访问次数最多的路径排行。"""
    return stats_service.get_top_paths(hours, limit)
