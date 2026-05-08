import logging
import json
import requests
from .config import HERE_API_KEY

logger = logging.getLogger(__name__)

_BASE = "https://image.maps.hereapi.com/mia/v3/base/mc"
_GEOCODE_URL = "https://geocode.search.hereapi.com/v1/geocode"


def geocode_address(address: str) -> tuple[float, float] | tuple[None, None]:
    """Convert address string to (lat, lon) using HERE Geocoding API."""
    if not address or not HERE_API_KEY:
        return None, None
    
    try:
        url = f"{_GEOCODE_URL}?q={address}&apiKey={HERE_API_KEY}"
        # Use standard requests for simple geocoding call
        resp = requests.get(url, timeout=10)
        if resp.status_code != 200:
            logger.error(f"HERE Geocode API returned {resp.status_code}: {resp.text}")
            return None, None
            
        data = resp.json()
        items = data.get("items", [])
        if items:
            pos = items[0].get("position", {})
            return pos.get("lat"), pos.get("lng")
    except Exception as e:
        logger.error(f"Geocoding error for {address}: {e}")
        
    return None, None


def build_here_url(
    lat: float,
    lon: float,
    *,
    zoom: int = 16,
    width: int = 1536,
    height: int = 512,
    style: str = "explore.satellite.day",
    lang: str = "pl",
    scale_bar: str = "km",
    pois: bool = False,
    marker_size: str = "large",
    marker_icon: str = "bubble",
) -> str:
    pois_val = "enabled" if pois else "disabled"
    path = f"overlay:zoom={zoom}/{width}x{height}/png"
    # HERE API requires unencoded colons, commas, pipes, semicolons in overlay params
    query = (
        f"apiKey={HERE_API_KEY}"
        f"&overlay=point:{lat},{lon}|size={marker_size};icon={marker_icon}"
        f"&style={style}"
        f"&scaleBar={scale_bar}"
        f"&features=pois:{pois_val}"
        f"&lang={lang}"
    )
    return f"{_BASE}/{path}?{query}"


def enrich_with_here_map(result: dict) -> dict:
    lat = result.get("latitude")
    lon = result.get("longitude")
    if lat is None or lon is None:
        return result
    try:
        result["here_map_url"] = build_here_url(float(lat), float(lon))
    except Exception as e:
        logger.warning(f"Could not build HERE map URL: {e}")
    return result
