"""Upstream connectivity diagnostics and user-facing error hints."""

from __future__ import annotations

from urllib.parse import urlparse


def format_upstream_error(target_url: str, exc: Exception) -> str:
    """
    Turn httpx connection errors into actionable messages.
    """
    raw = str(exc).strip() or exc.__class__.__name__
    parsed = urlparse(target_url)
    host = parsed.hostname or ""
    port = parsed.port or (443 if parsed.scheme == "https" else 80)

    hints: list[str] = []

    if "connection attempts failed" in raw.lower() or "connect" in raw.lower():
        hints.append(
            f"无法建立 TCP 连接 {host}:{port}（上游未启动、地址错误、或防火墙拦截）"
        )
        if host and not host.startswith("127.") and host != "localhost":
            hints.append(
                "若网关与上游在同一台机器：请确认上游监听 0.0.0.0 "
                f"（如 runserver 0.0.0.0:{port}），或把上游地址改为 http://127.0.0.1:{port}"
            )
        hints.append(f"在本机测试: curl -v {target_url}")

    if "timed out" in raw.lower() or "timeout" in raw.lower():
        hints.append("连接超时：检查网络是否互通、增大 HEALTH_CHECK_TIMEOUT / PROXY_CONNECT_TIMEOUT")

    ssl_markers = (
        "certificate verify failed",
        "ssl",
        "tls",
        "certIFICATE_VERIFY_FAILED",
        "hostname doesn't match",
        "ip address mismatch",
    )
    if any(m in raw.lower() for m in ssl_markers):
        hints.append(
            "HTTPS 证书与访问地址不匹配（常见：上游填的是 IP，证书只签在域名上）"
        )
        hints.append(
            "建议：上游 URL 改用证书对应的域名；或在可信内网设置环境变量 "
            "PROXY_SSL_VERIFY=false 后重启网关（会降低安全性）"
        )
        if host and host.replace(".", "").isdigit():
            hints.append(
                f"当前目标为 IP {host}，请确认证书 SAN/CN 包含该 IP，或勿用 IP 直连 HTTPS"
            )

    if not hints:
        return raw

    return f"{raw} — {'; '.join(hints)}"
