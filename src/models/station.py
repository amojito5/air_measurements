# src/models/station.py
from dataclasses import asdict, dataclass
from typing import Any


@dataclass
class SensorParams:
    id: int
    name: str
    units: str

    @classmethod
    def from_dict(cls, params: dict[str, Any]) -> "SensorParams":
        return cls(id=params["id"], name=params["name"], units=params["units"])


@dataclass
class Sensor:
    id: int
    name: str
    parameter: dict[str, Any]  # Ex: {"id": 5, "name": "no2", "units": "µg/m³"}
    averages: list[dict[str, Any]] | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Sensor":
        return cls(
            id=data["id"],
            name=data.get("name", ""),
            parameter=data.get("parameter", {}),
            averages=data.get("averages"),
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
        """Return ids of all stations."""
        return [station.id for station in self.stations]

    @property
    def sensor_ids(self) -> list[int]:
        """Return ids list of all sensors of all stations."""
        return [
            sensor.id
            for station in self.stations
            for sensor in station.sensors
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

    def set_averages_bulk(self, averages_map: dict[int, list[dict]]):
        for station in self.stations:
            for sensor in station.sensors:
                if sensor.id in averages_map:
                    sensor.averages = averages_map[sensor.id]

    def to_dict(self) -> dict[str, Any]:
        """Dict toJSON-compatible convresion"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "StationCollection":
        """Build StationCollection with means from cached dict"""
        return cls(stations=[Station.from_dict(s) for s in data["stations"]])
