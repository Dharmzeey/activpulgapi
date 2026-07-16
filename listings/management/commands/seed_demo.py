"""Populate the dev database with diverse, realistic demo data:
one-off sellers, vendors with storefronts, listings with generated photos,
favorites — spread across Nigerian campuses.

Usage:
  manage.py seed_demo           # creates demo data (skips if present)
  manage.py seed_demo --fresh   # wipes previous demo data first

All demo users share the password below and use @demo.activplug.ng emails.
"""

import random
from datetime import timedelta
from io import BytesIO

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.text import slugify
from PIL import Image, ImageDraw

from accounts.models import School, User
from listings.models import Category, Favorite, Listing, ListingImage
from stores.models import Store

PASSWORD = "demo-pass-123"
DOMAIN = "demo.activplug.ng"

random.seed(20260713)

PALETTE = [
    ("#166534", "#f0fdf4"), ("#1e3a8a", "#eff6ff"), ("#7c2d12", "#fff7ed"),
    ("#581c87", "#faf5ff"), ("#134e4a", "#f0fdfa"), ("#7f1d1d", "#fef2f2"),
    ("#3f6212", "#f7fee7"), ("#713f12", "#fefce8"),
]

# (first, last, school slug)
PEOPLE = [
    ("Chinedu", "Okafor", "university-of-lagos"),
    ("Aisha", "Bello", "ahmadu-bello-university"),
    ("Tunde", "Adewale", "university-of-ibadan"),
    ("Ngozi", "Eze", "university-of-nigeria-nsukka"),
    ("Emeka", "Nwosu", "university-of-port-harcourt"),
    ("Fatima", "Abubakar", "bayero-university-kano"),
    ("Yemi", "Ogunleye", "obafemi-awolowo-university"),
    ("Blessing", "Igwe", "yaba-college-of-technology"),
    ("Ibrahim", "Suleiman", "kaduna-polytechnic"),
    ("Funke", "Alabi", "lagos-state-university"),
    ("Osaze", "Edo", "university-of-benin"),
    ("Halima", "Yusuf", "university-of-ilorin"),
    ("Kelechi", "Obi", "federal-university-of-technology-owerri"),
    ("Simisola", "Bakare", "covenant-university"),
    ("Musa", "Garba", "federal-university-of-technology-minna"),
    ("Adaeze", "Okonkwo", "nnamdi-azikiwe-university"),
    ("Segun", "Fashola", "the-polytechnic-ibadan"),
    ("Zainab", "Mohammed", "university-of-abuja"),
]

