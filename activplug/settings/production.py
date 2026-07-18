"""Production settings: strict transport security, real WhatsApp delivery."""

# Transport security
# SECURE_SSL_REDIRECT = True
# SECURE_HSTS_SECONDS = 31536000
# SECURE_HSTS_INCLUDE_SUBDOMAINS = True
# SECURE_HSTS_PRELOAD = True
# SESSION_COOKIE_SECURE = True
# CSRF_COOKIE_SECURE = True
# SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")


# LOGGING = {
#     "version": 1,
#     "disable_existing_loggers": False,
#     "handlers": {"console": {"class": "logging.StreamHandler"}},
#     "root": {"handlers": ["console"], "level": "INFO"},
# }

"""
activplug — production settings.

Usage:
    DJANGO_SETTINGS_MODULE=core.settings.prod gunicorn core.wsgi
"""
from .base import *  # noqa: F401, F403
import os


# Fail fast if deploy-critical values are missing.
if not env("ALLOWED_HOSTS"):
    raise RuntimeError("ALLOWED_HOSTS must be set in production")
if SECRET_KEY.startswith("django-insecure"):  # noqa: F405
    raise RuntimeError("Set a real SECRET_KEY in production")

DEBUG = os.getenv('DEBUG', 'False') == 'True'


# ── Database — PostgreSQL ─────────────────────────────────────────────────────
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME":     os.environ["DB_NAME"],
        "USER":     os.environ["DB_USER"],
        "PASSWORD": os.environ["DB_PASSWORD"],
        "HOST":     os.environ.get("DB_HOST", "localhost"),
        "PORT":     os.environ.get("DB_PORT", "5432"),
        "OPTIONS": {
            "connect_timeout": 10,
        },
    }
}

if not env("GOOGLE_CLIENT_ID", default=""):
    raise RuntimeError("GOOGLE_CLIENT_ID must be set in production (Google-only sign-in)")


# ── Media storage — Backblaze B2 (S3-compatible) ──────────────────────────────
STORAGES = {
    "default": {
        "BACKEND": "storages.backends.s3boto3.S3Boto3Storage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.ManifestStaticFilesStorage",
    },
}


AWS_ACCESS_KEY_ID = os.environ.get('B2_APPLICATION_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('B2_APPLICATION_KEY')
AWS_STORAGE_BUCKET_NAME = os.getenv('B2_BUCKET_NAME')
AWS_S3_REGION_NAME = os.getenv('B2_REALM', 'eu-central-003')
AWS_S3_ENDPOINT_URL = f'https://s3.{AWS_S3_REGION_NAME}.backblazeb2.com'

# AWS_S3_CUSTOM_DOMAIN = "media.dharmzeey.com"
# AWS_LOCATION = "media"
# MEDIA_URL = f"https://{AWS_S3_CUSTOM_DOMAIN}/{AWS_LOCATION}/"


STATIC_URL = '/static/'
STATIC_ROOT = '/var/www/html/staticfiles'
