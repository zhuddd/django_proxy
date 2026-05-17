"""
透明反向代理网关的演示 Django 项目配置。

- ``DATABASES`` 由本项目的 ``django_proxy.database`` 管理
- 前端 SPA / WhiteNoise 由本项目配置，网关包不处理静态资源
- 代理相关默认值由 ``transparent_proxy_gateway.conf`` 注入
"""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# --- 路径与基础安全 ---
BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY",
    "django-insecure-dev-change-me-in-production",
)

DEBUG = os.environ.get("DJANGO_DEBUG", "true").lower() in ("1", "true", "yes")

ALLOWED_HOSTS = [
    h.strip()
    for h in os.environ.get("DJANGO_ALLOWED_HOSTS", "*").split(",")
    if h.strip()
]
# SECURE_REFERRER_POLICY = "none"
# SECURE_CROSS_ORIGIN_OPENER_POLICY = "none"

# --- 已安装应用 ---
INSTALLED_APPS = [
    "daphne",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "channels",
    "transparent_proxy_gateway",
]

# --- 中间件（代理门禁在 CommonMiddleware 之后）---
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "transparent_proxy_gateway.middleware.proxy_gate.ProxyGateMiddleware",
    # "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "django_proxy.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

ASGI_APPLICATION = "django_proxy.asgi.application"
WSGI_APPLICATION = "django_proxy.wsgi.application"

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR /"data"/ 'db.sqlite3',
    }
}

# 健康检查（后台线程，不得阻塞代理转发）
HEALTH_CHECK_ENABLED = os.environ.get("HEALTH_CHECK_ENABLED", "true").lower() in (
    "1",
    "true",
    "yes",
)
HEALTH_CHECK_CONCURRENCY = int(os.environ.get("HEALTH_CHECK_CONCURRENCY", "5"))

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "zh-hans"
TIME_ZONE = "Asia/Shanghai"
USE_I18N = True
USE_TZ = True

# --- 静态文件与前端构建产物 ---
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
_frontend_assets = BASE_DIR / "frontend" / "dist" / "assets"
STATICFILES_DIRS = [_frontend_assets] if _frontend_assets.is_dir() else []
STATICFILES_STORAGE = "whitenoise.storage.CompressedStaticFilesStorage"

WHITENOISE_ROOT = BASE_DIR / "frontend" / "dist"
WHITENOISE_INDEX_FILE = True

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# 注入网关包默认配置（不覆盖下方显式赋值）
from transparent_proxy_gateway.conf import inject_settings  # noqa: E402

inject_settings(globals())

# 演示项目前端静态路径（网关包默认不跳过 /assets/、/static/）
PROXY_EXTRA_SKIP_PREFIXES = (
    "/static/",
    "/assets/",
)

# --- 代理转发（可用环境变量覆盖，参见 .env.example）---
# PROXY_FORWARD_MODE: stream（默认流式）| buffered（整包缓冲回退）
PROXY_FORWARD_MODE = os.environ.get("PROXY_FORWARD_MODE", "stream")
PROXY_CONNECT_TIMEOUT = float(os.environ.get("PROXY_CONNECT_TIMEOUT", "10"))
PROXY_READ_TIMEOUT = float(os.environ.get("PROXY_READ_TIMEOUT", "300"))
# 上游 HTTPS：true | false | CA 证书包路径（PROXY_SSL_CA_BUNDLE）
PROXY_SSL_VERIFY = os.environ.get("PROXY_SSL_VERIFY", "true").lower() not in (
    "0",
    "false",
    "no",
    "off",
)
PROXY_SSL_CA_BUNDLE = os.environ.get("PROXY_SSL_CA_BUNDLE", "").strip()
PROXY_WEBSOCKET_ENABLED = os.environ.get("PROXY_WEBSOCKET_ENABLED", "true").lower() not in (
    "0",
    "false",
    "no",
    "off",
)
HTTPX_MAX_CONNECTIONS = int(os.environ.get("HTTPX_MAX_CONNECTIONS", "200"))
HTTPX_MAX_KEEPALIVE = int(os.environ.get("HTTPX_MAX_KEEPALIVE", "50"))

# --- 健康检查与日志保留 ---
HEALTH_CHECK_INTERVAL = int(os.environ.get("HEALTH_CHECK_INTERVAL", "30"))
HEALTH_CHECK_TIMEOUT = int(os.environ.get("HEALTH_CHECK_TIMEOUT", "5"))
LOG_RETENTION_DAYS = int(os.environ.get("LOG_RETENTION_DAYS", "7"))

# --- Channels（有 REDIS_URL 时用 Redis，否则内存层）---
REDIS_URL = os.environ.get("REDIS_URL", "")

if REDIS_URL:
    CHANNEL_LAYERS = {
        "default": {
            "BACKEND": "channels_redis.core.RedisChannelLayer",
            "CONFIG": {"hosts": [REDIS_URL]},
        }
    }
else:
    CHANNEL_LAYERS = {
        "default": {"BACKEND": "channels.layers.InMemoryChannelLayer"},
    }

CSRF_TRUSTED_ORIGINS = [
    o.strip()
    for o in os.environ.get("CSRF_TRUSTED_ORIGINS", "").split(",")
    if o.strip()
]

# --- Loguru：拦截 Django/stdlib 日志，可选将 print 重定向到 logger ---
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
LOG_TO_FILE = os.environ.get("LOG_TO_FILE", "true").lower() in ("1", "true", "yes")
PATCH_PRINT = os.environ.get("PATCH_PRINT", "true").lower() in ("1", "true", "yes")

from django_proxy.log_config import configure_loguru, get_logging_config  # noqa: E402

configure_loguru(
    base_dir=BASE_DIR,
    log_level=LOG_LEVEL,
    retention_days=LOG_RETENTION_DAYS,
    enable_file=LOG_TO_FILE,
    patch_print=PATCH_PRINT,
)

LOGGING = get_logging_config(LOG_LEVEL)
