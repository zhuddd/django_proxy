"""
透明反向代理网关的默认 Django 配置项。

在宿主项目 ``settings.py`` 中调用 ``inject_settings(globals())``，
仅填充尚未定义的配置键，不覆盖项目已有设置。

不负责 ``DATABASES``、前端静态资源或 SPA 路由。
"""

from __future__ import annotations

# 网关默认配置（键名与 settings 属性一致）
DEFAULTS: dict[str, object] = {
    "PROXY_FORWARD_MODE": "stream",
    "PROXY_CONNECT_TIMEOUT": 10.0,
    "PROXY_READ_TIMEOUT": 300.0,
    "PROXY_SSL_VERIFY": True,
    "PROXY_SSL_CA_BUNDLE": "",
    "HTTPX_MAX_CONNECTIONS": 200,
    "HTTPX_MAX_KEEPALIVE": 50,
    "HEALTH_CHECK_ENABLED": True,
    "HEALTH_CHECK_INTERVAL": 30,
    "HEALTH_CHECK_CONCURRENCY": 5,
    "HEALTH_CHECK_TIMEOUT": 5,
    "LOG_RETENTION_DAYS": 7,
    "PROXY_WEBSOCKET_ENABLED": True,
    "PROXY_EXTRA_SKIP_PREFIXES": (),
}


def inject_settings(settings_globals: dict) -> None:
    """
    将 ``DEFAULTS`` 合并进宿主 settings 模块的全局命名空间。

    Args:
        settings_globals: 通常为 ``inject_settings(globals())`` 中的 ``globals()``。
    """
    for key, value in DEFAULTS.items():
        settings_globals.setdefault(key, value)
