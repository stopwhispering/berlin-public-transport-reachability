import json
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

    from berlin_public_transport_reachability.entities import (
        Destination,
        GeoFeature,
        ReachableInMinutes,
    )
    from berlin_public_transport_reachability.enums import TimeValue

from berlin_public_transport_reachability.ortsteil import Ortsteil
from berlin_public_transport_reachability.station import Station
from berlin_public_transport_reachability.transport_api import BerlinTransportApi

logger = logging.getLogger(__name__)


def fetch_api_data(
    destinations: list[str],
    max_duration: int,
    max_transfers: int,
    time: TimeValue,
) -> tuple[list[Destination], dict[str, list[ReachableInMinutes]]]:
    """fetch the data from the transport api and return the raw data"""
    bvg = BerlinTransportApi(
        max_duration=max_duration, time=time, max_transfers=max_transfers
    )
    destinations_: list[Destination] = [bvg.get_destination(d) for d in destinations]
    reachable_by_destinations = {}
    for destination in destinations_:
        reachable = bvg.get_reachable_stops_from(destination)
        reachable_by_destinations[destination.name] = reachable

    return destinations_, reachable_by_destinations


def unserialize_stations(
    reachable_by_destinations: dict[str, list[ReachableInMinutes]], max_duration: int
) -> list[Station]:
    """unserialize the stations from the raw data"""
    reachable_stations: list[Station] = []
    # for each destination (that has a list of durations)
    for destination, durations in reachable_by_destinations.items():
        # each duration has a list of stations
        for stops_by_duration in durations:
            # for each station, create a Station instance or, if it already exists, add the
            # duration to the existing instance
            for stop in stops_by_duration.stations:  # ["stations"]:
                if (
                    station := next(
                        (x for x in reachable_stations if x.name == stop.name), None
                    )
                ) is None:
                    coordinates = stop.coordinates
                    station = Station(
                        name=stop.name,
                        coordinates=coordinates,
                        products=stop.products,
                    )
                    reachable_stations.append(station)
                station.add_duration(destination, stops_by_duration.duration)

    # if a station lacks a connection to one of the destinations, add a duration of MAX_DURATION
    for station in reachable_stations:
        for destination in reachable_by_destinations:
            if destination not in station.durations:
                station.add_duration_not_found(destination)

    # remove stations with an average duration > MAX_DURATION
    reachable_stations_in_time = [
        station
        for station in reachable_stations
        if station.get_weighted_duration() <= max_duration
    ]
    logger.info(
        f"Found {len(reachable_stations_in_time)} reachable stations with average duration "
        f"up to {max_duration} minutes."
    )

    return reachable_stations_in_time


def load_ortsteile(path: Path, stations: list[Station]) -> list[Ortsteil]:
    """load the geojson file with the ortsteile and add the reachable stations to each ortsteil"""
    with path.open(encoding="utf-8") as file:
        features: list[GeoFeature] = json.load(file)["features"]
    ortsteile = [Ortsteil(f) for f in features]

    for station in stations:
        found = False
        for ortsteil in ortsteile:
            if ortsteil.contains_station(station=station):
                ortsteil.add_station(station)
                found = True
        if not found:
            logger.debug(f"Station {station.name} not found in any Ortsteil")

    # we need to calculate the average duration for each ortsteil as it must be stored at specific
    # position for the folium/leaflet geojson tooltip
    for ortsteil in ortsteile:
        ortsteil.calculate_average_duration()

    return ortsteile
