"""上游 HTTPS TLS 校验配置（供 httpx ``verify`` 参数使用）。"""

from __future__ import annotations

import os

from django.conf import settings
from loguru import logger


def get_proxy_ssl_verify() -> bool | str:
    """
    返回 httpx 的 ``verify`` 参数值。

    - True（默认）：校验服务端证书与主机名
    - False：关闭校验（如用 IP 访问但证书无匹配 SAN）
    - str：自定义 CA 证书包路径
    """
    ca_bundle = (
        os.environ.get("PROXY_SSL_CA_BUNDLE", "").strip()
        or getattr(settings, "PROXY_SSL_CA_BUNDLE", "") or ""
    )
    if ca_bundle:
        return ca_bundle

    raw = os.environ.get(
        "PROXY_SSL_VERIFY",
        str(getattr(settings, "PROXY_SSL_VERIFY", True)),
    ).strip().lower()
    if raw in ("0", "false", "no", "off"):
        return False
    return True


def log_ssl_verify_mode() -> None:
    """在客户端创建时记录当前 TLS 校验模式（含风险提示）。"""
    verify = get_proxy_ssl_verify()
    if verify is False:
        logger.warning(
            "PROXY_SSL_VERIFY=false: upstream HTTPS certificates are NOT verified "
            "(use only for dev / trusted private networks)"
        )
    elif isinstance(verify, str):
        logger.info("Upstream TLS using custom CA bundle: {}", verify)
