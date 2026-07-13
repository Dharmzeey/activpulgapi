import json
from pathlib import Path

from django.apps import apps
from django.core.management.base import BaseCommand
from django.utils.text import slugify

from accounts.models import School, State, Town
from listings.models import Category

CATEGORIES = [
    "Textbooks & Study Materials",
    "Electronics & Gadgets",
    "Phones & Accessories",
    "Laptops & Computers",
    "Furniture",
    "Home & Kitchen",
    "Clothing & Shoes",
    "Beauty & Personal Care",
    "Sports & Fitness",
    "Bikes & Transport",
    "Food & Snacks",
    "Event Tickets",
    "Services",
    "Other",
]

INSTITUTIONS_FILE = (
    Path(apps.get_app_config("accounts").path) / "data" / "nigeria_institutions.json"
)


class Command(BaseCommand):
    help = (
        "Seed default categories and Nigerian institutions (idempotent). "
        "Extend accounts/data/nigeria_institutions.json to add more schools; "
        "coordinates are city-level and can be refined in the admin."
    )

    def handle(self, *args, **options):
        for name in CATEGORIES:
            Category.objects.get_or_create(slug=slugify(name), defaults={"name": name})

        institutions = json.loads(INSTITUTIONS_FILE.read_text(encoding="utf-8"))
        created = 0
        for row in institutions:
            state, _ = State.objects.get_or_create(
                name=row["state"], defaults={"slug": slugify(row["state"])}
            )
            town, _ = Town.objects.get_or_create(
                name=row["city"],
                state=state,
                defaults={"latitude": row["lat"], "longitude": row["lng"]},
            )
            _, was_created = School.objects.get_or_create(
                slug=slugify(row["name"])[:255],
                defaults={
                    "name": row["name"],
                    "institution_type": row["type"],
                    "town": town,
                },
            )
            created += was_created

        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded. Categories: {Category.objects.count()}, "
                f"States: {State.objects.count()}, Towns: {Town.objects.count()}, "
                f"Schools: {School.objects.count()} ({created} new)"
            )
        )
