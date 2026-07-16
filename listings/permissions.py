from rest_framework import permissions


class IsSellerOrReadOnly(permissions.BasePermission):
    """Anyone can read; only the listing's seller can modify it."""

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.seller_id == request.user.id