# Vendors: (person index, store name, tagline, description, whatsapp, verified, category focus, inventory)
VENDORS = [
    (0, "Chi's Gadget Hub", "Original phones, chargers and accessories",
     "UK-used and brand new phones with warranty. Pickup at UNILAG main gate or delivery within Yaba/Akoka.",
     "+2348031234501", True, "phones-accessories", [
        ("iPhone 12 (UK used, 128GB)", 315000, "good", "Clean UK-used iPhone 12, battery health 88%. Comes with cable and case."),
        ("Samsung Galaxy A35", 245000, "new", "Brand new, sealed. 8GB/256GB. One year warranty."),
        ("Oraimo FreePods 4", 21500, "new", "Sealed Oraimo FreePods 4, ANC. Free delivery on campus."),
        ("Anker 20,000mAh Power Bank", 28000, "new", "Original Anker PowerCore. Perfect for exam season blackouts."),
        ("iPhone XR (64GB)", 185000, "good", "Very neat XR, face ID working perfectly. Slight scratch on frame."),
        ("Type-C fast chargers (25W)", 7500, "new", "Original Samsung 25W bricks. Bulk price available."),
    ]),
    (7, "Blessing Thrift Closet", "Okrika grade-A fits for less",
     "Hand-picked grade-A thrift: gowns, jeans, corporate wear. New stock every Friday. Yaba Tech pickup.",
     "+2348052234502", True, "clothing-shoes", [
        ("Grade-A denim jackets", 8500, "good", "Sturdy denim jackets, assorted sizes M-XL."),
        ("Corporate shirts bundle (5pcs)", 12000, "good", "Crisp corporate shirts, ready for IT/SIWES."),
        ("Ladies' summer gowns", 6500, "good", "Flowy gowns, UK sizes 8-14. First grade okrika."),
        ("Nike Air Force 1 (UK 42)", 38000, "like_new", "Barely worn AF1s, no crease. Original."),
        ("Ankara two-piece set", 15000, "new", "Tailored ankara set, size 12. Sewn but never worn."),
    ]),
    (8, "Suleiman Foodstuff Depot", "Beans, garri, rice — student measures",
     "Foodstuff in student-friendly quantities. Free delivery inside Kaduna Poly hostels, Mon-Sat.",
     "+2348063334503", False, "food-snacks", [
        ("Honey beans (paint bucket)", 9500, "new", "Clean oloyin beans, no stones. Paint-bucket measure."),
        ("Ijebu garri (paint bucket)", 4500, "new", "Sharp, sour ijebu garri. Perfect for soaking."),
        ("Golden penny spaghetti (10 packs)", 11000, "new", "Carton price beats shop price. Hostel delivery."),
        ("Chin-chin (1kg tub)", 3500, "new", "Crunchy homemade chin-chin, baked weekly."),
    ]),
    (13, "Simi Beauty Essentials", "Skincare and hair that actually works",
     "Authentic skincare, wigs and hair products. Covenant and Ota axis. DM for bundle deals.",
     "+2348094454504", False, "beauty-personal-care", [
        ("CeraVe foaming cleanser", 18500, "new", "Sealed, original CeraVe 236ml. Batch-checked."),
        ("Bone-straight wig (14 inch)", 85000, "new", "Double-drawn bone straight, 210% density."),
        ("Shea butter (500g, unrefined)", 4000, "new", "Raw shea from Kwara, whipped on request."),
        ("Nivea body lotion set", 12500, "new", "Nivea deep moisture set, sealed."),
    ]),
    (16, "Segun Tech Corner", "Laptops and student tech, tested and trusted",
     "UK-used laptops with 3-month guarantee. Swap deals welcome. Poly Ibadan south gate.",
     "+2348125554505", True, "laptops-computers", [
        ("HP EliteBook 840 G5 (i5, 16GB)", 385000, "good", "UK-used EliteBook, 256GB SSD, backlit keyboard. 3-month guarantee."),
        ("Dell Latitude 7490 (i7)", 450000, "good", "Sturdy Latitude, 16GB RAM, new battery."),
        ("Lenovo ThinkPad T480 (i5)", 340000, "good", "The student workhorse. 8GB/256GB, upgradeable."),
        ("MacBook Air 2017", 420000, "good", "Neat MacBook Air 13-inch, 8GB/128GB, cycle count 210."),
        ("Wireless mouse + pad combo", 6500, "new", "Silent-click wireless mouse with free pad."),
        ("Laptop sleeves (13-15 inch)", 5000, "new", "Padded sleeves, grey or black."),
    ]),
]

# One-off listings: (person index, title, price, category, condition, description)
ONE_OFFS = [
    (1, "GST 111 & 121 textbooks (set)", 4500, "textbooks-study-materials", "good",
     "Complete GST first-year pack, clean copies with no torn pages."),
    (1, "Scientific calculator (Casio fx-991)", 9000, "textbooks-study-materials", "like_new",
     "Used for one semester only. Selling because I got a graphing one."),
    (2, "Reading table and chair", 18000, "furniture", "good",
     "Solid wooden reading table with drawer. Buyer picks up at Agbowo."),
    (2, "Mini gas cooker with cylinder (3kg)", 22000, "home-kitchen", "good", None),
    (3, "Engineering drawing board + tee square", 7500, "textbooks-study-materials", "good",
     "Complete drawing kit for first-year engineering. Slightly used."),
    (4, "Bunk bed mattress (student size)", 15000, "home-kitchen", "good",
     "Mouka foam, 6 inches, very clean. Moving out of hostel."),
    (5, "Hijab set (10 pieces, assorted)", 8000, "clothing-shoes", "new",
     "Brand new chiffon hijabs, assorted colours. Bought excess."),
    (6, "Yamaha acoustic guitar", 65000, "other", "good",
     "F310 acoustic, warm tone, new strings. Case included."),
    (9, "Rechargeable standing fan", 35000, "electronics-gadgets", "like_new",
     "18-inch rechargeable fan, lasts 6+ hours. NEPA-proof your night reading."),
    (10, "GOTV decoder + dish", 14000, "electronics-gadgets", "good",
     "Complete GOTV setup, working perfectly. Moving abroad."),
    (11, "Anatomy atlas (Netter, 7th ed)", 28000, "textbooks-study-materials", "good",
     "Netter's Atlas, some highlights in upper limb section."),
    (12, "Gaming chair", 95000, "furniture", "like_new",
     "Ergonomic gaming chair, barely used. Reason: japa."),
    (14, "Electric kettle (2.2L)", 8500, "home-kitchen", "good", None),
    (15, "Jersey collection (5 original kits)", 40000, "sports-fitness", "good",
     "Original Arsenal, Chelsea and Super Eagles kits. Size M-L."),
    (17, "Big Blue mountain bike", 78000, "bikes-transport", "good",
     "26-inch mountain bike, new brake pads. Great for getting to class."),
    (17, "Ring light with tripod (18 inch)", 26000, "electronics-gadgets", "like_new", None),
]


