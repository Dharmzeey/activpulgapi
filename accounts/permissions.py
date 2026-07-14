from django.conf import settings
from rest_framework import permissions


class PhoneVerifiedForWrites(permissions.BasePermission):
    """Blocks writes for users who haven't verified their WhatsApp number.

    Only enforced when REQUIRE_PHONE_VERIFICATION is on (production).
    Anonymous requests pass through so IsAuthenticated* returns 401, not this.
    """

    message = "Verify your WhatsApp number to continue."

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        if not settings.REQUIRE_PHONE_VERIFICATION:
            return True
        if not request.user.is_authenticated:
            return True
        return request.user.is_phone_verified
