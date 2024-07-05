from math import ceil
from typing import Any

from shapely import Point
from shapely.geometry import shape

from berlin_public_transport_reachability.entities import GeoFeature, color_map
from berlin_public_transport_reachability.station import Station


class Ortsteil:  # pylint: disable=too-many-instance-attributes
    def __init__(self, geojson_feature: GeoFeature):
        self.alias = geojson_feature["properties"]["spatial_alias"]
        self.ortsteil = geojson_feature["properties"]["OTEIL"]
        self.bezirk = geojson_feature["properties"]["BEZIRK"]
        self.area = geojson_feature["properties"]["FLAECHE_HA"]  # in hectar

        if geojson_feature["geometry"]["type"] not in {"Polygon", "MultiPolygon"}:
            raise ValueError
        # self.geometry = geojson_feature["geometry"]
        self.feature: GeoFeature = geojson_feature
        self.shape = shape(geojson_feature["geometry"])

        self.stations: list[Station] = []
        self.average_duration: int | None = None

    def __repr__(self) -> str:
        return f"Ortsteil({self.ortsteil} in {self.bezirk})"

    def contains_station(self, station: Station) -> bool:
        return bool(
            self.shape.contains(Point(station.get_coordinates(latitude_first=False)))
        )

    def add_station(self, station: Station) -> None:
        self.stations.append(station)

    def calculate_average_duration(self) -> None:
        """Calculate the average duration to the station"""
        durations = [station.get_weighted_duration() for station in self.stations]
        if len(durations) == 0:
            self.average_duration = None
            min_duration = None
            max_duration = None
            count_stations = 0
        else:
            # we use a weighted average: only the best 10% of stations are considered
            count_n = ceil(len(durations) * 0.1)
            top_n = sorted(durations)[:count_n]
            self.average_duration = int(sum(top_n) / len(top_n))
            min_duration = min(durations)
            max_duration = max(durations)
            count_stations = len(durations)
        self.feature["properties"]["average_duration"] = self.average_duration
        self.feature["properties"]["min_duration"] = min_duration
        self.feature["properties"]["max_duration"] = max_duration
        self.feature["properties"]["count_stations"] = count_stations

    def get_style(
        self, feature: Any  # noqa: ARG002  # pylint: disable=unused-argument
    ) -> dict[str, Any]:
        """Return a color based on the average duration to the station as hex string"""
        if self.average_duration is None:
            color = "#000000"
        else:
            color = color_map[self.average_duration - 1].get_hex()
        return {
            "fillColor": color,
            "fillOpacity": 0.5,
            # 'color': 'gray',  # border color
            # 'weight': 1  # border width
        }