def make_image(title, size=(800, 600)):
    """Two-tone placeholder photo with the item name."""
    dark, light = random.choice(PALETTE)
    img = Image.new("RGB", size, light)
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, 0, size[0], size[1] // 3], fill=dark)
    draw.ellipse(
        [size[0] * 0.62, size[1] * 0.45, size[0] * 0.95, size[1] * 0.92],
        outline=dark, width=6,
    )
    text = title[:28]
    draw.text((40, size[1] // 3 + 40), text, fill=dark, font_size=40)
    draw.text((40, 40), "activplug demo", fill=light, font_size=24)
    buffer = BytesIO()
    img.save(buffer, format="JPEG", quality=80)
    return ContentFile(
        buffer.getvalue(), name=f"{slugify(title)[:40]}-{random.randint(1000, 9999)}.jpg"
    )


class Command(BaseCommand):
    help = "Seed diverse demo data: users, vendors with stores, listings, favorites."

    def add_arguments(self, parser):
        parser.add_argument("--fresh", action="store_true", help="Delete previous demo data first")

    def handle(self, *args, **options):
        existing = User.objects.filter(email__endswith=f"@{DOMAIN}")
        if existing.exists():
            if not options["fresh"]:
                self.stdout.write("Demo data already present. Use --fresh to recreate.")
                return
            existing.delete()

        jitter = lambda: random.uniform(-0.012, 0.012)
        users = []
        for first, last, school_slug in PEOPLE:
            school = School.objects.filter(slug=school_slug).first()
            user = User.objects.create_user(
                email=f"{first.lower()}.{last.lower()}@{DOMAIN}",
                password=PASSWORD,
                first_name=first,
                last_name=last,
                school=school,
                is_email_verified=True,
            )
            if school:
                user.latitude = float(school.latitude) + jitter()
                user.longitude = float(school.longitude) + jitter()
                user.save(update_fields=["latitude", "longitude"])
            users.append(user)

        def create_listing(user, title, price, category_slug, condition, description):
            category = Category.objects.filter(slug=category_slug).first() or Category.objects.get(slug="other")
            listing = Listing.objects.create(
                seller=user,
                title=title,
                description=description
                or f"{title} in {'excellent' if condition in ('new', 'like_new') else 'solid'} condition. "
                   "Price slightly negotiable. Meet on campus or nearby.",
                price=price,
                condition=condition,
                category=category,
                school=user.school,
                latitude=user.latitude,
                longitude=user.longitude,
                location_name=user.school.town.name if user.school else "",
                views_count=random.randint(3, 220),
            )
            for position in range(random.randint(1, 3)):
                ListingImage.objects.create(
                    listing=listing,
                    image=make_image(title),
                    position=position,
                )
            # stagger creation times over the past 3 weeks
            Listing.objects.filter(pk=listing.pk).update(
                created_at=timezone.now() - timedelta(hours=random.randint(2, 500))
            )
            return listing

        listings = []
        for idx, name, tagline, description, whatsapp, verified, focus, inventory in VENDORS:
            owner = users[idx]
            Store.objects.create(
                owner=owner, name=name, tagline=tagline, description=description,
                whatsapp=whatsapp, is_verified=verified,
            )
            for title, price, condition, item_description in inventory:
                listings.append(create_listing(owner, title, price, focus, condition, item_description))

        for idx, title, price, category_slug, condition, description in ONE_OFFS:
            listings.append(create_listing(users[idx], title, price, category_slug, condition, description))

        # a few realistic non-active statuses
        for listing in random.sample(listings, 4):
            listing.status = random.choice([Listing.Status.SOLD, Listing.Status.PAUSED])
            listing.save(update_fields=["status"])

        # favorites: each user saves a few things they didn't post
        favorites = 0
        for user in users:
            for listing in random.sample(listings, random.randint(1, 5)):
                if listing.seller_id != user.id:
                    _, created = Favorite.objects.get_or_create(user=user, listing=listing)
                    favorites += created

        self.stdout.write(self.style.SUCCESS(
            f"Demo data ready: {len(users)} users, {Store.objects.count()} stores, "
            f"{len(listings)} listings ({ListingImage.objects.count()} images), {favorites} favorites.\n"
            f"All demo logins use password '{PASSWORD}', e.g. chinedu.okafor@{DOMAIN}"
        ))
