from __future__ import annotations

import time
from collections.abc import AsyncIterator

import httpx
from asgiref.sync import sync_to_async
from django.http import HttpResponseNotFound, StreamingHttpResponse
from loguru import logger

from gateway.proxy.client import get_http_client
from gateway.proxy.headers import BODYLESS_METHODS, filter_hop_by_hop, prepare_outgoing_headers
from gateway.proxy.router import build_target_from_request, match_route
from gateway.proxy.route_cache import get_routes
from gateway.services.log_broadcaster import broadcast_log, persist_proxy_log


def get_client_ip(request) -> str | None:
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def _headers_to_dict(headers) -> dict[str, str]:
    return {k: v for k, v in headers.items()}


async def _read_request_body(request) -> bytes:
    """Read body once for upstream (safe for ASGI + WSGI)."""
    if request.method in BODYLESS_METHODS:
        return b""
    return await sync_to_async(lambda: bytes(request.body or b""))()


def _bad_gateway_response(
    message: str,
    *,
    method: str,
    path: str,
    target_url: str,
    client_ip: str | None,
    route_id: int | None,
    start: float,
) -> StreamingHttpResponse:
    async def err_iter() -> AsyncIterator[bytes]:
        yield message.encode("utf-8", errors="replace")
        latency_ms = (time.perf_counter() - start) * 1000
        await persist_proxy_log(
            method=method,
            path=path,
            target_url=target_url,
            status_code=502,
            request_headers={},
            response_headers={},
            latency_ms=latency_ms,
            client_ip=client_ip,
            route_id=route_id,
            error_message=message,
        )
        await broadcast_log(
            {
                "method": method,
                "path": path,
                "target_url": target_url,
                "status_code": 502,
                "latency_ms": round(latency_ms, 2),
                "client_ip": client_ip,
                "error_message": message,
            }
        )

    return StreamingHttpResponse(
        streaming_content=err_iter(),
        status=502,
        reason="Bad Gateway",
        content_type="text/plain; charset=utf-8",
    )


async def _forward_httpx_stream(
    *,
    request,
    route,
    target_url: str,
    method: str,
    client_ip: str | None,
    start: float,
) -> StreamingHttpResponse:
    """Primary path: httpx send(stream=True) + StreamingHttpResponse."""
    body = await _read_request_body(request)
    outgoing_headers = prepare_outgoing_headers(request, target_url)
    cookies = dict(request.COOKIES)
    client = get_http_client()

    try:
        req = client.build_request(
            method=method,
            url=target_url,
            headers=outgoing_headers,
            cookies=cookies,
            content=body if body else None,
        )
        upstream = await client.send(req, stream=True)
    except httpx.RequestError as exc:
        logger.error("Upstream unreachable {}: {}", target_url, exc)
        return _bad_gateway_response(
            f"Bad Gateway: {exc}",
            method=method,
            path=request.path_info,
            target_url=target_url,
            client_ip=client_ip,
            route_id=route.id,
            start=start,
        )

    status_code = upstream.status_code
    raw_headers = dict(upstream.headers)
    django_headers = filter_hop_by_hop(raw_headers)

    logger.debug(
        "Proxy {} {} -> {} status={}",
        method,
        request.path_info,
        target_url,
        status_code,
    )

    async def body_iterator() -> AsyncIterator[bytes]:
        error_message = ""
        try:
            async for chunk in upstream.aiter_bytes():
                yield chunk
        except Exception as exc:
            error_message = str(exc)
            logger.exception("Stream error from {}", target_url)
            yield f"Bad Gateway: {exc}".encode()
        finally:
            await upstream.aclose()
            latency_ms = (time.perf_counter() - start) * 1000
            await persist_proxy_log(
                method=method,
                path=request.path_info,
                target_url=target_url,
                status_code=status_code,
                request_headers=_headers_to_dict(request.headers),
                response_headers=filter_hop_by_hop(raw_headers),
                latency_ms=latency_ms,
                client_ip=client_ip,
                route_id=route.id,
                error_message=error_message,
            )
            await broadcast_log(
                {
                    "method": method,
                    "path": request.path_info,
                    "target_url": target_url,
                    "status_code": status_code,
                    "latency_ms": round(latency_ms, 2),
                    "client_ip": client_ip,
                    "error_message": error_message,
                }
            )

    response = StreamingHttpResponse(
        streaming_content=body_iterator(),
        status=status_code,
        reason=getattr(upstream, "reason_phrase", None),
    )
    for key, value in django_headers.items():
        response[key] = value
    return response


async def _forward_buffered_fallback(
    *,
    request,
    route,
    target_url: str,
    method: str,
    client_ip: str | None,
    start: float,
) -> StreamingHttpResponse:
    """
    Fallback when streaming path fails at connect time only.
    Still uses httpx; buffers response (not for huge downloads).
    """
    body = await _read_request_body(request)
    outgoing_headers = prepare_outgoing_headers(request, target_url)
    cookies = dict(request.COOKIES)
    client = get_http_client()

    try:
        resp = await client.request(
            method=method,
            url=target_url,
            headers=outgoing_headers,
            cookies=cookies,
            content=body if body else None,
        )
    except httpx.RequestError as exc:
        logger.error("Buffered upstream failed {}: {}", target_url, exc)
        return _bad_gateway_response(
            f"Bad Gateway: {exc}",
            method=method,
            path=request.path_info,
            target_url=target_url,
            client_ip=client_ip,
            route_id=route.id,
            start=start,
        )

    status_code = resp.status_code
    raw_headers = dict(resp.headers)
    content = resp.content

    async def body_iterator() -> AsyncIterator[bytes]:
        yield content
        latency_ms = (time.perf_counter() - start) * 1000
        await persist_proxy_log(
            method=method,
            path=request.path_info,
            target_url=target_url,
            status_code=status_code,
            request_headers=_headers_to_dict(request.headers),
            response_headers=filter_hop_by_hop(raw_headers),
            latency_ms=latency_ms,
            client_ip=client_ip,
            route_id=route.id,
            error_message="",
        )
        await broadcast_log(
            {
                "method": method,
                "path": request.path_info,
                "target_url": target_url,
                "status_code": status_code,
                "latency_ms": round(latency_ms, 2),
                "client_ip": client_ip,
                "error_message": "",
            }
        )

    response = StreamingHttpResponse(
        streaming_content=body_iterator(),
        status=status_code,
        reason=getattr(resp, "reason_phrase", None),
    )
    for key, value in filter_hop_by_hop(raw_headers).items():
        response[key] = value
    return response


async def forward_request(request) -> StreamingHttpResponse | HttpResponseNotFound:
    """
    Transparent async reverse proxy with prefix forwarding.
    Default: httpx stream; optional buffered fallback via PROXY_FORWARD_MODE.
    """
    from django.conf import settings

    routes = await get_routes()
    matched = match_route(request.path_info, routes)

    if not matched:
        return HttpResponseNotFound("No proxy route matched")

    route = matched.route
    target_url = build_target_from_request(route, request.get_full_path())
    method = request.method
    client_ip = get_client_ip(request)
    start = time.perf_counter()

    mode = getattr(settings, "PROXY_FORWARD_MODE", "stream").lower()
    if mode == "buffered":
        return await _forward_buffered_fallback(
            request=request,
            route=route,
            target_url=target_url,
            method=method,
            client_ip=client_ip,
            start=start,
        )

    return await _forward_httpx_stream(
        request=request,
        route=route,
        target_url=target_url,
        method=method,
        client_ip=client_ip,
        start=start,
    )
