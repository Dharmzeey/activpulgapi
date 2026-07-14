"""WhatsApp delivery backends for verification codes.

"console" prints the code (development). "meta" sends an authentication
template through the WhatsApp Cloud API — requires a Meta app with an
approved template (default name: campscrow_verify) that takes the code as
its one body parameter and copy-code button.
"""

import json
import logging
import urllib.request

from django.conf import settings

logger = logging.getLogger(__name__)

GRAPH_URL = "https://graph.facebook.com/v21.0/{phone_number_id}/messages"


class WhatsAppError(Exception):
    pass


def send_verification_code(phone: str, code: str) -> None:
    backend = settings.WHATSAPP_BACKEND
    if backend == "console":
        print(f"[whatsapp:console] verification code for {phone}: {code}", flush=True)
        return
    if backend == "meta":
        _send_via_meta(phone, code)
        return
    raise WhatsAppError(f"Unknown WHATSAPP_BACKEND {backend!r}")


def _send_via_meta(phone: str, code: str) -> None:
    if not settings.WHATSAPP_ACCESS_TOKEN or not settings.WHATSAPP_PHONE_NUMBER_ID:
        raise WhatsAppError("WHATSAPP_ACCESS_TOKEN / WHATSAPP_PHONE_NUMBER_ID not configured")
    payload = {
        "messaging_product": "whatsapp",
        "to": phone.lstrip("+"),
        "type": "template",
        "template": {
            "name": settings.WHATSAPP_TEMPLATE,
            "language": {"code": "en"},
            "components": [
                {"type": "body", "parameters": [{"type": "text", "text": code}]},
                {
                    "type": "button",
                    "sub_type": "url",
                    "index": "0",
                    "parameters": [{"type": "text", "text": code}],
                },
            ],
        },
    }
    request = urllib.request.Request(
        GRAPH_URL.format(phone_number_id=settings.WHATSAPP_PHONE_NUMBER_ID),
        data=json.dumps(payload).encode(),
        headers={
            "Authorization": f"Bearer {settings.WHATSAPP_ACCESS_TOKEN}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            body = json.loads(response.read())
        logger.info("WhatsApp code sent to %s (message id %s)",
                    phone, body.get("messages", [{}])[0].get("id"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode(errors="replace")[:500]
        logger.error("WhatsApp send failed for %s: %s %s", phone, exc.code, detail)
        raise WhatsAppError("Could not send the WhatsApp message.") from exc
    except Exception as exc:
        logger.error("WhatsApp send failed for %s: %s", phone, exc)
        raise WhatsAppError("Could not send the WhatsApp message.") from exc
