"""
Django settings for transparent reverse proxy gateway.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

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

INSTALLED_APPS = [
    "daphne",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "channels",
    "gateway",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "gateway.middleware.proxy_gate.ProxyGateMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
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
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "data" / "db.sqlite3",
    }
}

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

# Proxy
# PROXY_FORWARD_MODE: stream (default, streaming) | buffered (fallback, loads full response)
PROXY_FORWARD_MODE = os.environ.get("PROXY_FORWARD_MODE", "stream")
PROXY_CONNECT_TIMEOUT = float(os.environ.get("PROXY_CONNECT_TIMEOUT", "10"))
PROXY_READ_TIMEOUT = float(os.environ.get("PROXY_READ_TIMEOUT", "300"))
HTTPX_MAX_CONNECTIONS = int(os.environ.get("HTTPX_MAX_CONNECTIONS", "200"))
HTTPX_MAX_KEEPALIVE = int(os.environ.get("HTTPX_MAX_KEEPALIVE", "50"))

# Health check
HEALTH_CHECK_INTERVAL = int(os.environ.get("HEALTH_CHECK_INTERVAL", "30"))
HEALTH_CHECK_TIMEOUT = int(os.environ.get("HEALTH_CHECK_TIMEOUT", "5"))
LOG_RETENTION_DAYS = int(os.environ.get("LOG_RETENTION_DAYS", "7"))

JWT_EXPIRE_SECONDS = int(os.environ.get("JWT_EXPIRE_SECONDS", "86400"))

# Channels
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

# Loguru: intercept Django/stdlib logs + redirect print() -> logger.info
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
