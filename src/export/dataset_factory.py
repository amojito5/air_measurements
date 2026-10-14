# src/export/dataset_factory.py
from typing import ClassVar

import numpy as np
import pandas as pd
import xarray as xr

from models.station import StationCollection
from quality.checker import QualityChecker


class NetCDFDatasetFactory:
    CF_STANDARD_NAMES: ClassVar[dict[str, str]] = {
        "no2": "mass_concentration_of_nitrogen_dioxide_in_air",
        "pm10": "mass_concentration_of_pm10_ambient_aerosol_in_air",
        "pm25": "mass_concentration_of_pm2p5_ambient_aerosol_in_air",
        "o3": "mass_concentration_of_ozone_in_air",
        "so2": "mass_concentration_of_sulfur_dioxide_in_air",
        "co": "mass_concentration_of_carbon_monoxide_in_air",
    }

    @staticmethod
    def create_from_collection(
        collection: StationCollection, freq: str = "1D"
    ) -> xr.Dataset:
        raw_records = []
        station_meta = {}

        # ... (Toute ta boucle d'extraction inchangée) ...
        for station in collection.stations:
            coords = station.coordinates or {}
            station_meta[station.id] = {
                "latitude": coords.get("latitude", np.nan),
                "longitude": coords.get("longitude", np.nan),
                "name": station.name,
            }

            for sensor in getattr(station, "sensors", []):
                measurements = getattr(sensor, "averages", None) or []
                param_info = getattr(sensor, "parameter", {})
                if isinstance(param_info, dict):
                    param_name = param_info.get("name", "unknown")
                    param_unit = param_info.get("units", "ug m-3")
                else:
                    param_name = "unknown"
                    param_unit = "ug m-3"

                for m in measurements:
                    if not isinstance(m, dict):
                        continue

                    val = m.get("value")
                    if val is None:
                        continue

                    time_str = (
                        m.get("time_from")
                        or m.get("time")
                        or m.get("datetime")
                        or (
                            m.get("period", {})
                            .get("datetimeFrom", {})
                            .get("utc")
                            if isinstance(m.get("period"), dict)
                            else None
                        )
                    )

                    if time_str:
                        raw_records.append(
                            {
                                "station_id": station.id,
                                "time": pd.to_datetime(time_str),
                                "parameter": param_name,
                                "value": float(val),
                                "unit": param_unit,
                            }
                        )

        if not raw_records:
            print("No hydratate data in collection. Check sensor.averages.")
            return xr.Dataset()

        df = pd.DataFrame(raw_records)

        # 1. INJECTION : QUALITY CHECKER
        qc = QualityChecker()
        for param in df["parameter"].unique():
            mask = df["parameter"] == param
            df.loc[mask, "value"] = qc.clean_series(
                parameter=str(param), series=df.loc[mask, "value"]
            )

        # Alignement matriciel xarray
        data_vars = {}
        unique_params = df["parameter"].unique()

        # 1. Extraction et nettoyage de l'axe temporel
        min_time = df["time"].min()
        max_time = df["time"].max()

        if getattr(min_time, "tzinfo", None) is not None:
            min_time = min_time.tz_localize(None)
            max_time = max_time.tz_localize(None)
            df["time"] = df["time"].dt.tz_localize(None)

        df["time"] = (
            pd.to_datetime(df["time"])
            .dt.to_period("Y")
            .dt.to_timestamp(how="end")
            .dt.floor("D")
        )
        # 2. Calcul de la moyenne annuelle par station et par polluant
        df_grouped = (
            df.groupby(["station_id", "time", "parameter"])["value"]
            .mean()
            .reset_index()
        )

        # 3. Grille temporelle annuelle alignée
        all_times = pd.date_range(
            start=df["time"].min(), end=df["time"].max(), freq="1YE"
        )
        all_stations = list(station_meta.keys())

        for param in unique_params:
            df_param = df[df["parameter"] == param]
            df_grouped = (
                df_param.groupby(["station_id", "time"])["value"]
                .mean()
                .reset_index()
            )
            df_pivot = df_grouped.pivot(
                index="station_id", columns="time", values="value"
            )
            df_reindexed = df_pivot.reindex(
                index=all_stations, columns=all_times
            )

            unit_str = (
                df_param["unit"].iloc[0] if not df_param.empty else "ug m-3"
            )

            data_vars[param] = (
                ["station", "time"],
                df_reindexed.values,
                {
                    "standard_name": (
                        NetCDFDatasetFactory.CF_STANDARD_NAMES.get(
                            param, f"mass_concentration_of_{param}_in_air"
                        )
                    ),
                    "units": unit_str,
                    "cell_methods": f"time: mean (interval: {freq})",
                    "_FillValue": np.nan,
                },
            )

        ds = xr.Dataset(
            data_vars=data_vars,
            coords={
                "station": (["station"], all_stations),
                "time": (["time"], all_times),
                "latitude": (
                    ["station"],
                    [station_meta[s]["latitude"] for s in all_stations],
                    {"standard_name": "latitude", "units": "degrees_north"},
                ),
                "longitude": (
                    ["station"],
                    [station_meta[s]["longitude"] for s in all_stations],
                    {"standard_name": "longitude", "units": "degrees_east"},
                ),
            },
            attrs={
                "title": "OpenAQ Atmospheric Measurements",
                "institution": "ECMWF / Copernicus Partner Pipeline",
                "conventions": "CF-1.8",
            },
        )

        return ds
