"""系统配置 API 的输入/输出 Schema。"""

from datetime import datetime

from ninja import Schema


class ConfigOut(Schema):
    """系统配置项输出。"""

    key: str
    value: str
    description: str
    updated_at: datetime


class ConfigIn(Schema):
    """更新系统配置项的输入。"""

    value: str
    description: str | None = None
