from django.core.management.base import BaseCommand
from django.utils.text import slugify

from accounts.models import School
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

SCHOOLS = [
    ("Carleton University", "Ottawa", "Ontario", "Canada", 45.3876, -75.6960),
    ("University of Ottawa", "Ottawa", "Ontario", "Canada", 45.4231, -75.6831),
]


class Command(BaseCommand):
    help = "Seed default categories and starter schools (idempotent)."

    def handle(self, *args, **options):
        for name in CATEGORIES:
            Category.objects.get_or_create(slug=slugify(name), defaults={"name": name})
        for name, city, state, country, lat, lng in SCHOOLS:
            School.objects.get_or_create(
                slug=slugify(name),
                defaults={
                    "name": name,
                    "city": city,
                    "state": state,
                    "country": country,
                    "latitude": lat,
                    "longitude": lng,
                },
            )
        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded. Categories: {Category.objects.count()}, Schools: {School.objects.count()}"
            )
        )
