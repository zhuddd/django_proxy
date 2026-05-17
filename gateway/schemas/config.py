from datetime import datetime

from ninja import Schema


class ConfigOut(Schema):
    key: str
    value: str
    description: str
    updated_at: datetime


class ConfigIn(Schema):
    value: str
    description: str | None = None
