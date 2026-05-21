"""Lightweight geo helpers for bbox filtering."""
from __future__ import annotations

import math


def in_bbox(
    lat: float,
    lon: float,
    min_lat: float,
    min_lon: float,
    max_lat: float,
    max_lon: float,
) -> bool:
    return min_lat <= lat <= max_lat and min_lon <= lon <= max_lon


def radius_km_from_height_m(height_m: float) -> float:
    """Approximate ground search radius from camera altitude."""
    h = max(100.0, float(height_m))
    return min(80.0, max(2.0, h / 800.0))


def distance_nm_from_height_m(height_m: float) -> int:
    km = radius_km_from_height_m(height_m)
    nm = km / 1.852
    return int(max(50, min(400, round(nm))))
