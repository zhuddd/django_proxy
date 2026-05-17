from django.test import SimpleTestCase

from gateway.models import ProxyRoute
from gateway.proxy.router import match_route, prefix_matches


def _route(prefix: str, target: str = "http://127.0.0.1:9000") -> ProxyRoute:
    return ProxyRoute(prefix=prefix, target_url=target, enabled=True)


class PrefixMatchTests(SimpleTestCase):
    def test_literal_prefix(self):
        self.assertTrue(prefix_matches("/account/login", "/account"))
        self.assertFalse(prefix_matches("/accounts", "/account"))

    def test_robot_wildcard(self):
        self.assertTrue(prefix_matches("/robot/foo", "/robot/*"))
        self.assertTrue(prefix_matches("/robot", "/robot/*"))
        self.assertFalse(prefix_matches("/robotics", "/robot/*"))

    def test_global_wildcard(self):
        self.assertTrue(prefix_matches("/anything", "/*"))


class MatchRouteTests(SimpleTestCase):
    def test_longest_literal_wins(self):
        routes = [_route("/account"), _route("/*", "http://127.0.0.1:1")]
        m = match_route("/account/login", routes)
        self.assertEqual(m.route.prefix, "/account")

    def test_scoped_wildcard_over_global(self):
        routes = [
            _route("/*", "http://127.0.0.1:1"),
            _route("/robot/*", "http://127.0.0.1:2"),
        ]
        m = match_route("/robot/api", routes)
        self.assertEqual(m.route.prefix, "/robot/*")

    def test_literal_beats_wildcard_same_scope(self):
        routes = [
            _route("/robot/*", "http://127.0.0.1:1"),
            _route("/robot", "http://127.0.0.1:2"),
        ]
        m = match_route("/robot/x", routes)
        self.assertEqual(m.route.prefix, "/robot")
