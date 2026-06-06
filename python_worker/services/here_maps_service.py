import json
import logging
import requests
import urllib.request
import urllib.parse

logger = logging.getLogger("USIWorker.HereMapsService")

class HereMapsService:
    """
    Service for interacting with HERE Maps APIs (Geocoding, Places/POI, Static Maps).
    Centralizes all external geographic API calls.
    """
    
    # Places Browse API — category IDs
    HERE_CATEGORIES = {
        "food":          "100-1000",
        "entertainment": "200-2000",
        "outdoor":       "300-3000",
        "transport":     "400-4000",
        "shopping":      "600-6000",
        "education":     "700-7000",
        "health":        "800-8000",
    }
    
    HERE_RADIUS_M = 2000
    HERE_LIMIT_PER_CAT = 5
    
    _BASE_STATIC = "https://image.maps.hereapi.com/mia/v3/base/mc"
    _GEOCODE_URL = "https://geocode.search.hereapi.com/v1/geocode"
    _BROWSE_URL = "https://browse.search.hereapi.com/v1/browse"

    def __init__(self, api_key: str):
        self.api_key = api_key

    def geocode_address(self, address: str) -> tuple[float, float] | tuple[None, None]:
        """Convert address string to (lat, lon) using HERE Geocoding API."""
        if not address or not self.api_key:
            return None, None
        
        try:
            params = urllib.parse.urlencode({"q": address, "apiKey": self.api_key})
            url = f"{self._GEOCODE_URL}?{params}"
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
        self,
        lat: float,
        lon: float,
        *,
        zoom: int = 16,
        width: int = 1536,
        height: int = 512,
        dark: bool = False,
        style: str = None,
        lang: str = "pl",
        scale_bar: str = "km",
        pois: bool = False,
        marker_size: str = "large",
        marker_icon: str = "bubble",
    ) -> str:
        """Generates a URL for the HERE Static Map image."""
        if style is None:
            style = "explore.satellite.night" if dark else "explore.satellite.day"
        
        pois_val = "enabled" if pois else "disabled"
        path = f"overlay:zoom={zoom}/{width}x{height}/png"
        query = (
            f"apiKey={self.api_key}"
            f"&overlay=point:{lat},{lon}|size={marker_size};icon={marker_icon}"
            f"&style={style}"
            f"&scaleBar={scale_bar}"
            f"&features=pois:{pois_val}"
            f"&lang={lang}"
        )
        return f"{self._BASE_STATIC}/{path}?{query}"

    def fetch_places(self, lat: float, lon: float) -> list[dict]:
        """Fetches points of interest around coordinates using HERE Places Browse API in parallel."""
        if not self.api_key:
            return []

        import concurrent.futures
        results = []
        seen_ids = set()

        # Funkcja pomocnicza do pobierania pojedynczej kategorii w osobnym wątku
        def fetch_category(cat_name, cat_id):
            params = urllib.parse.urlencode({
                "at": f"{lat},{lon}",
                "categories": cat_id,
                "limit": self.HERE_LIMIT_PER_CAT,
                "radius": self.HERE_RADIUS_M,
                "lang": "pl",
                "apiKey": self.api_key,
            })
            url = f"{self._BROWSE_URL}?{params}"
            try:
                with urllib.request.urlopen(url, timeout=5) as resp:
                    return cat_name, json.loads(resp.read().decode())
            except Exception as e:
                logger.warning("HERE Places fetch failed for cat %s: %s", cat_name, e)
                return cat_name, None

        # Uruchomienie zapytań dla wszystkich kategorii równolegle
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(self.HERE_CATEGORIES)) as executor:
            futures = [executor.submit(fetch_category, name, cid) for name, cid in self.HERE_CATEGORIES.items()]
            
            for future in concurrent.futures.as_completed(futures):
                cat_name, data = future.result()
                if not data:
                    continue
                
                for item in data.get("items", []):
                    pid = item.get("id", "")
                    if pid in seen_ids:
                        continue
                    seen_ids.add(pid)
                    cat_label = (item.get("categories") or [{}])[0].get("name", cat_name)
                    results.append({
                        "id": pid,
                        "category": cat_name,
                        "category_label": cat_label,
                        "name": item.get("title", ""),
                        "address": item.get("address", {}).get("label", ""),
                        "distance": item.get("distance", 0),
                        "lat": (item.get("position") or {}).get("lat"),
                        "lon": (item.get("position") or {}).get("lng"),
                    })

        results.sort(key=lambda x: x["distance"])
        return results
