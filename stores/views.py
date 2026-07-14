from django.db.models import Count, Q
from rest_framework import generics, permissions, status
from rest_framework.response import Response

from accounts.permissions import PhoneVerifiedForWrites
from listings.models import Listing

from .models import Store
from .serializers import PublicStoreSerializer, StoreSerializer


def public_store_queryset():
    return Store.objects.filter(is_active=True).annotate(
        active_listings=Count(
            "owner__listings",
            filter=Q(owner__listings__status=Listing.Status.ACTIVE),
        )
    )


class StoreListView(generics.ListAPIView):
    """Public directory of active storefronts."""

    serializer_class = PublicStoreSerializer
    permission_classes = [permissions.AllowAny]
    search_fields = ["name", "tagline"]

    def get_queryset(self):
        return public_store_queryset().order_by("-created_at")


class StoreDetailView(generics.RetrieveAPIView):
    serializer_class = PublicStoreSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = "slug"

    def get_queryset(self):
        return public_store_queryset().select_related("owner__school")


class MyStoreView(generics.RetrieveUpdateDestroyAPIView):
    """The owner's storefront: fetch, edit, or close (delete) it."""

    serializer_class = StoreSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return generics.get_object_or_404(Store, owner=self.request.user)


class StoreCreateView(generics.CreateAPIView):
    serializer_class = StoreSerializer
    permission_classes = [permissions.IsAuthenticated, PhoneVerifiedForWrites]

    def create(self, request, *args, **kwargs):
        if Store.objects.filter(owner=request.user).exists():
            return Response(
                {"detail": "You already have a storefront."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)
