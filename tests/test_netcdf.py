from pathlib import Path
import numpy as np
import pytest
import xarray as xr

from export.netcdf_exporter import NetCDFExporter


@pytest.fixture
def dummy_dataset():
    """Fixture Pytest pour créer un faux Dataset xarray valide pour les tests."""
    # Création d'un dataset simple avec une variable (ex: concentration de polluant)
    data = np.array([10.5, 12.0, 15.2])
    ds = xr.Dataset(
        {"pm25": (["time"], data)},
        coords={
            "time": np.array([1, 2, 3]),
            "lat": 48.85,
            "lon": 2.35,
        },
    )
    ds.attrs["Conventions"] = "CF-1.8"
    return ds


def test_netcdf_exporter_creates_file(tmp_path, dummy_dataset):
    """Vérifie que l'exporteur crée bien un fichier NetCDF physique sur le disque."""
    # tmp_path est une fixture intégrée à pytest qui crée un dossier temporaire propre
    exporter = NetCDFExporter(output_dir=tmp_path)
    
    filename = "test_output.nc"
    output_path = exporter.export(dummy_dataset, filename=filename)

    # 1. Vérifie que le fichier existe bien
    assert output_path.exists()
    assert output_path.is_file()

    # 2. Vérifie qu'on peut le recharger avec xarray et que la donnée est intacte
    with xr.open_dataset(output_path) as loaded_ds:
        assert "pm25" in loaded_ds.data_vars
        assert "time" in loaded_ds.dims
        # Vérifie que la valeur correspond
        np.testing.assert_array_equal(loaded_ds["pm25"].values, [10.5, 12.0, 15.2])


def test_netcdf_exporter_empty_dataset_handles_gracefully(tmp_path):
    """Vérifie le comportement si le dataset est vide (pas de variables de données)."""
    exporter = NetCDFExporter(output_dir=tmp_path)
    empty_ds = xr.Dataset()

    output_path = exporter.export(empty_ds, filename="empty.nc")
    
    # L'exporteur doit retourner le chemin sans planter, mais ne pas créer de fichier NetCDF lourd
    assert output_path == tmp_path / "empty.nc"
