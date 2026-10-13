# main.py
import os
from src.services.client import OpenAQClient
from src.services.repository import StationRepository
from src.export.dataset_factory import NetCDFDatasetFactory
from src.export.netcdf_exporter import NetCDFExporter
from src.export.visualizer import AirQualityAnimator

API_KEY = os.getenv("OPENAQ_API_KEY")
BBOX = (-0.26122, 51.38494, -0.136122, 51.548494)

# Setup
repo = StationRepository(client=OpenAQClient(API_KEY), max_workers=1)

# Pipeline ETL
stations = repo.get_hydrated_stations(BBOX, force_refresh=True)  # Extract + Hydrate

# 2. Transformation vers le standard scientifique (Gold XArray)
dataset = NetCDFDatasetFactory.create_from_collection(stations, freq="1D")

# 3. Export physique sur disque
exporter = NetCDFExporter(output_dir="data/output")
output_nc = exporter.export(dataset, filename="openaq_londres_2026.nc")

# Génération du GIF animé pour le NO2 ou PM2.5
animator = AirQualityAnimator(output_nc)
animator.create_animation(
    variable="no2",
    output_gif="data/output/no2_london_evolution.gif",
    fps=2  # 2 images par seconde
)