from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from .models import School, User
from .otp import normalize_phone


class SchoolSerializer(serializers.ModelSerializer):
    """Flat shape: town/state/coords are denormalized here for clients even
    though they live on the Town/State tables."""

    city = serializers.CharField(source="town.name", read_only=True)
    state = serializers.CharField(source="town.state.name", read_only=True)
    latitude = serializers.DecimalField(
        source="town.latitude", max_digits=9, decimal_places=6, read_only=True
    )
    longitude = serializers.DecimalField(
        source="town.longitude", max_digits=9, decimal_places=6, read_only=True
    )

    class Meta:
        model = School
        fields = [
            "id",
            "name",
            "slug",
            "institution_type",
            "city",
            "state",
            "latitude",
            "longitude",
        ]


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    phone = serializers.CharField()
    school = serializers.SlugRelatedField(
        slug_field="slug", queryset=School.objects.all(), required=False, allow_null=True
    )

    class Meta:
        model = User
        fields = ["email", "password", "first_name", "last_name", "phone", "school"]

    def validate_phone(self, value):
        phone = normalize_phone(value)
        if phone is None:
            raise serializers.ValidationError(
                "Enter a valid Nigerian WhatsApp number, e.g. 0803 123 4567."
            )
        if User.objects.filter(phone=phone).exists():
            raise serializers.ValidationError(
                "An account already exists with this WhatsApp number."
            )
        return phone

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class UserSerializer(serializers.ModelSerializer):
    school = SchoolSerializer(read_only=True)
    school_slug = serializers.SlugRelatedField(
        slug_field="slug",
        queryset=School.objects.all(),
        source="school",
        write_only=True,
        required=False,
        allow_null=True,
    )

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "phone",
            "school",
            "school_slug",
            "latitude",
            "longitude",
            "is_email_verified",
            "is_phone_verified",
            "date_joined",
        ]
        read_only_fields = ["email", "is_email_verified", "is_phone_verified", "date_joined"]

    def validate_phone(self, value):
        phone = normalize_phone(value)
        if phone is None:
            raise serializers.ValidationError(
                "Enter a valid Nigerian WhatsApp number, e.g. 0803 123 4567."
            )
        if User.objects.exclude(pk=self.instance.pk).filter(phone=phone).exists():
            raise serializers.ValidationError(
                "An account already exists with this WhatsApp number."
            )
        return phone

    def update(self, instance, validated_data):
        # Changing the number invalidates the previous verification.
        new_phone = validated_data.get("phone")
        if new_phone and new_phone != instance.phone:
            instance.is_phone_verified = False
        return super().update(instance, validated_data)


class PublicSellerSerializer(serializers.ModelSerializer):
    """What other users see about a seller — no contact or precise location."""

    school = serializers.CharField(source="school.name", default=None, read_only=True)

    class Meta:
        model = User
        fields = ["id", "first_name", "last_name", "school", "date_joined"]
