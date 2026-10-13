# src/export/visualizer.py
from pathlib import Path

import cartopy.crs as ccrs
import cartopy.feature as cfeature
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import xarray as xr
from matplotlib import animation


class AirQualityAnimator:

    def __init__(self, nc_path: str | Path):
        self.nc_path = Path(nc_path)
        if not self.nc_path.exists():
            raise FileNotFoundError(
                    f"Fichier NetCDF introuvable : {self.nc_path}"
                    )

        self.ds = xr.open_dataset(self.nc_path)

    def create_animation(
        self,
        variable: str = "no2",
        output_gif: str = "air_quality_animation.gif",
        cmap: str = "YlOrRd",
        fps: int = 2,
    ) -> Path:
        if variable not in self.ds.data_vars:
            raise ValueError(
                f"Variable '{variable}' non présente."
                f"Vars dispos : {list(self.ds.data_vars.keys())}"
            )

        # 1. Extraction
        lats_all = self.ds["latitude"].values
        lons_all = self.ds["longitude"].values
        times = self.ds["time"].values
        data_all = self.ds[variable].values

        # 2. Filtering
        valid_stations_mask = ~np.isnan(data_all).all(axis=1)

        if not np.any(valid_stations_mask):
            print(f"Aucune donnée disponible pour le polluant {variable}.")
            return Path(output_gif)

        lats = lats_all[valid_stations_mask]
        lons = lons_all[valid_stations_mask]
        data = data_all[valid_stations_mask, :]

        # 3. Min/max calculation
        valid_values = data[~np.isnan(data)]
        if len(valid_values) == 0:
            vmin, vmax = 0, 50
        else:
            vmin = 0
            vmax = float(np.percentile(valid_values, 95)) or 50.0

        units = self.ds[variable].attrs.get("units", "µg/m³")

        # 4. Configuration de la figure Cartopy
        fig = plt.figure(figsize=(10, 8))
        ax = plt.axes(projection=ccrs.PlateCarree())

        lon_margin = (lons.max() - lons.min()) * 0.2 if len(lons) > 1 else 0.1
        lat_margin = (lats.max() - lats.min()) * 0.2 if len(lats) > 1 else 0.1
        ax.set_extent(
            [
                lons.min() - lon_margin,
                lons.max() + lon_margin,
                lats.min() - lat_margin,
                lats.max() + lat_margin,
            ],
            crs=ccrs.PlateCarree(),
        )

        ax.add_feature(cfeature.BORDERS, linestyle=":")
        ax.add_feature(cfeature.COASTLINE)
        ax.add_feature(cfeature.RIVERS, alpha=0.5)
        ax.add_feature(cfeature.LAND, facecolor="#f4f4f0")
        ax.add_feature(cfeature.OCEAN, facecolor="#e0ede8")

        # 5. Tracer initial des points
        initial_frame_data = data[:, 0]
        scatter = ax.scatter(
            lons,
            lats,
            c=initial_frame_data,
            cmap=cmap,
            vmin=vmin,
            vmax=vmax,
            s=120,
            edgecolors="black",
            linewidth=0.8,
            transform=ccrs.PlateCarree(),
            zorder=5,
        )

        cbar = plt.colorbar(
                scatter,
                ax=ax,
                orientation="vertical",
                shrink=0.7,
                pad=0.03
        )
        cbar.set_label(
                f"Concentration ({units})",
                fontsize=11,
                fontweight="bold")

        title_time = pd.to_datetime(times[0]).strftime("%Y-%m-%d %H:%M UTC")
        title_text = ax.set_title(
            f"OpenAQ {variable.upper()} - {title_time}",
            fontsize=13,
            fontweight="bold",
            pad=12,
        )

        # 6. Animation frame by frame
        def update(frame: int):
            current_time = pd.to_datetime(
                    times[frame]).strftime(
                            "%Y-%m-%d %H:%M UTC"
                            )
            frame_values = data[:, frame]
            scatter.set_array(frame_values)
            title_text.set_text(f"OpenAQ {variable.upper()} - {current_time}")
            return scatter, title_text

        ani = animation.FuncAnimation(
            fig, update, frames=len(times), interval=1000 // fps, blit=False
        )

        output_path = Path(output_gif)
        ani.save(output_path, writer="pillow", fps=fps)
        plt.close(fig)

        print(f"Animation GIF générée : {output_path.resolve()}")
        return output_path
