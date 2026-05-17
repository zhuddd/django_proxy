from __future__ import annotations

import asyncio
import os
import threading
import time
from dataclasses import dataclass
from urllib.parse import urlparse

import httpx
from django.conf import settings
from django.db import close_old_connections, transaction
from django.utils import timezone as dj_timezone
from loguru import logger

from gateway.models import NodeStatus, ProxyRoute, SystemConfig
from gateway.proxy.connectivity import format_upstream_error
from gateway.proxy.router import build_target_url, normalize_path
from gateway.proxy.ssl_config import get_proxy_ssl_verify

_checker_thread: threading.Thread | None = None
_client: httpx.AsyncClient | None = None
_proxy_env_warned = False
_running = False
_run_lock = threading.Lock()

# Latest results for API (avoid hammering DB on every probe)
_status_cache: dict[int, dict] = {}


@dataclass
class ProbeResult:
    route_id: int
    is_online: bool
    error_message: str
    status_code: int | None
    response_time_ms: float | None


def _orm_thread(fn, *args, **kwargs):
    close_old_connections()
    try:
        return fn(*args, **kwargs)
    finally:
        close_old_connections()


def get_cached_status(route_id: int) -> dict | None:
    return _status_cache.get(route_id)


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


def _concurrency_limit() -> int:
    return int(getattr(settings, "HEALTH_CHECK_CONCURRENCY", 5))


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
        _client = httpx.AsyncClient(
            follow_redirects=True,
            trust_env=False,
            proxy=None,
            verify=get_proxy_ssl_verify(),
            limits=httpx.Limits(
                max_connections=_concurrency_limit() + 2,
                max_keepalive_connections=_concurrency_limit(),
            ),
        )
    return _client


def _health_probe_urls(route: ProxyRoute) -> list[str]:
    prefix = route.effective_prefix
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
    return {
        "User-Agent": (
            "Mozilla/5.0 (compatible; DjangoProxyGateway-HealthCheck/1.0)"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Connection": "keep-alive",
        "Host": parsed.netloc,
    }


async def _probe_one(
    client: httpx.AsyncClient,
    url: str,
    timeout: float,
) -> tuple[bool, str, int | None, float | None]:
    headers = _browser_like_headers(url)
    start = time.perf_counter()
    try:
        resp = await client.get(url, timeout=timeout, headers=headers)
        elapsed_ms = (time.perf_counter() - start) * 1000
        if resp.status_code < 500:
            return True, "", resp.status_code, elapsed_ms
        return False, f"HTTP {resp.status_code}", resp.status_code, None
    except httpx.HTTPError as exc:
        return False, format_upstream_error(url, exc), None, None


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
    return False, last_error or "unreachable", last_status, None


async def _probe_route_limited(
    sem: asyncio.Semaphore,
    client: httpx.AsyncClient,
    route: ProxyRoute,
    timeout: float,
) -> ProbeResult:
    async with sem:
        is_online, error_message, status_code, response_time_ms = await _probe_upstream(
            client, route, timeout
        )
        if not is_online:
            logger.debug(
                "Health offline prefix={} target={} err={}",
                route.prefix,
                route.target_url,
                error_message,
            )
        return ProbeResult(
            route_id=route.id,
            is_online=is_online,
            error_message=error_message,
            status_code=status_code,
            response_time_ms=response_time_ms,
        )


def _bulk_persist(results: list[ProbeResult]) -> None:
    """Single transaction — avoid SQLite lock storm from per-route writes."""
    global _status_cache
    now = dj_timezone.now()
    with transaction.atomic():
        for item in results:
            NodeStatus.objects.update_or_create(
                route_id=item.route_id,
                defaults={
                    "is_online": item.is_online,
                    "response_time_ms": item.response_time_ms,
                    "last_check": now,
                    "error_message": item.error_message,
                },
            )
            _status_cache[item.route_id] = {
                "is_online": item.is_online,
                "response_time_ms": item.response_time_ms,
                "last_check": now,
                "error_message": item.error_message,
            }


async def run_health_checks() -> None:
    """
    Probe upstreams concurrently (bounded), then one DB transaction.
    Does not block the main ASGI event loop when called from background thread.
    """
    global _running
    with _run_lock:
        if _running:
            logger.debug("Health check already running, skip")
            return
        _running = True

    try:
        routes: list[ProxyRoute] = await asyncio.to_thread(
            _orm_thread,
            lambda: list(ProxyRoute.objects.filter(enabled=True)),
        )
        if not routes:
            return

        timeout = await _get_timeout()
        client = await _get_client()
        sem = asyncio.Semaphore(_concurrency_limit())

        outcomes = await asyncio.gather(
            *(_probe_route_limited(sem, client, r, timeout) for r in routes),
            return_exceptions=True,
        )

        results: list[ProbeResult] = []
        for route, outcome in zip(routes, outcomes):
            if isinstance(outcome, Exception):
                results.append(
                    ProbeResult(
                        route_id=route.id,
                        is_online=False,
                        error_message=str(outcome),
                        status_code=None,
                        response_time_ms=None,
                    )
                )
            else:
                results.append(outcome)

        await asyncio.to_thread(_orm_thread, _bulk_persist, results)
        logger.debug("Health check finished for {} route(s)", len(results))
    finally:
        with _run_lock:
            _running = False


async def health_checker_loop() -> None:
    while True:
        try:
            await run_health_checks()
        except Exception:
            logger.exception("Health check cycle failed")
        await asyncio.sleep(await _get_interval())


def _checker_thread_main() -> None:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(health_checker_loop())
    finally:
        loop.run_until_complete(_close_client())
        loop.close()


def start_health_checker() -> None:
    """Daemon thread with its own event loop — never blocks Daphne."""
    global _checker_thread

    if os.environ.get("HEALTH_CHECK_ENABLED", "true").lower() in ("0", "false", "no"):
        logger.info("In-process health checker disabled (HEALTH_CHECK_ENABLED=false)")
        return

    if _checker_thread and _checker_thread.is_alive():
        return

    _checker_thread = threading.Thread(
        target=_checker_thread_main,
        daemon=True,
        name="health-checker",
    )
    _checker_thread.start()
    logger.info("Health checker started (background thread)")


def schedule_health_checks() -> bool:
    """
    Fire-and-forget manual check — does NOT block HTTP workers.
    Returns False if a run is already in progress.
    """
    def _run_once():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(run_health_checks())
        finally:
            loop.run_until_complete(_close_client())
            loop.close()

    with _run_lock:
        if _running:
            return False

    threading.Thread(target=_run_once, daemon=True, name="health-check-once").start()
    return True


async def _close_client() -> None:
    global _client
    if _client and not _client.is_closed:
        await _client.aclose()
        _client = None
