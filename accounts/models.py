from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.db import models


class State(models.Model):
    """A Nigerian state (or the FCT). Stored once, not repeated per school."""

    name = models.CharField(max_length=60, unique=True)
    slug = models.SlugField(max_length=60, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Town(models.Model):
    """A town/city holding the coordinates shared by every campus in it."""

    name = models.CharField(max_length=120)
    state = models.ForeignKey(State, on_delete=models.CASCADE, related_name="towns")
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(fields=["name", "state"], name="unique_town_per_state")
        ]

    def __str__(self):
        return f"{self.name}, {self.state.name}"


class School(models.Model):
    """A campus. Location lives on its town; the town's coordinates are the
    default location for its users' listings."""

    class InstitutionType(models.TextChoices):
        UNIVERSITY = "university", "University"
        POLYTECHNIC = "polytechnic", "Polytechnic"
        COLLEGE_OF_EDUCATION = "college_of_education", "College of Education"
        COLLEGE_OF_HEALTH = "college_of_health", "College of Health Sciences/Technology"
        TECHNICAL = "technical", "Technical/Vocational College"
        OTHER = "other", "Other institution"

    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(max_length=255, unique=True)
    institution_type = models.CharField(
        max_length=25, choices=InstitutionType.choices, default=InstitutionType.UNIVERSITY
    )
    town = models.ForeignKey(Town, on_delete=models.PROTECT, related_name="schools")

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    @property
    def latitude(self):
        return self.town.latitude

    @property
    def longitude(self):
        return self.town.longitude


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    """Email-login user. Location defaults to the school's coordinates and can
    be refined from the browser's geolocation for better proximity results."""

    username = None
    email = models.EmailField(unique=True)
    # Alias-collapsed identity (plus-tags stripped, gmail dots removed) so one
    # mailbox cannot register many accounts. Maintained in save().
    canonical_email = models.EmailField(unique=True, null=True, editable=False)
    # WhatsApp number in E.164 (+234...). One account per number: this is the
    # anti-bot anchor, verified by OTP before the user can publish.
    phone = models.CharField(max_length=20, unique=True, null=True, blank=True)
    school = models.ForeignKey(
        School, null=True, blank=True, on_delete=models.SET_NULL, related_name="users"
    )
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    is_email_verified = models.BooleanField(default=False)
    is_phone_verified = models.BooleanField(default=False)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return self.email

    def save(self, *args, **kwargs):
        from .validation import canonical_email

        if self.email:
            self.canonical_email = canonical_email(self.email)
        if self.phone == "":
            self.phone = None
        if self.latitude is None and self.school_id:
            self.latitude = self.school.latitude
            self.longitude = self.school.longitude
        super().save(*args, **kwargs)
