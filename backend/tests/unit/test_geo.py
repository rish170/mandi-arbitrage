import math
import pytest
from app.core.geo import (
    estimate_duration_minutes,
    haversine_distance_km,
    haversine_fallback_distance_km,
)

def test_haversine_zero_distance():
    # Same point should have 0 distance
    assert haversine_distance_km(18.5204, 73.8567, 18.5204, 73.8567) == pytest.approx(0.0)

def test_haversine_known_distance_pune_mumbai():
    # Pune (18.5204, 73.8567) to Mumbai (18.9220, 72.8347)
    # Great circle distance is approx 120-125 km
    dist = haversine_distance_km(18.5204, 73.8567, 18.9220, 72.8347)
    assert 115.0 < dist < 130.0

def test_haversine_road_fallback():
    crow_km = haversine_distance_km(18.5204, 73.8567, 18.9220, 72.8347)
    road_km = haversine_fallback_distance_km(18.5204, 73.8567, 18.9220, 72.8347, road_factor=1.3)
    assert road_km == pytest.approx(crow_km * 1.3)

def test_estimate_duration():
    # 40 km at 40 km/h should take 60 minutes
    assert estimate_duration_minutes(40.0, average_speed_kmh=40.0) == pytest.approx(60.0)
    # 80 km at 40 km/h should take 120 minutes
    assert estimate_duration_minutes(80.0, average_speed_kmh=40.0) == pytest.approx(120.0)
