import uuid

from django.conf import settings
from django.db import models
from django.utils.text import slugify


class Store(models.Model):
    """An optional storefront layered on top of a regular seller account.

    Listings stay untouched: if a seller has an active store, their listings
    present as the store; deleting the store demotes them back to a personal
    seller with no data migration.
    """

    owner = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="store"
    )
    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=140, unique=True, editable=False)
    tagline = models.CharField(max_length=160, blank=True)
    description = models.TextField(blank=True)
    logo = models.ImageField(upload_to="stores/logos/%Y/", null=True, blank=True)
    banner = models.ImageField(upload_to="stores/banners/%Y/", null=True, blank=True)
    whatsapp = models.CharField(max_length=20, blank=True)
    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        # Slug is set once and stays stable if the store is later renamed.
        if not self.slug:
            base = slugify(self.name)[:120] or "store"
            slug = base
            while Store.objects.filter(slug=slug).exists():
                slug = f"{base}-{uuid.uuid4().hex[:6]}"
            self.slug = slug
        super().save(*args, **kwargs)
