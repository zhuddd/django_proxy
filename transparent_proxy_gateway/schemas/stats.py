"""日志统计 API 输出 Schema。"""

from ninja import Schema


class StatsOverviewOut(Schema):
    """时间窗口内的访问概览。"""

    hours: int
    total: int
    success: int
    client_error: int
    server_error: int
    other_error: int
    avg_latency_ms: float
    max_latency_ms: float
    success_rate: float


class TimelinePointOut(Schema):
    """时间线上的单个聚合点。"""

    bucket: str
    total: int
    success: int
    error: int
    avg_latency_ms: float


class StatsTimelineOut(Schema):
    """按时间桶聚合的时间线数据。"""

    hours: int
    granularity: str
    points: list[TimelinePointOut]


class StatusBucketOut(Schema):
    """状态码分布桶。"""

    label: str
    count: int


class MethodBucketOut(Schema):
    """HTTP 方法分布桶。"""

    method: str
    count: int


class TopPathOut(Schema):
    """热门访问路径条目。"""

    path: str
    count: int
    avg_latency_ms: float
