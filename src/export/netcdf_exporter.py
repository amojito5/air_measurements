# src/export/netcdf_exporter.py
from pathlib import Path
from typing import Optional
import xarray as xr


class NetCDFExporter:
    """Gère la persistance physique d'un xarray.Dataset au format NetCDF4 conforme CF."""

    def __init__(self, output_dir: str | Path = "data/output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def export(
        self,
        dataset: xr.Dataset,
        filename: str = "air_quality_observations.nc",
        complevel: int = 5,
    ) -> Path:
        """Sorte l'objet xarray.Dataset en fichier NetCDF4 avec compression zlib.

        Args:
            dataset: Le Dataset xarray construit par le NetCDFDatasetFactory.
            filename: Le nom du fichier de sortie (.nc).
            complevel: Niveau de compression zlib (1-9, 5 est le compromis optimal speed/size).

        Returns:
            Path: Le chemin absolu vers le fichier généré.
        """
        if not dataset.data_vars:
            print("Avertissement : Le Dataset xarray est vide. Aucun fichier généré.")
            return self.output_dir / filename

        filepath = self.output_dir / filename

        # Options d'encodage et compression NetCDF4 pour chaque variable de données
        encoding = {}
        for var in dataset.data_vars:
            encoding[var] = {
                "zlib": True,
                "complevel": complevel,
                "shuffle": True,  # Améliore le taux de compression pour les arrays numériques
            }

        try:
            # Écriture du fichier NetCDF4
            dataset.to_netcdf(
                filepath,
                format="NETCDF4",
                engine="netcdf4",
                encoding=encoding,
            )
            print(f"📦 Export NetCDF-CF réussi : {filepath.resolve()}")
            return filepath

        except Exception as err:
            print(f"❌ Erreur lors de l'export NetCDF ({filename}) : {err}")
            raise err
