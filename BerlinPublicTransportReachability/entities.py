from math import ceil

from colour import Color
from shapely.geometry import shape, Point

from settings import MAX_DURATION

color_map = tuple(Color("green").range_to(Color("red"), MAX_DURATION))  # n steps from green to red


class Destination:
    """A destination is a point of interest with a name and coordinates. This is where we are getting
    the reachable stations for."""
    def __init__(self, name: str, coordinates: tuple[float, float], products: dict):
        self.name = name
        self.coordinates = coordinates
        self.products = products

    def __repr__(self):
        return f'Destination(name={self.name})'


class Station:
    """Bus/Tram/Subway/Regional Station with coordinates and durations to destinations"""
    def __init__(self, name: str, coordinates: tuple[float, float], products: dict):
        self.name = name
        self.coordinates = coordinates
        self.products = products
        self.durations: dict[str, int] = {}

    def get_coordinates(self, latitude_first=True) -> tuple[float, float]:
        """Return the coordinates of the station"""
        return self.coordinates if latitude_first else self.coordinates[::-1]

    def __repr__(self):
        return f'Station({self.name})'

    def get_weighted_duration(self) -> int:
        """Return the duration to the station weighted by the number of destinations"""
        return int(sum(self.durations.values()) / len(self.durations))

    def get_color(self) -> str:
        """Return a color based on the duration to the station as hex string"""
        duration = self.get_weighted_duration()
        return color_map[duration - 1].get_hex()

    def get_popup_text(self) -> str:
        """Return a string with the station name and durations to destinations in pseudo-html"""
        popup = f"{self.name}<br><br>"
        for key, value in self.durations.items():
            popup += f"{key}: {value} min<br>"
        popup += f"Average: {self.get_weighted_duration()} min"
        return popup

    def add_duration_not_found(self, destination: str):
        """Add a duration of MAX_DURATION*2 to a specific destination to the station that was
        not found.
        However, there seems to be a bug with some central bus stations not being found; we add
        average current duration there"""
        if len(self.durations) >= 1 and self.get_weighted_duration() < 20:
            self.durations[destination] = self.get_weighted_duration()
        else:
            self.durations[destination] = MAX_DURATION*2

    def add_duration(self, destination: str, duration: int):
        """Add a duration to a specific destination to the station"""
        # we may receive durations for the same destination multiple times
        # we only want to keep the shortest duration
        if destination in self.durations:
            self.durations[destination] = min(self.durations[destination], duration)
        else:
            self.durations[destination] = duration


class Ortsteil:
    def __init__(self, geojson_feature: dict[str, any]):
        self.alias = geojson_feature["properties"]["spatial_alias"]
        self.ortsteil = geojson_feature["properties"]["OTEIL"]
        self.bezirk = geojson_feature["properties"]["BEZIRK"]
        self.area = geojson_feature["properties"]["FLAECHE_HA"]  # in hectar

        assert geojson_feature["geometry"]["type"] in {"Polygon", "MultiPolygon"}
        # self.geometry = geojson_feature["geometry"]
        self.feature = geojson_feature
        self.shape = shape(geojson_feature["geometry"])

        self.stations: list[Station] = []
        self.average_duration: int | None = None

    def __repr__(self):
        return f'Ortsteil({self.ortsteil} in {self.bezirk})'

    def contains_station(self, station: Station) -> bool:
        return self.shape.contains(Point(station.get_coordinates(latitude_first=False)))

    def add_station(self, station: Station):
        self.stations.append(station)

    def calculate_average_duration(self):
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

    def get_style(self, feature):  # noqa
        """Return a color based on the average duration to the station as hex string"""
        if self.average_duration is None:
            color = "#000000"
        else:
            color = color_map[self.average_duration - 1].get_hex()
        return {
            'fillColor': color,
            'fillOpacity': 0.5,
            # 'color': 'gray',  # border color
            # 'weight': 1  # border width
        }
