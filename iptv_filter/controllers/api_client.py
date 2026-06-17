import requests
from typing import Dict, Any
from iptv_filter.utils.constants import API_ENDPOINTS
from .cache_manager import CacheManager

class ApiClient:
    def __init__(self, cache_manager: CacheManager):
        self.cache = cache_manager

    def fetch_data(self, key: str, force: bool = False) -> Any:
        """Fetches data from cache or API."""
        if key not in API_ENDPOINTS:
            raise ValueError(f"Unknown endpoint key: {key}")

        if not force:
            cached_data = self.cache.get(key)
            if cached_data is not None:
                return cached_data

        url = API_ENDPOINTS[key]
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        data = response.json()

        self.cache.set(key, data)
        return data

    def fetch_all(self, force: bool = False, progress_callback=None) -> Dict[str, Any]:
        """Fetches all necessary data for the application."""
        result = {}
        keys = list(API_ENDPOINTS.keys())
        total = len(keys)

        for i, key in enumerate(keys):
            if progress_callback:
                progress_callback(i, total, f"Fetching {key}...")
            result[key] = self.fetch_data(key, force=force)

        if progress_callback:
            progress_callback(total, total, "Finished fetching data.")

        return result
