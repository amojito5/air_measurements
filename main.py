# main.py
import os
from src.services.client import OpenAQClient
from src.services.repository import StationRepository

API_KEY = os.getenv("OPENAQ_API_KEY")
BBOX = (-0.26122, 51.38494, -0.136122, 51.548494)

# Setup
repo = StationRepository(client=OpenAQClient(API_KEY), max_workers=1)

# Pipeline ETL
stations = repo.get_hydrated_stations(BBOX, force_refresh=False)  # Extract + Hydrate
