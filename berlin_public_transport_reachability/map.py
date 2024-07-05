import webbrowser

import folium
from folium import Popup

from berlin_public_transport_reachability.entities import Destination
from berlin_public_transport_reachability.ortsteil import Ortsteil
from berlin_public_transport_reachability.station import Station

# Example Latitudes/Longitudes:
# Berlin
# 52.520008, 13.404954
# S+U Alexanderplatz
# 52.521512, 13.411267
# U Mehringdamm
# 52.493567, 13.38814
# U Nollendorfplatz
# 52.499644, 13.353825


class ReachableMap:
    """Draw a map with the given destinations as markers and the given stations as circles"""

    def __init__(
        self,
        destinations: list[Destination],
        stations: list[Station],
        circle_radius: int,
    ):
        self.destinations = destinations
        self.reachable_stations = stations
        self.circle_radius = circle_radius  # in meters
        self.folium_map = self._draw_base_map()

    def draw_reachable_stations(self) -> None:
        """Draw the map with the given destinations as markers and the given stations as circles"""
        self._draw_base_map()
        self._draw_reachable_stops()
        self.folium_map.save("index.html")
        webbrowser.open("index.html")

    def draw_ortsteile(self, ortsteile: list[Ortsteil]) -> None:
        self._draw_base_map()
        self._draw_ortsteile(ortsteile=ortsteile)
        self.folium_map.save("index.html")
        webbrowser.open("index.html")

    def _draw_reachable_stops(self) -> None:
        """Draw the reachable stops as circles on the map"""
        station_circles = []

        # sort stations from green to red to avoid green being overwritten
        # by red
        self.reachable_stations.sort(
            key=lambda x: x.get_weighted_duration(), reverse=True
        )

        for station in self.reachable_stations:
            coordinates = station.coordinates
            station_circle = folium.Circle(
                radius=self.circle_radius,
                location=coordinates,
                popup=Popup(station.get_popup_text(), max_width=400),
                color=station.get_color(),
                fill=True,
                # fill_color="green",
                stroke=False,
                # opacity=1.0,
                fill_opacity=1.0,
            )
            station_circles.append(station_circle)

        for station_circle in station_circles:
            station_circle.add_to(self.folium_map)

        # we need a div around each circle setting opacity to avoid
        # overlaying circles being displayed darker
        div = folium.Element(
            """
            <style>
            g {
              opacity: 0.5;
            }
            </style>
                    """
        )

        self.folium_map.get_root().html.add_child(div)

    def _get_center_of_destinations(self) -> tuple[float, float]:
        """Determine the geographical center of the destinations"""
        latitudes = [destination.location.latitude for destination in self.destinations]
        longitudes = [
            destination.location.longitude for destination in self.destinations
        ]
        return sum(latitudes) / len(latitudes), sum(longitudes) / len(longitudes)

    def _draw_base_map(self) -> folium.Map:
        """Draw the base map with the given locations as markers"""
        folium_map = folium.Map(
            location=self._get_center_of_destinations(),
            zoom_start=12,
            control_scale=True,
            # tiles='Stamen Toner'  # make it monochrome
        )
        for destination in self.destinations:
            folium.Marker(
                location=(
                    destination.location.latitude,
                    destination.location.longitude,
                ),
                popup=destination.name,
                icon=folium.Icon(
                    color="blue", icon="subway", prefix="fa"
                ),  # https://fontawesome.com/v4/icons/
            ).add_to(folium_map)

        return folium_map

    def _draw_ortsteile(self, ortsteile: list[Ortsteil]) -> None:
        """Draw the ortsteile as polygons from geojson file on the map"""
        fields = [
            "OTEIL",
            "BEZIRK",
            "average_duration",
            "min_duration",
            "max_duration",
            "count_stations",
        ]
        aliases = [
            "Ortsteil",
            "Bezirk",
            "Weighted Average Duration",
            "Min. Duration",
            "Max. Duration",
            "Count Stations",
        ]
        for ortsteil in ortsteile:
            geojson = folium.GeoJson(
                ortsteil.feature,
                style_function=ortsteil.get_style,
                tooltip=folium.features.GeoJsonTooltip(
                    fields=fields,
                    aliases=aliases,
                ),
            )
            geojson.add_to(self.folium_map)
