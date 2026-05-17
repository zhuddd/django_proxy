from django.test import RequestFactory, SimpleTestCase

from gateway.models import ProxyRoute
from gateway.proxy.response_rewrite import (
    REDIRECT_STATUS_CODES,
    is_redirect_status,
    rewrite_location,
)


class RewriteLocationTests(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.route = ProxyRoute(
            prefix="/test",
            target_url="http://127.0.0.1:8888",
            enabled=True,
        )

    def _request(self, path="/test/admin/"):
        return self.factory.get(path, HTTP_HOST="localhost:8000")

    def test_absolute_path(self):
        req = self._request()
        out = rewrite_location("/test/login/", req, self.route)
        self.assertEqual(out, "http://localhost:8000/test/login/")

    def test_relative_path(self):
        req = self._request("/test/admin/users/")
        out = rewrite_location("edit", req, self.route)
        self.assertEqual(out, "http://localhost:8000/test/admin/users/edit")

    def test_upstream_absolute_loopback_alias(self):
        req = self._request()
        out = rewrite_location(
            "http://127.0.0.1:8888/test/dashboard/",
            req,
            self.route,
            target_url="http://192.168.1.2:8888/test/dashboard/",
        )
        self.assertEqual(out, "http://localhost:8000/test/dashboard/")

    def test_upstream_path_prefix_without_host_match(self):
        req = self._request()
        out = rewrite_location("http://other:8888/test/page", req, self.route)
        self.assertEqual(out, "http://localhost:8000/test/page")

    def test_external_redirect_unchanged(self):
        req = self._request()
        out = rewrite_location("https://example.com/offsite", req, self.route)
        self.assertEqual(out, "https://example.com/offsite")

    def test_protocol_relative(self):
        req = self._request()
        out = rewrite_location("//127.0.0.1:8888/test/ok", req, self.route)
        self.assertEqual(out, "http://localhost:8000/test/ok")

    def test_redirect_status_codes(self):
        self.assertTrue(is_redirect_status(302))
        self.assertIn(308, REDIRECT_STATUS_CODES)
