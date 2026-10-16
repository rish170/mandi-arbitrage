import math

EARTH_RADIUS_KM = 6371.0088

def haversine_distance_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Calculate the great circle distance between two points on Earth in kilometers."""
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lng2 - lng1)

    a = (
        math.sin(delta_phi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * (math.sin(delta_lambda / 2.0) ** 2)
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return EARTH_RADIUS_KM * c

def haversine_fallback_distance_km(
    lat1: float, lng1: float, lat2: float, lng2: float, road_factor: float = 1.3
) -> float:
    """Estimate road distance using haversine multiplied by a winding/road factor."""
    crow_km = haversine_distance_km(lat1, lng1, lat2, lng2)
    return crow_km * road_factor

def estimate_duration_minutes(
    road_km: float, average_speed_kmh: float = 40.0
) -> float:
    """Estimate travel duration in minutes based on distance and average speed."""
    if average_speed_kmh <= 0:
        return 0.0
    return (road_km / average_speed_kmh) * 60.0
