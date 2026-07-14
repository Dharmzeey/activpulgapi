from rest_framework import permissions


class HasContactPhoneForWrites(permissions.BasePermission):
    """Sellers must have a contact (WhatsApp) number before publishing.

    Anonymous requests pass through so IsAuthenticated* returns 401, not this.
    """

    message = "Add your WhatsApp number to your profile before posting."

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        if not request.user.is_authenticated:
            return True
        return bool(request.user.phone)
