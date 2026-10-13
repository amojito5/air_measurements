# src/export/netcdf_exporter.py
from pathlib import Path

import xarray as xr


class NetCDFExporter:
    """Gère la persistance physique d'un xarray.Dataset conforme CF."""

    def __init__(self, output_dir: str | Path = "data/output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def export(
        self,
        dataset: xr.Dataset,
        filename: str = "air_quality_observations.nc",
        complevel: int = 5,
    ) -> Path:
        """Sorte l'objet xarray.Dataset en fichier nc, compression zlib.

        Args:
            dataset: Le Dataset xarray construit par le NetCDFDatasetFactory.
            filename: Le nom du fichier de sortie (.nc).
            complevel: Niveau de compression zlib.

        Returns:
            Path: Le chemin absolu vers le fichier généré.
        """
        if not dataset.data_vars:
            print("Avertissement : xarray vide. Aucun fichier généré.")
            return self.output_dir / filename

        filepath = self.output_dir / filename

        # Options d'encodage et compression NetCDF4
        encoding = {}
        for var in dataset.data_vars:
            encoding[var] = {
                "zlib": True,
                "complevel": complevel,
                "shuffle": True,
            }

        try:
            # Écriture du fichier NetCDF4
            dataset.to_netcdf(
                filepath,
                format="NETCDF4",
                engine="netcdf4",
                encoding=encoding,
            )
            print(f"Export NetCDF-CF réussi : {filepath.resolve()}")
            return filepath

        except Exception as err:
            print(f"Erreur lors de l'export NetCDF ({filename}) : {err}")
            raise
