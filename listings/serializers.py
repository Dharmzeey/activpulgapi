from rest_framework import serializers

from accounts.serializers import PublicSellerSerializer

from .models import Category, Favorite, Listing, ListingImage

MAX_IMAGES_PER_LISTING = 6


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "slug"]


class ListingImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ListingImage
        fields = ["id", "image", "position"]


class ListingListSerializer(serializers.ModelSerializer):
    """Compact shape for grids and search results."""

    category = serializers.CharField(source="category.slug", read_only=True)
    school = serializers.CharField(source="school.name", default=None, read_only=True)
    cover_image = serializers.SerializerMethodField()
    distance_km = serializers.FloatField(read_only=True, default=None)

    class Meta:
        model = Listing
        fields = [
            "id",
            "title",
            "slug",
            "price",
            "condition",
            "status",
            "category",
            "school",
            "location_name",
            "cover_image",
            "distance_km",
            "created_at",
        ]

    def get_cover_image(self, obj):
        first = next(iter(obj.images.all()), None)
        if first is None:
            return None
        request = self.context.get("request")
        url = first.image.url
        return request.build_absolute_uri(url) if request else url


class ListingDetailSerializer(serializers.ModelSerializer):
    seller = PublicSellerSerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    category_slug = serializers.SlugRelatedField(
        slug_field="slug", queryset=Category.objects.all(), source="category", write_only=True
    )
    images = ListingImageSerializer(many=True, read_only=True)
    uploaded_images = serializers.ListField(
        child=serializers.ImageField(), write_only=True, required=False, max_length=MAX_IMAGES_PER_LISTING
    )
    school = serializers.CharField(source="school.name", default=None, read_only=True)
    distance_km = serializers.FloatField(read_only=True, default=None)
    is_favorited = serializers.SerializerMethodField()

    class Meta:
        model = Listing
        fields = [
            "id",
            "title",
            "slug",
            "description",
            "price",
            "condition",
            "status",
            "category",
            "category_slug",
            "seller",
            "school",
            "latitude",
            "longitude",
            "location_name",
            "images",
            "uploaded_images",
            "views_count",
            "is_favorited",
            "distance_km",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["slug", "views_count", "created_at", "updated_at"]

    def get_is_favorited(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False
        return Favorite.objects.filter(user=request.user, listing=obj).exists()

    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("Price must be greater than zero.")
        return value

    def create(self, validated_data):
        images = validated_data.pop("uploaded_images", [])
        user = self.context["request"].user
        # Location is captured automatically from the seller's profile unless
        # the seller supplies explicit coordinates for this listing.
        validated_data.setdefault("school", user.school)
        if validated_data.get("latitude") is None:
            validated_data["latitude"] = user.latitude
            validated_data["longitude"] = user.longitude
        listing = Listing.objects.create(seller=user, **validated_data)
        self._save_images(listing, images, start=0)
        return listing

    def update(self, instance, validated_data):
        images = validated_data.pop("uploaded_images", None)
        listing = super().update(instance, validated_data)
        if images is not None:
            start = listing.images.count()
            if start + len(images) > MAX_IMAGES_PER_LISTING:
                raise serializers.ValidationError(
                    {"uploaded_images": f"A listing can have at most {MAX_IMAGES_PER_LISTING} images."}
                )
            self._save_images(listing, images, start=start)
        return listing

    def _save_images(self, listing, images, start):
        ListingImage.objects.bulk_create(
            ListingImage(listing=listing, image=image, position=start + i)
            for i, image in enumerate(images)
        )
