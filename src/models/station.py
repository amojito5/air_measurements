# src/models/station.py
from dataclasses import asdict, dataclass
from typing import Any, Optional


@dataclass
class SensorParams:
    id: int
    name: str
    units: str

    @classmethod
    def from_dict(cls, params: dict[str, Any]) -> "SensorParams":
        return cls(
            id=params["id"], name=params["name"], units=params["units"]
        )


@dataclass
class Sensor:
    id: int
    name: str
    parameter: SensorParams
    averages: Optional[list[float]] = None

    @classmethod
    def from_dict(cls, attributes: dict[str, Any]) -> "Sensor":
        return cls(
            id=attributes["id"],
            name=attributes["name"],
            parameter=SensorParams.from_dict(attributes["parameter"]),
            averages=attributes.get("averages"),
        )


@dataclass
class Station:
    id: int
    name: str
    coordinates: dict[str, float]
    sensors: list[Sensor]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Station":
        return cls(
            id=data["id"],
            name=data.get("name", "Inconnue"),
            coordinates=data["coordinates"],
            sensors=[Sensor.from_dict(s) for s in data["sensors"]],
        )


@dataclass
class StationCollection:
    stations: list[Station]

    @classmethod
    def from_openaq_list(
        cls, raw_list: list[dict[str, Any]]
    ) -> "StationCollection":
        return cls(stations=[Station.from_dict(item) for item in raw_list])

    @property
    def station_ids(self) -> list[int]:
        """Retourne la liste de tous les IDs de stations."""
        return [station.id for station in self.stations]

    @property
    def sensor_ids(self) -> list[int]:
        """Retourne la liste de tous les IDs de capteurs de toutes les stations."""
        return [
            sensor.id for station in self.stations for sensor in station.sensors
        ]

    def set_averages(self, id: int, values: list[float]) -> None:
        """Met à jour les moyennes d'un seul capteur."""
        sensor_map = {
            sensor.id: sensor
            for station in self.stations
            for sensor in station.sensors
        }
        if id in sensor_map:
            sensor_map[id].averages = values

    def set_averages_bulk(self, averages_map: dict[int, list[float]]) -> None:
        """Met à jour les moyennes de plusieurs capteurs en une seule passe."""
        sensor_map = {
            sensor.id: sensor
            for station in self.stations
            for sensor in station.sensors
        }
        for sensor_id, values in averages_map.items():
            if sensor_id in sensor_map:
                sensor_map[sensor_id].averages = values

    # --- SÉRIALISATION POUR LE CACHE ---
    def to_dict(self) -> dict[str, Any]:
        """Convertit l'intégralité de la collection en dictionnaire JSON-compatible."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "StationCollection":
        """Reconstruit une StationCollection (avec ses moyennes) depuis un dictionnaire de cache."""
        return cls(stations=[Station.from_dict(s) for s in data["stations"]])