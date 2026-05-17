"""ORM 运行时兼容判断（只读当前连接，不配置数据库）。"""

from __future__ import annotations


def supports_filtered_aggregates() -> bool:
    """
    当前默认库是否支持 ORM 条件聚合 ``Count(..., filter=Q(...))``。

    MySQL 需 8.0+；不满足时 ``services.stats`` 对时间线统计使用 Python 分桶。
    """
    from django.db import connection

    if connection.vendor == "mysql":
        try:
            version = connection.mysql_version  # type: ignore[attr-defined]
            return version >= (8, 0, 0)
        except Exception:
            return False
    return connection.vendor in ("postgresql", "sqlite", "oracle")
