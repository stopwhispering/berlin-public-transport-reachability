from typing import TypedDict

from colour import Color
from pydantic import BaseModel

from berlin_public_transport_reachability.settings import settings

color_map = tuple(
    Color("green").range_to(Color("red"), settings.general.max_duration)  #  * 2)
)  # n steps from green to red


class GeoProperties(TypedDict):
    OTEIL: str
    BEZIRK: str
    FLAECHE_HA: float
    spatial_alias: str

    average_duration: int | None
    min_duration: int | None
    max_duration: int | None
    count_stations: int | None


class GeoGeometry(TypedDict):
    type: str  # noqa: A003


class GeoFeature(TypedDict):
    type: str  # noqa: A003
    properties: GeoProperties
    geometry: GeoGeometry
    product_codes: list[str]


abbreviation_map = {
    "suburban": "S",
    "subway": "U",
    "tram": "T",
    "bus": "B",
    "ferry": "F",
    "express": "RE",
    "regional": "RB",
}


class DestinationProducts(BaseModel):
    suburban: bool  # S-Bahn
    subway: bool  # U-Bahn
    tram: bool
    bus: bool
    ferry: bool
    express: bool  # RE
    regional: bool  # RB

    def __repr__(self) -> str:
        return (
            f"DestinationProducts({self.suburban=}, {self.subway=}, {self.tram=}, "
            f"{self.bus=}, {self.ferry=}, {self.express=}, {self.regional=})"
        )

    def as_list(self) -> list[str]:
        return [abbreviation_map[k] for k, v in self.dict().items() if v]


class DestinationLocation(BaseModel):
    latitude: float  # e.g. 52.521508
    longitude: float


class Destination(BaseModel):
    """A destination is a point of interest with a name and coordinates. This is where we are
    getting the reachable stations for."""

    name: str
    location: DestinationLocation
    products: DestinationProducts

    def __repr__(self) -> str:
        return f"Destination(name={self.name})"

    @property
    def coordinates(self) -> tuple[float, float]:
        return self.location.latitude, self.location.longitude


class ReachableInMinutes(BaseModel):
    duration: int
    stations: list[Destination]
