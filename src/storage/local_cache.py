# src/storage/local_cache.py
import json
import time
from pathlib import Path
from typing import Optional


class LocalCache:
    """Gère la persistance JSON avec péremption par durée de vie (TTL)."""

    def __init__(
        self, cache_dir: str = "data/cache", ttl_seconds: int = 86400
    ):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.ttl_seconds = ttl_seconds  # 86400s = 24 heures

    def _get_path(self, key: str) -> Path:
        return self.cache_dir / f"{key}.json"

    def get(self, key: str) -> Optional[dict]:
        """Renvoie les données si le fichier existe et que son âge < ttl_seconds."""
        filepath = self._get_path(key)
        if not filepath.exists():
            return None

        # Vérification de l'âge du fichier
        file_age = time.time() - filepath.stat().st_mtime
        if file_age > self.ttl_seconds:
            print(
                f"⌛ Cache expiré ({int(file_age / 3600)}h). Récupération réseau requise."
            )
            return None

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None

    def set(self, key: str, data: dict) -> None:
        """Enregistre le dictionnaire en JSON local."""
        filepath = self._get_path(key)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)