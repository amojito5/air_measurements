import logging
from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

from models import station

logging.basicConfig(level=logging.INFO)


class OpenAQClient:

    def __init__(
            self,
            api_key: str,
            timeout: int = 10,
            retries: int = 3,
            default_limit: int = 100
            ):
        self.api_key = api_key
        self.BASE_URL = "https://api.openaq.org/v3/"
        self.timeout = timeout
        self.default_limit = default_limit
        self.session = requests.Session()
        self.session.headers.update({"X-API-Key": self.api_key})

        # --- Stratégie de Retry globale ---
        retry_strategy = Retry(
            total=retries,  # Nombre max de tentatives
            backoff_factor=1,  # Attend 1s, puis 2s, puis 4s...
            status_forcelist=[
                429,
                500,
                502,
                503,
                504,
            ],  # Erreurs serveur ou Rate Limit
            allowed_methods=["GET"],  # S'applique uniquement aux requêtes GET
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

    def get_stations(
        self, bbox: tuple[float, float, float, float], limit: int | None = None
    ) -> list[dict[str, Any]]:
        """Retrieve bouding box limits"""
        min_lon, min_lat, max_lon, max_lat = bbox
        endpoint = f"{self.BASE_URL}locations"
        params = {
            "bbox": f"{min_lon},{min_lat},{max_lon},{max_lat}",
            "limit": limit if limit is not None else self.default_limit,
        }

        response = self.session.get(
            endpoint, params=params, timeout=self.timeout
        )
        response.raise_for_status()
        return station.StationCollection.from_openaq_list(
                response.json().get("results", [])
                )

    def get_average(
            self, sensor_id: int, limit: int = 1000
    ) -> list[dict[str, Any]]:
        """Retrieve senors mean values."""
        endpoint = f"{self.BASE_URL}sensors/{sensor_id}/days"
        params = {
            "limit": limit,
        }
        response = self.session.get(
            endpoint, params=params, timeout=self.timeout
        )
        response.raise_for_status()
        return response.json().get("results", [])
