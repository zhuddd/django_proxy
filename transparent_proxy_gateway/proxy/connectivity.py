"""上游连接失败时的可读错误信息与排查提示。"""

from __future__ import annotations

from urllib.parse import urlparse


def format_upstream_error(target_url: str, exc: Exception) -> str:
    """将 httpx 异常转为带上下文的说明（TCP/超时/TLS 等）。"""
    raw = str(exc).strip() or exc.__class__.__name__
    parsed = urlparse(target_url)
    host = parsed.hostname or ""
    port = parsed.port or (443 if parsed.scheme == "https" else 80)

    hints: list[str] = []

    if "connection attempts failed" in raw.lower() or "connect" in raw.lower():
        hints.append(
            f"Cannot open TCP connection to {host}:{port} "
            "(upstream down, wrong address, or firewall)"
        )
        if host and not host.startswith("127.") and host != "localhost":
            hints.append(
                f"If gateway and upstream share a host, bind upstream to 0.0.0.0:{port} "
                f"or use http://127.0.0.1:{port}"
            )
        hints.append(f"Test locally: curl -v {target_url}")

    if "timed out" in raw.lower() or "timeout" in raw.lower():
        hints.append(
            "Connection timed out; check network or increase "
            "HEALTH_CHECK_TIMEOUT / PROXY_CONNECT_TIMEOUT"
        )

    ssl_markers = (
        "certificate verify failed",
        "ssl",
        "tls",
        "certificate_verify_failed",
        "hostname doesn't match",
        "ip address mismatch",
    )
    if any(m in raw.lower() for m in ssl_markers):
        hints.append(
            "HTTPS certificate does not match the target host "
            "(common when using an IP URL but cert is issued for a domain)"
        )
        hints.append(
            "Use the domain on the certificate as upstream URL, or set "
            "PROXY_SSL_VERIFY=false on a trusted network (less secure)"
        )
        if host and host.replace(".", "").isdigit():
            hints.append(
                f"Target is IP {host}; ensure cert SAN/CN includes the IP or use a domain name"
            )

    if not hints:
        return raw

    return f"{raw} -- {'; '.join(hints)}"