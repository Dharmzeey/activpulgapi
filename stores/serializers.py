from rest_framework import serializers

from .models import Store


class StoreSerializer(serializers.ModelSerializer):
    """Full shape for the owner managing their own storefront."""

    class Meta:
        model = Store
        fields = [
            "id",
            "name",
            "slug",
            "tagline",
            "description",
            "logo",
            "banner",
            "whatsapp",
            "is_active",
            "is_verified",
            "created_at",
        ]
        read_only_fields = ["slug", "is_verified", "created_at"]


class PublicStoreSerializer(serializers.ModelSerializer):
    """What buyers see. No contact details beyond what the store chose to share."""

    school = serializers.CharField(source="owner.school.name", default=None, read_only=True)
    active_listings = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = Store
        fields = [
            "name",
            "slug",
            "tagline",
            "description",
            "logo",
            "banner",
            "whatsapp",
            "is_verified",
            "school",
            "active_listings",
            "created_at",
        ]


class StoreBadgeSerializer(serializers.ModelSerializer):
    """Minimal shape embedded in listing detail responses."""

    class Meta:
        model = Store
        fields = ["name", "slug", "tagline", "logo", "is_verified"]
