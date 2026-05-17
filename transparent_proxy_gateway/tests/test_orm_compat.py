"""ORM 兼容辅助测试（使用宿主项目 settings.DATABASES）。"""

from django.test import SimpleTestCase

from transparent_proxy_gateway.orm_compat import supports_filtered_aggregates


class SupportsFilteredAggregatesTests(SimpleTestCase):
    def test_sqlite_supports(self):
        with self.settings(
            DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}
        ):
            from django.db import connection

            connection.ensure_connection()
            self.assertTrue(supports_filtered_aggregates())
