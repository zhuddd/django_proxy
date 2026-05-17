from ninja import Router, Query

from gateway.schemas.stats import (
    MethodBucketOut,
    StatsOverviewOut,
    StatsTimelineOut,
    StatusBucketOut,
    TopPathOut,
)
from gateway.services import stats as stats_service

router = Router()


@router.get("/overview", response=StatsOverviewOut)
def overview(request, hours: int = Query(24, ge=1, le=720)):
    return stats_service.get_overview(hours)


@router.get("/timeline", response=StatsTimelineOut)
def timeline(request, hours: int = Query(24, ge=1, le=720)):
    return stats_service.get_timeline(hours)


@router.get("/status", response=list[StatusBucketOut])
def status_distribution(request, hours: int = Query(24, ge=1, le=720)):
    return stats_service.get_status_distribution(hours)


@router.get("/methods", response=list[MethodBucketOut])
def method_distribution(request, hours: int = Query(24, ge=1, le=720)):
    return stats_service.get_method_distribution(hours)


@router.get("/top-paths", response=list[TopPathOut])
def top_paths(
    request,
    hours: int = Query(24, ge=1, le=720),
    limit: int = Query(10, ge=1, le=50),
):
    return stats_service.get_top_paths(hours, limit)
