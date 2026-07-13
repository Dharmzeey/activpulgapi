from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import School, State, Town, User


@admin.register(State)
class StateAdmin(admin.ModelAdmin):
    list_display = ["name"]
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Town)
class TownAdmin(admin.ModelAdmin):
    list_display = ["name", "state", "latitude", "longitude"]
    list_filter = ["state"]
    search_fields = ["name"]


@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    list_display = ["name", "institution_type", "town"]
    list_filter = ["institution_type", "town__state"]
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ["name", "town__name"]
    autocomplete_fields = ["town"]


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
