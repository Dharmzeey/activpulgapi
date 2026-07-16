"""Server-side verification of Google Sign-In ID tokens.

Uses Google's tokeninfo endpoint, which validates the token's signature and
expiry; we additionally pin the audience to our OAuth client id and require
a verified email. Fine for auth-time volumes; swap for local JWKS
verification if login traffic ever makes the extra HTTP call matter.
"""

import json
import logging
import urllib.parse
import urllib.request

from django.conf import settings

logger = logging.getLogger(__name__)

TOKENINFO_URL = "https://oauth2.googleapis.com/tokeninfo"
VALID_ISSUERS = {"https://accounts.google.com", "accounts.google.com"}


class GoogleAuthError(Exception):
    pass


def verify_id_token(credential: str) -> dict:
    """Returns the token claims (email, given_name, family_name, sub, ...)."""
    if not settings.GOOGLE_CLIENT_ID:
        raise GoogleAuthError("Google sign-in is not configured on the server.")
    if not credential:
        raise GoogleAuthError("Missing Google credential.")
    url = f"{TOKENINFO_URL}?{urllib.parse.urlencode({'id_token': credential})}"
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            claims = json.loads(response.read())
    except urllib.error.HTTPError as exc:
        logger.info("Google tokeninfo rejected a credential: %s", exc.code)
        raise GoogleAuthError("Invalid Google credential.") from exc
    except Exception as exc:
        logger.error("Google tokeninfo unreachable: %s", exc)
        raise GoogleAuthError("Could not reach Google. Try again.") from exc

    if claims.get("aud") != settings.GOOGLE_CLIENT_ID:
        raise GoogleAuthError("Credential was issued for a different app.")
    if claims.get("iss") not in VALID_ISSUERS:
        raise GoogleAuthError("Invalid Google credential.")
    if claims.get("email_verified") not in ("true", True):
        raise GoogleAuthError("Google account email is not verified.")
    return claims
