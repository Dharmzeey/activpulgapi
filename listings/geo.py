"""Haversine distance in the ORM — portable across SQLite and Postgres.

Good enough for campus-scale proximity ranking; swap for PostGIS if spatial
queries ever need real indexes.
"""

import math

from django.db.models import F, FloatField, Value
from django.db.models.functions import ACos, Cos, Least, Radians, Sin

EARTH_RADIUS_KM = 6371.0


def with_distance(queryset, latitude, longitude):
    """Annotate each row with `distance_km` from the given point.

    Rows without coordinates get NULL, which sorts last on ascending order.
    """
    lat_rad = math.radians(float(latitude))
    lng_rad = math.radians(float(longitude))
    # Least(..., 1.0) guards ACos against floating-point drift past its domain.
    return queryset.annotate(
        distance_km=EARTH_RADIUS_KM
        * ACos(
            Least(
                Value(math.cos(lat_rad)) * Cos(Radians(F("latitude")))
                * Cos(Radians(F("longitude")) - Value(lng_rad))
                + Value(math.sin(lat_rad)) * Sin(Radians(F("latitude"))),
                Value(1.0),
            ),
            output_field=FloatField(),
        )
    )
