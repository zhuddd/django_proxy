"""Upstream TLS verification settings for httpx clients."""

from __future__ import annotations

import os

from django.conf import settings
from loguru import logger


def get_proxy_ssl_verify() -> bool | str:
    """
    httpx ``verify`` argument.

    - True (default): verify server certificate and hostname
    - False: disable verification (e.g. HTTPS by IP without matching SAN)
    - str: path to a custom CA bundle file
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
    verify = get_proxy_ssl_verify()
    if verify is False:
        logger.warning(
            "PROXY_SSL_VERIFY=false: upstream HTTPS certificates are NOT verified "
            "(use only for dev / trusted private networks)"
        )
    elif isinstance(verify, str):
        logger.info("Upstream TLS using custom CA bundle: {}", verify)
