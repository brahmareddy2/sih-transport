import logging
import requests
from app.core.config import get_settings
from app.services.optimization.distance_matrix import INDIAN_CITIES, haversine_km

logger = logging.getLogger(__name__)
settings = get_settings()

# In-memory cache for coordinates to address geocoding to avoid rate-limiting
GEOCODE_CACHE = {}


def reverse_geocode(lat: float, lon: float) -> str:
    """
    Reverse geocodes a GPS coordinate to a readable name or address.
    Utilizes Nominatim OpenStreetMap with caching and a local city-proximity fallback.
    """
    if lat is None or lon is None:
        return "Unknown Location"

    # Standardize cache key
    key = (round(lat, 4), round(lon, 4))
    if key in GEOCODE_CACHE:
        return GEOCODE_CACHE[key]

    # 1. Attempt Nominatim OpenStreetMap Geocoding
    url = f"{settings.nominatim_base_url.rstrip('/')}/reverse"
    params = {"lat": lat, "lon": lon, "format": "json", "addressdetails": 1}
    headers = {"User-Agent": settings.nominatim_user_agent or "sih-logistics-dss/1.0"}

    try:
        response = requests.get(url, params=params, headers=headers, timeout=1.5)
        if response.status_code == 200:
            data = response.json()
            address = data.get("display_name")
            if address:
                # Clean address: extract key parts (street, suburb, city, state)
                addr_details = data.get("address", {})
                road = addr_details.get("road")
                suburb = addr_details.get("suburb")
                city = (
                    addr_details.get("city")
                    or addr_details.get("town")
                    or addr_details.get("village")
                    or addr_details.get("county")
                )
                state = addr_details.get("state")

                parts = []
                if road:
                    parts.append(road)
                if suburb:
                    parts.append(suburb)
                if city:
                    parts.append(city)
                if state:
                    parts.append(state)

                clean_address = ", ".join(parts) if parts else ", ".join(address.split(",")[:3])
                GEOCODE_CACHE[key] = clean_address
                return clean_address
    except Exception as e:
        logger.debug("Nominatim geocoding failed: %s. Falling back to pre-defined cities.", e)

    # 2. Pre-defined Indian Cities Fallback
    closest_city = "Unknown Location"
    min_dist = float("inf")
    for city_name, coords in INDIAN_CITIES.items():
        dist = haversine_km(lat, lon, coords["lat"], coords["lon"])
        if dist < min_dist:
            min_dist = dist
            closest_city = city_name

    if min_dist < 5.0:
        address = f"In {closest_city}"
    elif min_dist < 40.0:
        address = f"Near {closest_city} (~{round(min_dist)} km)"
    else:
        address = f"{round(lat, 4)}°N, {round(lon, 4)}°E (closest: {closest_city})"

    GEOCODE_CACHE[key] = address
    return address
