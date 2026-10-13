# src/quality/checker.py
import logging

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

class QualityChecker:
    """Module de contrôle qualité (QC) pour les données d'observations de qualité de l'air."""
    
    # Seuils physiques plausibles (en µg/m³)
    # Les valeurs en dehors de cette plage sont considérées comme des erreurs d'instrumentation.
    THRESHOLDS = {
        "no2": {"min": 0.0, "max": 1000.0},
        "pm25": {"min": 0.0, "max": 1000.0},
        "pm10": {"min": 0.0, "max": 2000.0},
        "o3": {"min": 0.0, "max": 1000.0},
        "so2": {"min": 0.0, "max": 2000.0},
    }

    def __init__(self, custom_thresholds: dict | None = None):
        """Possibilité de surcharger les seuils par défaut."""
        self.thresholds = custom_thresholds or self.THRESHOLDS

    def clean_series(self, parameter: str, series: pd.Series) -> pd.Series:
        """Nettoie une série Pandas de mesures pour un polluant donné."""
        param_clean = parameter.lower().strip()
        
        if param_clean not in self.thresholds:
            logger.warning(f"⚠️ Aucun seuil QC défini pour '{parameter}'. Aucune validation effectuée.")
            return series

        bounds = self.thresholds[param_clean]
        min_val, max_val = bounds["min"], bounds["max"]

        # Copie pour éviter le SettingWithCopyWarning
        cleaned = series.copy()

        # Identification des anomalies (valeurs négatives ou hors limites supérieures)
        invalid_mask = (cleaned < min_val) | (cleaned > max_val)
        nb_invalids = invalid_mask.sum()

        if nb_invalids > 0:
            logger.info(f"🧹 QC [{param_clean.upper()}]: {nb_invalids} valeur(s) aberrante(s) remplacée(s) par NaN.")
            cleaned[invalid_mask] = np.nan

        return cleaned
