import logging
import requests
from fastapi import APIRouter, Depends, HTTPException, status
from app.core.config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/nearby", tags=["Nearby Places Locator"])
settings = get_settings()

@router.get("/petrol-pumps", summary="Find nearby petrol pumps")
def get_nearby_petrol_pumps(lat: float, lng: float, radius: float = 5000):
    """
    Get nearby gas stations using Google Places API (Nearby Search).
    If no API key is configured, falls back to realistic Indian mock gas stations.
    """
    api_key = settings.google_maps_api_key
    if not api_key:
        logger.warning("GOOGLE_MAPS_API_KEY not configured. Falling back to mock data.")
        return {
            "status": "mock",
            "results": [
                {
                    "name": "Indian Oil Coco Bunk (IOCL)",
                    "lat": lat + 0.008,
                    "lng": lng + 0.005,
                    "address": "NH-44 Corridor, near Toll Plaza",
                    "rating": 4.5,
                    "fuels": ["Petrol", "Diesel", "CNG"]
                },
                {
                    "name": "Bharat Petroleum COCO Hub (BPCL)",
                    "lat": lat - 0.012,
                    "lng": lng - 0.009,
                    "address": "Highway Mile 120, Exit 4",
                    "rating": 4.2,
                    "fuels": ["Petrol", "Diesel"]
                },
                {
                    "name": "Hindustan Petroleum Highway Bunk (HPCL)",
                    "lat": lat + 0.015,
                    "lng": lng - 0.004,
                    "address": "NH-48 Express bypass",
                    "rating": 4.0,
                    "fuels": ["Diesel", "CNG"]
                }
            ]
        }

    url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    params = {
        "location": f"{lat},{lng}",
        "radius": radius,
        "type": "gas_station",
        "key": api_key
    }
    
    try:
        response = requests.get(url, params=params)
        data = response.json()
        if data.get("status") not in ["OK", "ZERO_RESULTS"]:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Google Places API error: {data.get('error_message', 'Unknown error')}"
            )
        
        results = []
        for p in data.get("results", []):
            loc = p.get("geometry", {}).get("location", {})
            results.append({
                "name": p.get("name"),
                "lat": loc.get("lat"),
                "lng": loc.get("lng"),
                "address": p.get("vicinity"),
                "rating": p.get("rating", 0)
            })
        return {"status": "ok", "results": results}
    except Exception as e:
        logger.error("Failed to query Google Places API: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to query nearby gas stations: {str(e)}"
        )

@router.get("/mechanics", summary="Find nearby mechanics and repair shops")
def get_nearby_mechanics(lat: float, lng: float, radius: float = 5000):
    """
    Get nearby car repair shops using Google Places API (Nearby Search).
    If no API key is configured, falls back to realistic Indian mock mechanics.
    """
    api_key = settings.google_maps_api_key
    if not api_key:
        logger.warning("GOOGLE_MAPS_API_KEY not configured. Falling back to mock data.")
        return {
            "status": "mock",
            "results": [
                {
                    "name": "Om Sai Tubeless Tyre & Puncture Care",
                    "lat": lat - 0.005,
                    "lng": lng + 0.012,
                    "address": "NH-44 Bypass, opposite Shiva Dhaba",
                    "rating": 4.7
                },
                {
                    "name": "Highway Heavy Truck Garage & Mechanics",
                    "lat": lat + 0.011,
                    "lng": lng - 0.014,
                    "address": "Service Lane 3, Nagpur Bypass",
                    "rating": 4.4
                },
                {
                    "name": "Bajrang Auto Electricals & Puncture Shop",
                    "lat": lat - 0.015,
                    "lng": lng + 0.008,
                    "address": "State Highway Toll Exit",
                    "rating": 4.1
                }
            ]
        }

    url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    params = {
        "location": f"{lat},{lng}",
        "radius": radius,
        "type": "car_repair",
        "key": api_key
    }
    
    try:
        response = requests.get(url, params=params)
        data = response.json()
        if data.get("status") not in ["OK", "ZERO_RESULTS"]:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Google Places API error: {data.get('error_message', 'Unknown error')}"
            )
        
        results = []
        for p in data.get("results", []):
            loc = p.get("geometry", {}).get("location", {})
            results.append({
                "name": p.get("name"),
                "lat": loc.get("lat"),
                "lng": loc.get("lng"),
                "address": p.get("vicinity"),
                "rating": p.get("rating", 0)
            })
        return {"status": "ok", "results": results}
    except Exception as e:
        logger.error("Failed to query Google Places API: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to query nearby mechanics: {str(e)}"
        )
