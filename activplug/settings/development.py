"""Development settings: permissive, codes printed to the console."""

from .base import *  # noqa: F401,F403
from .base import env

DEBUG = env("DEBUG", default=True)

ALLOWED_HOSTS = ALLOWED_HOSTS or ["localhost", "127.0.0.1"]  # noqa: F405
