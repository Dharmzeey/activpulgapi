from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import School, User


@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    list_display = ["name", "city", "country"]
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ["name", "city"]


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    ordering = ["email"]
    list_display = ["email", "first_name", "last_name", "school", "is_email_verified"]
    list_filter = ["is_staff", "is_email_verified", "school"]
    search_fields = ["email", "first_name", "last_name"]
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Profile", {"fields": ("first_name", "last_name", "phone", "school", "latitude", "longitude")}),
        ("Status", {"fields": ("is_email_verified", "is_active", "is_staff", "is_superuser")}),
        ("Dates", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = ((None, {"fields": ("email", "password1", "password2")}),)
