from django.test import TestCase

from gateway.models import ProxyRoute
from gateway.proxy.route_rules import (
    normalize_route_prefix,
    validate_no_wildcard_conflict,
    validate_wildcard_scope_clean,
    validate_wildcard_uniqueness,
)


class RouteRulesTests(TestCase):
    def test_normalize_wildcard(self):
        self.assertEqual(normalize_route_prefix("robot/*"), "/robot/*")
        self.assertEqual(normalize_route_prefix("/*"), "/*")

    def test_duplicate_global_wildcard(self):
        ProxyRoute.objects.create(prefix="/*", target_url="http://a")
        with self.assertRaises(ValueError):
            validate_wildcard_uniqueness("/*")

    def test_duplicate_robot_wildcard(self):
        ProxyRoute.objects.create(prefix="/robot/*", target_url="http://a")
        with self.assertRaises(ValueError):
            validate_wildcard_uniqueness("/robot/*")

    def test_literal_blocked_by_scoped_wildcard(self):
        ProxyRoute.objects.create(prefix="/robot/*", target_url="http://a")
        with self.assertRaises(ValueError):
            validate_no_wildcard_conflict("/robot/api")

    def test_literal_allowed_with_global_wildcard(self):
        ProxyRoute.objects.create(prefix="/*", target_url="http://a")
        validate_no_wildcard_conflict("/account")

    def test_wildcard_blocked_by_existing_literals(self):
        ProxyRoute.objects.create(prefix="/robot", target_url="http://a")
        with self.assertRaises(ValueError):
            validate_wildcard_scope_clean("/robot/*")
