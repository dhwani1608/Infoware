import time
import requests
from config.settings import get_settings
from integrations.cache import FileCache


class GooglePlacesClient:
    def __init__(self):
        self.settings = get_settings()
        self.cache = FileCache(namespace="google_places")
        self.last_call = 0.0

    def _rate_limit(self):
        delta = time.time() - self.last_call
        min_interval = 1.0 / self.settings.api_rate_limit_per_second
        if delta < min_interval:
            time.sleep(min_interval - delta)
        self.last_call = time.time()

    def nearby_places(self, lat: float, lng: float, radius: int = 1200):
        key = f"np:{lat}:{lng}:{radius}"
        cached = self.cache.get(key)
        if cached:
            return cached
        if not self.settings.google_maps_api_key:
            mock = {
                "results": [
                    {"name": "Mock Fuel Station", "types": ["gas_station"], "rating": 4.1},
                    {"name": "Mock Warehouse", "types": ["storage"], "rating": 4.0},
                ],
                "source": "mock",
            }
            self.cache.set(key, mock)
            return mock
        self._rate_limit()
        url = f"{self.settings.google_maps_base_url}/place/nearbysearch/json"
        params = {"location": f"{lat},{lng}", "radius": radius, "key": self.settings.google_maps_api_key}
        for attempt in range(3):
            try:
                resp = requests.get(url, params=params, timeout=10)
                resp.raise_for_status()
                data = resp.json()
                self.cache.set(key, data)
                return data
            except Exception:
                if attempt == 2:
                    return {"results": [], "source": "fallback"}
                time.sleep(0.6 * (attempt + 1))

    def geocode_place(self, query: str):
        key = f"geocode:{query.strip().lower()}"
        cached = self.cache.get(key)
        if cached:
            return cached
        if not self.settings.google_maps_api_key:
            # Mock fallback centered near Ahmedabad to keep system fully usable without API key.
            mock = {
                "name": query,
                "latitude": 23.0225,
                "longitude": 72.5714,
                "region": "Ahmedabad",
                "source": "mock",
            }
            self.cache.set(key, mock)
            return mock

        self._rate_limit()
        url = f"{self.settings.google_maps_base_url}/geocode/json"
        params = {"address": query, "key": self.settings.google_maps_api_key}
        for attempt in range(3):
            try:
                resp = requests.get(url, params=params, timeout=10)
                resp.raise_for_status()
                data = resp.json()
                if not data.get("results"):
                    return None
                top = data["results"][0]
                loc = top["geometry"]["location"]
                region = "Unknown"
                for comp in top.get("address_components", []):
                    if "administrative_area_level_2" in comp.get("types", []):
                        region = comp.get("long_name", "Unknown")
                        break
                out = {
                    "name": query,
                    "latitude": float(loc["lat"]),
                    "longitude": float(loc["lng"]),
                    "region": region,
                    "source": "google",
                }
                self.cache.set(key, out)
                return out
            except Exception:
                if attempt == 2:
                    return None
                time.sleep(0.6 * (attempt + 1))

    def cache_stats(self) -> dict:
        return self.cache.stats()
