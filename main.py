import logging
import os

from src.config import load_config
from src.export.dataset_factory import NetCDFDatasetFactory
from src.export.netcdf_exporter import NetCDFExporter
from src.export.visualizer import AirQualityAnimator
from src.services.client import OpenAQClient
from src.services.repository import StationRepository

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

env_name = os.getenv("ENV_NAME", "paris")
config = load_config(env_name)

API_KEY = os.getenv("OPENAQ_API_KEY")

site_name = config["area"]["name"]
bbox = tuple(config["area"]["bbox"])
max_workers = config["runtime"]["max_workers"]
api_limit = config.get("api", {}).get("limit", 1000)
api_timeout = config.get("api", {}).get("timeout", 20)

logger.info(
        "Démarrage du pipeline pour la zone : [%s] %s",
        env_name.upper(), site_name
        )

client = OpenAQClient(API_KEY, timeout=api_timeout, default_limit=api_limit)
repo = StationRepository(
    client=OpenAQClient(API_KEY, timeout=api_timeout),
    max_workers=max_workers
)
stations = repo.get_hydrated_stations(bbox, force_refresh=False)

dataset = NetCDFDatasetFactory.create_from_collection(stations, freq="1D")

exporter = NetCDFExporter(output_dir="data/output")
output_nc = exporter.export(dataset, filename=f"openaq_{env_name}_2026.nc")

animator = AirQualityAnimator(output_nc)
animator.create_animation(
    variable="no2",
    output_gif=f"data/output/no2_{env_name}_evolution.gif",
    fps=2,
)
