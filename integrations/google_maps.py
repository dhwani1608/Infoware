import math
import time
import requests
from typing import Dict
from config.settings import get_settings
from integrations.cache import FileCache


class GoogleMapsClient:
    def __init__(self):
        self.settings = get_settings()
        self.cache = FileCache(namespace="google_maps")
        self.last_call = 0.0

    def _rate_limit(self):
        delta = time.time() - self.last_call
        min_interval = 1.0 / self.settings.api_rate_limit_per_second
        if delta < min_interval:
            time.sleep(min_interval - delta)
        self.last_call = time.time()

    @staticmethod
    def _haversine_km(origin: tuple[float, float], destination: tuple[float, float]) -> float:
        r = 6371.0
        lat1, lon1 = map(math.radians, origin)
        lat2, lon2 = map(math.radians, destination)
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
        return 2 * r * math.asin(math.sqrt(a))

    def distance_matrix(
        self,
        origin: tuple[float, float],
        destination: tuple[float, float],
        traffic: str = "medium",
        bypass_cache: bool = False,
    ) -> Dict:
        # Bucket cache by 15-minute windows so we can react to traffic shifts.
        traffic_bucket = int(time.time() // 900)
        key = f"dm:{origin}:{destination}:{traffic}:{traffic_bucket}"
        if bypass_cache:
            self.cache.invalidate(key)
        cached = self.cache.get(key)
        if cached:
            return cached

        if not self.settings.google_maps_api_key:
            distance_km = self._haversine_km(origin, destination) * 1.18
            speed = {"low": 38, "medium": 28, "high": 20}.get(traffic, 28)
            duration_min = distance_km / speed * 60
            response = {"distance_km": round(distance_km, 2), "duration_min": round(duration_min, 2), "source": "mock"}
            self.cache.set(key, response)
            return response

        self._rate_limit()
        url = f"{self.settings.google_maps_base_url}/distancematrix/json"
        params = {
            "origins": f"{origin[0]},{origin[1]}",
            "destinations": f"{destination[0]},{destination[1]}",
            "departure_time": "now",
            "key": self.settings.google_maps_api_key,
        }
        for attempt in range(3):
            try:
                resp = requests.get(url, params=params, timeout=10)
                resp.raise_for_status()
                data = resp.json()
                element = data["rows"][0]["elements"][0]
                output = {
                    "distance_km": round(element["distance"]["value"] / 1000, 2),
                    "duration_min": round(element.get("duration_in_traffic", element["duration"])["value"] / 60, 2),
                    "source": "google",
                }
                self.cache.set(key, output)
                return output
            except Exception:
                if attempt == 2:
                    distance_km = self._haversine_km(origin, destination) * 1.2
                    speed = {"low": 36, "medium": 27, "high": 19}.get(traffic, 27)
                    fallback = {
                        "distance_km": round(distance_km, 2),
                        "duration_min": round(distance_km / speed * 60, 2),
                        "source": "fallback",
                    }
                    self.cache.set(key, fallback)
                    return fallback
                time.sleep(0.6 * (attempt + 1))

    def cache_stats(self) -> dict:
        return self.cache.stats()
