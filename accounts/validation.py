"""Signup hygiene: phone normalization, throwaway-email detection, and
canonical email identity (defeats plus/dot aliasing on Gmail)."""

import re
from functools import lru_cache
from pathlib import Path

NIGERIAN_PHONE = re.compile(r"^\+234[789][01]\d{8}$")

DISPOSABLE_DOMAINS_FILE = Path(__file__).parent / "data" / "disposable_email_domains.txt"

# Providers where dots in the local part are ignored and + starts a tag.
GMAIL_DOMAINS = {"gmail.com", "googlemail.com"}


def normalize_phone(raw: str) -> str | None:
    """Accepts 0803..., 234803... or +234803... and returns +234803... (E.164)."""
    digits = re.sub(r"[^\d+]", "", raw or "")
    if digits.startswith("0") and len(digits) == 11:
        digits = "+234" + digits[1:]
    elif digits.startswith("234"):
        digits = "+" + digits
    return digits if NIGERIAN_PHONE.fullmatch(digits) else None


@lru_cache(maxsize=1)
def disposable_domains() -> frozenset[str]:
    lines = DISPOSABLE_DOMAINS_FILE.read_text(encoding="utf-8").splitlines()
    return frozenset(
        line.strip().lower() for line in lines if line.strip() and not line.startswith("#")
    )


def is_disposable_email(email: str) -> bool:
    domain = email.rsplit("@", 1)[-1].lower()
    # Match the domain and any parent domain (a.b.mailinator.com).
    parts = domain.split(".")
    candidates = {".".join(parts[i:]) for i in range(len(parts) - 1)}
    return not candidates.isdisjoint(disposable_domains())


def canonical_email(email: str) -> str:
    """One identity per mailbox: lowercase, strip +tags, collapse Gmail dots."""
    local, _, domain = email.lower().rpartition("@")
    local = local.split("+", 1)[0]
    if domain in GMAIL_DOMAINS:
        local = local.replace(".", "")
        domain = "gmail.com"
    return f"{local}@{domain}"
