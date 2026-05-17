"""SQLite tuning for concurrent proxy logs + health checker writes."""

from django.db.backends.signals import connection_created


def _enable_sqlite_wal(sender, connection, **kwargs):
    if connection.vendor != "sqlite":
        return
    with connection.cursor() as cursor:
        cursor.execute("PRAGMA journal_mode=WAL;")
        cursor.execute("PRAGMA synchronous=NORMAL;")
        cursor.execute("PRAGMA busy_timeout=5000;")


def setup_sqlite():
    connection_created.connect(_enable_sqlite_wal)
