# src/quality/checker.py
import logging
from typing import ClassVar

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class QualityChecker:
    """Quality Checker module"""

    THRESHOLDS: ClassVar[dict[str, dict[str, float]]] = {
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
            logger.warning(f"No QC threshold for '{parameter}'.")
            return series

        bounds = self.thresholds[param_clean]
        min_val, max_val = bounds["min"], bounds["max"]

        cleaned = series.copy()

        invalid_mask = (cleaned < min_val) | (cleaned > max_val)
        nb_invalids = invalid_mask.sum()

        if nb_invalids > 0:
            logger.info(f"QC [{param_clean.upper()}]: {nb_invalids} to NaN.")
            cleaned[invalid_mask] = np.nan

        return cleaned
