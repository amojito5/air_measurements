# src/services/station_repository.py
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Optional

from src.models.station import StationCollection
from src.services.client import OpenAQClient
from src.storage.local_cache import LocalCache


class StationRepository:

    def __init__(
        self,
        client: OpenAQClient,
        cache: Optional[LocalCache] = None,
        max_workers: int = 2,
    ):
        self.client = client
        self.cache = cache or LocalCache(ttl_seconds=86400)
        self.max_workers = max_workers

    def _fetch_single_sensor_averages(
        self, sensor_id: int
    ) -> tuple[int, list[float]]:
        try:
            # 0.2s de pause entre chaque thread pour ne pas étouffer l'API
            time.sleep(0.2)
            raw_averages = self.client.get_average(sensor_id)
            if raw_averages:
                values = [
                    vals["value"] for vals in raw_averages if "value" in vals
                ]
                return sensor_id, values
        except Exception as err:
            print(f"⚠️ Erreur capteur {sensor_id}: {err}")
        return sensor_id, []

    def get_hydrated_stations(
        self,
        bbox: tuple[float, float, float, float],
        force_refresh: bool = False,
    ) -> StationCollection:
        cache_key = f"bbox_{bbox[0]}_{bbox[1]}_{bbox[2]}_{bbox[3]}"

        if not force_refresh:
            cached_data = self.cache.get(cache_key)
            if cached_data:
                print("⚡ Données lues depuis le cache local (0 appel réseau).")
                return StationCollection.from_dict(cached_data)

        print("🌐 Exécution des requêtes API OpenAQ...")
        collection = self.client.get_stations(bbox)

        averages_map = {}
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            results = executor.map(
                self._fetch_single_sensor_averages, collection.sensor_ids
            )
            for sensor_id, values in results:
                if values:
                    averages_map[sensor_id] = values

        collection.set_averages_bulk(averages_map)

        # On ne sauvegarde en cache que si on a pu récupérer au moins une partie significative des données
        if averages_map:
            self.cache.set(cache_key, collection.to_dict())

        return collection