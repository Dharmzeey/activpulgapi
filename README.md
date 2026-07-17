# ActivPlug API

Django REST backend for **ActivPlug**, the campus marketplace: students at
Nigerian institutions sell (side-hustle vendors or one-off declutterers) and
buy from people near them. The Next.js frontend lives in `../../frontend/my-app`.

## Stack & conventions

- Django 6 + Django REST Framework, SimpleJWT, django-filter, Pillow, django-environ.
- **Models → views (DRF generics) → explicit `urls.py`.** No ViewSets, no routers.
- SQLite in development; set `DATABASE_URL` for Postgres in production.
- Timezone `Africa/Lagos`; prices are naira (currency handling lives in the frontend).

## Getting started

```bash
# from this directory (the repo root, containing manage.py)
..\Scripts\python.exe -m pip install -r requirements.txt
copy .env.example .env         # then fill in values (dev defaults mostly work)
..\Scripts\python.exe manage.py migrate
..\Scripts\python.exe manage.py seed        # categories + 474 Nigerian institutions
..\Scripts\python.exe manage.py seed_demo   # optional: realistic demo users/stores/listings
..\Scripts\python.exe manage.py runserver 8000
```

Settings are split per environment in `activplug/settings/`:

| Module | Used by | Behaviour |
|---|---|---|
| `base.py` | everything | shared config, env-driven via `.env` |
| `development.py` | `manage.py` (default) | DEBUG on, permissive hosts |
| `production.py` | `wsgi.py`/`asgi.py` (default) | fails fast on weak `SECRET_KEY`, missing `ALLOWED_HOSTS` or `GOOGLE_CLIENT_ID`; HSTS, SSL redirect, secure cookies |

## Apps

- **accounts** — email-login `User` (unique, alias-collapsed `canonical_email`;
  unique E.164 `+234` WhatsApp `phone`), `State` → `Town` (owns coordinates) →
  `School` (474 institutions: universities, polytechnics, colleges of
  education/health, technical). Auth endpoints.
- **listings** — `Category`, `Listing` (auto-located from the seller, unique
  SEO slug, up to 6 images), `Favorite`. Proximity search and recommendations.
- **stores** — optional `Store` storefront layered on a seller account
  (one-to-one). Closing a store gracefully demotes the seller to personal
  listings; nothing on listings changes.

## Authentication & anti-bot defenses

Two sign-in paths, JWT (SimpleJWT) either way — access 30 min, refresh 7 days,
rotation + blacklist:

- `POST /api/v1/auth/google/` — Google ID token, verified server-side
  (audience-pinned, `email_verified` required). Set `GOOGLE_CLIENT_ID`.
- `POST /api/v1/auth/register/` — email/password, defended by:
  disposable-domain blocklist (`accounts/data/disposable_email_domains.txt`),
  canonical-email uniqueness (strips `+tags`, collapses Gmail dots), a
  honeypot field (`website`), a 5/hour per-IP throttle, and Django's
  password validators.

Publishing (creating listings or a storefront) requires a contact phone
(`HasContactPhoneForWrites`) — it doubles as the WhatsApp deal channel.

## Endpoints (all under `/api/v1/`)

```
auth/register|google|login|refresh|logout|me/        auth/schools/?type=&state=&search=
categories/
listings/?search=&category=&school=&store=&condition=&min_price=&max_price=
          &lat=&lng=&radius_km=&ordering=(distance|price|-price|-created_at)
listings/mine/            listings/<slug>/           listings/<slug>/favorite/
favorites/                recommendations/
stores/                   stores/create/             stores/mine/          stores/<slug>/
```

## Location & proximity

Coordinates live on `Town` (normalized: 37 `State` rows, ~271 towns), so the
full school list serves in one SQL query. Listings inherit the seller's
coordinates (profile → school town) unless explicitly overridden. Distance is
a portable haversine ORM annotation (`listings/geo.py`) — works on SQLite and
Postgres; swap for PostGIS only if spatial indexes ever become necessary.
Anonymous browsers can pass `lat`/`lng`; signed-in users fall back to their
profile location automatically. `recommendations/` ranks nearby active
listings boosted by the user's favorited categories.

Institution data is seeded from `accounts/data/nigeria_institutions.json`;
append entries and re-run `manage.py seed` (idempotent) to extend it.
Coordinates are town-level and can be refined per-town in the admin.

## Gotchas worth knowing

- Don't set a default `ordering` on views that rank by the distance
  annotation — DRF's `OrderingFilter` applies it after `get_queryset` and
  silently overrides the proximity sort.
- `DELETE` endpoints return 204 (no content) on success.
- Demo data: `manage.py seed_demo --fresh` recreates everything under
  `@demo.activplug.ng` (password `demo-pass-123`).
