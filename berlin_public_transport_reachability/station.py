from typing import Any

from berlin_public_transport_reachability.entities import DestinationProducts, color_map
from berlin_public_transport_reachability.settings import settings


class Station:
    """Bus/Tram/Subway/Regional Station with coordinates and durations to destinations"""

    def __init__(
        self, name: str, coordinates: tuple[float, float], products: DestinationProducts
    ):
        self.name = name
        self.coordinates = coordinates
        self.products: DestinationProducts = products
        self.durations: dict[str, int] = {}

    def get_coordinates(self, *, latitude_first: bool = True) -> tuple[float, float]:
        """Return the coordinates of the station"""
        return self.coordinates if latitude_first else self.coordinates[::-1]

    def __repr__(self) -> str:
        return f"Station({self.name})"

    def get_weighted_duration(self) -> int:
        """Return the duration to the station weighted by the number of destinations"""
        return int(sum(self.durations.values()) / len(self.durations))

    def get_color(self) -> Any:
        """Return a color based on the duration to the station as hex string"""
        duration = self.get_weighted_duration()
        return color_map[duration - 1].get_hex()

    def get_popup_text(self) -> str:
        """Return a string with the station name and durations to destinations in pseudo-html"""
        popup = f"{self.name}<br>{','.join(self.products.as_list())}<br><br>"
        for key, value in self.durations.items():
            popup += f"{key}: {value} min<br>"
        popup += f"Average: {self.get_weighted_duration()} min"
        return popup

    def add_duration_not_found(self, destination: str) -> None:
        """Add a duration of MAX_DURATION*2 to a specific destination to the station that was
        not found.
        However, there seems to be a bug with some central bus stations not being found; we add
        average current duration there"""
        if len(self.durations) >= 1 and self.get_weighted_duration() < 20:
            self.durations[destination] = self.get_weighted_duration()
        else:
            self.durations[destination] = settings.general.max_duration * 2

    def add_duration(self, destination: str, duration: int) -> None:
        """Add a duration to a specific destination to the station"""
        # we may receive durations for the same destination multiple times
        # we only want to keep the shortest duration
        if destination in self.durations:
            self.durations[destination] = min(self.durations[destination], duration)
        else:
            self.durations[destination] = duration
