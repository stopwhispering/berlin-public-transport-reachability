from colour import Color

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
