"""Development settings: permissive, codes printed to the console."""

from .base import *  # noqa: F401,F403
from .base import env

DEBUG = env("DEBUG", default=True)

ALLOWED_HOSTS = ALLOWED_HOSTS or ["localhost", "127.0.0.1"]  # noqa: F405

# Verification codes are printed to the runserver console instead of sent.
WHATSAPP_BACKEND = "console"

# Let developers post listings without completing phone verification.
REQUIRE_PHONE_VERIFICATION = False
