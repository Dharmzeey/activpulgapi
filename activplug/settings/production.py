"""Production settings: strict transport security, real WhatsApp delivery."""

from .base import *  # noqa: F401,F403
from .base import env

DEBUG = False

# Fail fast if deploy-critical values are missing.
if not env("ALLOWED_HOSTS"):
    raise RuntimeError("ALLOWED_HOSTS must be set in production")
if SECRET_KEY.startswith("django-insecure"):  # noqa: F405
    raise RuntimeError("Set a real SECRET_KEY in production")

# Transport security
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

if not env("GOOGLE_CLIENT_ID", default=""):
    raise RuntimeError("GOOGLE_CLIENT_ID must be set in production (Google-only sign-in)")

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": "INFO"},
}
