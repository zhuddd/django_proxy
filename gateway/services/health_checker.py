from __future__ import annotations

import asyncio
import os
import time
from urllib.parse import urlparse

import httpx
from django.conf import settings
from django.db import close_old_connections
from django.utils import timezone as dj_timezone
from loguru import logger

from gateway.models import NodeStatus, ProxyRoute, SystemConfig
from gateway.proxy.router import build_target_url, normalize_path

_checker_thread = None
_client: httpx.AsyncClient | None = None
_proxy_env_warned = False


def _orm_thread(fn, *args, **kwargs):
    close_old_connections()
    try:
        return fn(*args, **kwargs)
    finally:
        close_old_connections()


def _warn_proxy_env_once() -> None:
    global _proxy_env_warned
    if _proxy_env_warned:
        return
    _proxy_env_warned = True
    for key in ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "http_proxy", "https_proxy"):
        val = os.environ.get(key)
        if val:
            logger.warning(
                "Health checker ignores {}={} (direct connect only)",
                key,
                val,
            )


async def _get_interval() -> float:
    try:
        val = await asyncio.to_thread(
            _orm_thread, SystemConfig.get_value, "health_check_interval", "30"
        )
        return float(val)
    except ValueError:
        return float(getattr(settings, "HEALTH_CHECK_INTERVAL", 30))


async def _get_timeout() -> float:
    try:
        val = await asyncio.to_thread(
            _orm_thread, SystemConfig.get_value, "health_check_timeout", "5"
        )
        return float(val)
    except ValueError:
        return float(getattr(settings, "HEALTH_CHECK_TIMEOUT", 5))


async def _get_client() -> httpx.AsyncClient:
    global _client
    _warn_proxy_env_once()
    if _client is None or _client.is_closed:
        # trust_env=False: avoid routing 127.0.0.1 via HTTP_PROXY (returns 502 from gateway)
        _client = httpx.AsyncClient(
            follow_redirects=True,
            trust_env=False,
            proxy=None,
        )
    return _client


def _health_probe_urls(route: ProxyRoute) -> list[str]:
    """
    URLs to try, most relevant first.
    Use registered prefix path (e.g. /test) — same path the proxy actually forwards.
    """
    prefix = normalize_path(route.prefix)
    urls: list[str] = []
    if prefix != "/":
        urls.append(build_target_url(route, prefix, ""))
    urls.append(route.target_url.rstrip("/") + "/")
    seen: set[str] = set()
    ordered: list[str] = []
    for u in urls:
        if u not in seen:
            seen.add(u)
            ordered.append(u)
    return ordered


def _browser_like_headers(url: str) -> dict[str, str]:
    parsed = urlparse(url)
    host = parsed.netloc
    return {
        "User-Agent": (
            "Mozilla/5.0 (compatible; DjangoProxyGateway-HealthCheck/1.0; "
            "+https://github.com/local/proxy-gateway)"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Connection": "keep-alive",
        "Host": host,
    }


async def _probe_one(
    client: httpx.AsyncClient,
    url: str,
    timeout: float,
) -> tuple[bool, str, int | None, float | None]:
    """GET probe — matches browser behaviour."""
    headers = _browser_like_headers(url)
    start = time.perf_counter()
    try:
        resp = await client.get(url, timeout=timeout, headers=headers)
        elapsed_ms = (time.perf_counter() - start) * 1000
        if resp.status_code < 500:
            logger.debug(
                "Health OK {} -> {} ({:.1f}ms) server={}",
                url,
                resp.status_code,
                elapsed_ms,
                resp.headers.get("server", "-"),
            )
            return True, "", resp.status_code, elapsed_ms
        return False, f"HTTP {resp.status_code}", resp.status_code, None
    except httpx.HTTPError as exc:
        return False, str(exc), None, None


async def _probe_upstream(
    client: httpx.AsyncClient,
    route: ProxyRoute,
    timeout: float,
) -> tuple[bool, str, int | None, float | None]:
    last_error = ""
    last_status: int | None = None

    for url in _health_probe_urls(route):
        ok, err, status, elapsed = await _probe_one(client, url, timeout)
        if ok:
            return True, "", status, elapsed
        last_error = err
        last_status = status
        logger.debug("Health probe failed {}: {}", url, err)

    return False, last_error or "unreachable", last_status, None


async def check_route(route: ProxyRoute) -> None:
    timeout = await _get_timeout()
    client = await _get_client()

    is_online, error_message, status_code, response_time_ms = await _probe_upstream(
        client, route, timeout
    )

    if not is_online:
        logger.info(
            "Health check offline: prefix={} target={} status={} err={}",
            route.prefix,
            route.target_url,
            status_code,
            error_message,
        )

    def save_status():
        NodeStatus.objects.update_or_create(
            route_id=route.id,
            defaults={
                "is_online": is_online,
                "response_time_ms": response_time_ms,
                "last_check": dj_timezone.now(),
                "error_message": error_message,
            },
        )

    await asyncio.to_thread(_orm_thread, save_status)


async def run_health_checks() -> None:
    routes = await asyncio.to_thread(
        _orm_thread,
        lambda: list(ProxyRoute.objects.filter(enabled=True)),
    )
    await asyncio.gather(*(check_route(r) for r in routes), return_exceptions=True)


async def health_checker_loop() -> None:
    while True:
        try:
            await run_health_checks()
        except Exception:
            logger.exception("Health check cycle failed")
        await asyncio.sleep(await _get_interval())


def start_health_checker() -> None:
    import threading

    global _checker_thread

    if _checker_thread and _checker_thread.is_alive():
        return

    def _run():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(health_checker_loop())
        finally:
            loop.run_until_complete(_close_client())
            loop.close()

    _checker_thread = threading.Thread(target=_run, daemon=True, name="health-checker")
    _checker_thread.start()
    logger.info("Health checker started")


async def _close_client() -> None:
    global _client
    if _client and not _client.is_closed:
        await _client.aclose()
        _client = None
