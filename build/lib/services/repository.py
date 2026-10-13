# src/services/station_repository.py
from concurrent.futures import ThreadPoolExecutor

from src.models.station import StationCollection
from src.services.client import OpenAQClient
from src.storage.local_cache import LocalCache


class StationRepository:

    def __init__(
        self,
        client: OpenAQClient,
        cache: LocalCache | None = None,
        max_workers: int = 2,
    ):
        self.client = client
        self.cache = cache or LocalCache(ttl_seconds=86400)
        self.max_workers = max_workers

    def _fetch_single_sensor_averages(
        self, 
        sensor_id: int, 
        force_refresh: bool = False
    ) -> tuple[int, list[dict]]:
        cache_key = f"sensors/{sensor_id}"

        if not force_refresh:
            cached_data = self.cache.get(cache_key)
            if cached_data is not None:
                return sensor_id, cached_data

        try:
            # Appel API
            raw_averages = self.client.get_average(sensor_id)
            
            records = []
            if raw_averages:
                for item in raw_averages:
                    if isinstance(item, dict):
                        records.append(item)

                self.cache.set(cache_key, records)
                return sensor_id, records
            else:
                self.cache.set(cache_key, [])
                return sensor_id, []

        except Exception as err:
            print(f"⚠️ Échec temporaire capteur {sensor_id} ({err}) - NON MIS EN CACHE")
            return sensor_id, []


    def get_hydrated_stations(
            self,
            bbox: tuple[float, float, float, float],
            force_refresh: bool = False,
        ) -> StationCollection:
            cache_key = f"stations/bbox_{bbox[0]}_{bbox[1]}_{bbox[2]}_{bbox[3]}"

            # 1. On récupère la structure des stations (Cache ou API)
            cached_data = None if force_refresh else self.cache.get(cache_key)

            if cached_data:
                print("⚡ Structure des stations lue depuis le cache local.")
                collection = StationCollection.from_dict(cached_data)
            else:
                print("🌐 Exécution de la requête API OpenAQ (BBox)...")
                collection = self.client.get_stations(bbox)
                if collection:
                    # On sauvegarde la structure de la BBox sur disque
                    self.cache.set(cache_key, collection.to_dict())

            # 2. Le ThreadPoolExecutor DOIT ÊTRE HORS DU ELSE 
            # pour lire les capteurs en cache (ou l'API) à chaque appel
            averages_map = {}
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                results = executor.map(
                    lambda s_id: self._fetch_single_sensor_averages(s_id, force_refresh),
                    collection.sensor_ids
                )
                for sensor_id, values in results:
                    if values:
                        averages_map[sensor_id] = values

            # 3. Hydratation finale de l'objet domaine en mémoire
            collection.set_averages_bulk(averages_map)

            return collection
            