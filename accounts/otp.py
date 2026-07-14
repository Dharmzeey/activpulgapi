"""Create and check hashed one-time codes for WhatsApp verification."""

import re
import secrets
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.hashers import check_password, make_password
from django.utils import timezone

from .models import PhoneOTP

NIGERIAN_PHONE = re.compile(r"^\+234[789][01]\d{8}$")


class OTPError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(message)


def normalize_phone(raw: str) -> str | None:
    """Accepts 0803..., 234803... or +234803... and returns +234803... (E.164)."""
    digits = re.sub(r"[^\d+]", "", raw or "")
    if digits.startswith("0") and len(digits) == 11:
        digits = "+234" + digits[1:]
    elif digits.startswith("234"):
        digits = "+" + digits
    return digits if NIGERIAN_PHONE.fullmatch(digits) else None


def issue_code(user) -> str:
    """Create (or replace) the user's pending code and return the plaintext."""
    existing = PhoneOTP.objects.filter(user=user).first()
    if existing and (timezone.now() - existing.created_at) < timedelta(
        seconds=settings.OTP_RESEND_COOLDOWN_SECONDS
    ):
        raise OTPError("Please wait a minute before requesting another code.")
    code = f"{secrets.randbelow(1_000_000):06d}"
    PhoneOTP.objects.update_or_create(
        user=user, defaults={"code_hash": make_password(code), "attempts": 0}
    )
    return code


def confirm_code(user, code: str) -> None:
    """Raises OTPError unless the code is valid; marks the phone verified."""
    otp = PhoneOTP.objects.filter(user=user).first()
    if otp is None:
        raise OTPError("No pending code. Request a new one.")
    if (timezone.now() - otp.created_at) > timedelta(minutes=settings.OTP_TTL_MINUTES):
        otp.delete()
        raise OTPError("That code has expired. Request a new one.")
    if otp.attempts >= settings.OTP_MAX_ATTEMPTS:
        otp.delete()
        raise OTPError("Too many wrong attempts. Request a new code.")
    if not check_password(str(code or "").strip(), otp.code_hash):
        otp.attempts += 1
        otp.save(update_fields=["attempts"])
        raise OTPError("Incorrect code. Check WhatsApp and try again.")
    otp.delete()
    user.is_phone_verified = True
    user.save(update_fields=["is_phone_verified"])
