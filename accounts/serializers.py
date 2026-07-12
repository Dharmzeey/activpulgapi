from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from .models import School, User


class SchoolSerializer(serializers.ModelSerializer):
    class Meta:
        model = School
        fields = [
            "id",
            "name",
            "slug",
            "institution_type",
            "city",
            "state",
            "country",
            "latitude",
            "longitude",
        ]


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    school = serializers.SlugRelatedField(
        slug_field="slug", queryset=School.objects.all(), required=False, allow_null=True
    )

    class Meta:
        model = User
        fields = ["email", "password", "first_name", "last_name", "phone", "school"]

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
            "date_joined",
        ]
        read_only_fields = ["email", "is_email_verified", "date_joined"]


class PublicSellerSerializer(serializers.ModelSerializer):
    """What other users see about a seller — no contact or precise location."""

    school = serializers.CharField(source="school.name", default=None, read_only=True)

    class Meta:
        model = User
        fields = ["id", "first_name", "last_name", "school", "date_joined"]
