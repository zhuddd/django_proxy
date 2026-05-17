from ninja import Schema


class StatsOverviewOut(Schema):
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
    bucket: str
    total: int
    success: int
    error: int
    avg_latency_ms: float


class StatsTimelineOut(Schema):
    hours: int
    granularity: str
    points: list[TimelinePointOut]


class StatusBucketOut(Schema):
    label: str
    count: int


class MethodBucketOut(Schema):
    method: str
    count: int


class TopPathOut(Schema):
    path: str
    count: int
    avg_latency_ms: float
