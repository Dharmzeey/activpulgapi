from django.db.models import Count, F, Q
from rest_framework import generics, permissions, status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import PhoneVerifiedForWrites

from .filters import ListingFilter
from .geo import with_distance
from .models import Category, Favorite, Listing
from .permissions import IsSellerOrReadOnly
from .serializers import (
    CategorySerializer,
    ListingDetailSerializer,
    ListingListSerializer,
)


def parse_point(request):
    """Read lat/lng from query params (or fall back to the user's profile).

    Returns (lat, lng) or None. Raises ValidationError on malformed values.
    """
    lat, lng = request.query_params.get("lat"), request.query_params.get("lng")
    if lat is not None and lng is not None:
        try:
            lat, lng = float(lat), float(lng)
        except ValueError:
            raise ValidationError({"detail": "lat and lng must be numbers."})
        if not (-90 <= lat <= 90 and -180 <= lng <= 180):
            raise ValidationError({"detail": "lat/lng out of range."})
        return lat, lng
    user = request.user
    if user.is_authenticated and user.latitude is not None:
        return float(user.latitude), float(user.longitude)
    return None


class CategoryListView(generics.ListAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = None
    filter_backends = []


class ListingListCreateView(generics.ListCreateAPIView):
    """Browse (public, proximity-ranked) and create (authenticated) listings.

    Query params: q, category, school, condition, min_price, max_price,
    lat, lng, radius_km, ordering (distance|price|-price|-created_at).
    """

    permission_classes = [permissions.IsAuthenticatedOrReadOnly, PhoneVerifiedForWrites]
    filterset_class = ListingFilter
    search_fields = ["title", "description"]
    # No `ordering` default here: OrderingFilter would apply it after
    # get_queryset and silently override the distance ranking. With no
    # ?ordering= param the distance order_by (or Meta.ordering) stands.
    ordering_fields = ["price", "created_at"]

    def get_serializer_class(self):
        return ListingDetailSerializer if self.request.method == "POST" else ListingListSerializer

    def get_queryset(self):
        qs = (
            Listing.objects.filter(status=Listing.Status.ACTIVE)
            .select_related("category", "school")
            .prefetch_related("images")
        )
        point = parse_point(self.request)
        if point is None:
            return qs
        qs = with_distance(qs, *point)
        radius = self.request.query_params.get("radius_km")
        if radius is not None:
            try:
                radius = float(radius)
            except ValueError:
                raise ValidationError({"detail": "radius_km must be a number."})
            qs = qs.filter(distance_km__lte=radius)
        if self.request.query_params.get("ordering") in (None, "", "distance"):
            qs = qs.order_by(F("distance_km").asc(nulls_last=True), "-created_at")
        return qs


class ListingDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ListingDetailSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsSellerOrReadOnly]
    lookup_field = "slug"

    def get_queryset(self):
        return Listing.objects.select_related(
            "category", "school", "seller__school", "seller__store"
        ).prefetch_related("images")

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.seller_id != getattr(request.user, "id", None):
            Listing.objects.filter(pk=instance.pk).update(views_count=F("views_count") + 1)
            instance.views_count += 1
        point = parse_point(request)
        if point is not None and instance.latitude is not None:
            instance.distance_km = with_distance(
                Listing.objects.filter(pk=instance.pk), *point
            ).values_list("distance_km", flat=True)[0]
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class MyListingsView(generics.ListAPIView):
    """The authenticated seller's own listings, any status."""

    serializer_class = ListingListSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_class = ListingFilter
    ordering = ["-created_at"]

    def get_queryset(self):
        return (
            Listing.objects.filter(seller=self.request.user)
            .select_related("category", "school")
            .prefetch_related("images")
        )


class FavoriteToggleView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, slug):
        listing = generics.get_object_or_404(Listing, slug=slug, status=Listing.Status.ACTIVE)
        favorite, created = Favorite.objects.get_or_create(user=request.user, listing=listing)
        if not created:
            favorite.delete()
        return Response({"favorited": created}, status=status.HTTP_200_OK)


class FavoriteListView(generics.ListAPIView):
    serializer_class = ListingListSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = []

    def get_queryset(self):
        return (
            Listing.objects.filter(favorited_by__user=self.request.user)
            .select_related("category", "school")
            .prefetch_related("images")
        )


class RecommendationsView(generics.ListAPIView):
    """Proximity-first recommendations, boosted by the user's category affinity.

    Nearby active listings (not the user's own), ranked by distance; listings
    in categories the user has favorited are surfaced first within each band.
    Anonymous users get recent popular listings.
    """

    serializer_class = ListingListSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = []

    def get_queryset(self):
        qs = (
            Listing.objects.filter(status=Listing.Status.ACTIVE)
            .select_related("category", "school")
            .prefetch_related("images")
        )
        user = self.request.user
        if user.is_authenticated:
            qs = qs.exclude(seller=user)
        point = parse_point(self.request)

        if user.is_authenticated:
            liked_categories = Favorite.objects.filter(user=user).values_list(
                "listing__category_id", flat=True
            )
            qs = qs.annotate(
                affinity=Count("category", filter=Q(category_id__in=list(liked_categories)))
            )
            if point is not None:
                qs = with_distance(qs, *point)
                # Same-school items first, then close-by, then liked categories.
                return qs.order_by(
                    F("distance_km").asc(nulls_last=True), "-affinity", "-created_at"
                )
            return qs.order_by("-affinity", "-created_at")

        if point is not None:
            qs = with_distance(qs, *point)
            return qs.order_by(F("distance_km").asc(nulls_last=True), "-created_at")
        return qs.order_by("-views_count", "-created_at")
