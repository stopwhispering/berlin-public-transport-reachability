import logging
from typing import Literal
import pickle  # noqa

from BerlinPublicTransportReachability.transport_api import BerlinTransportApi
from BerlinPublicTransportReachability.entities import Station, Destination

logger = logging.getLogger(__name__)


def fetch_api_data(destinations: list[str],
                   max_duration: int,
                   max_transfers: int,
                   time: Literal['next_sunday_early_morning', 'next_workday_noon']
                   ) -> tuple[list[dict], dict[str, list[dict]]]:
    bvg = BerlinTransportApi(max_duration=max_duration, time=time, max_transfers=max_transfers)
    destinations = [bvg.get_destination(d) for d in destinations]
    reachable_by_destinations = {}
    for destination in destinations:
        reachable = bvg.get_reachable_stops_from(destination)
        reachable_by_destinations[destination['name']] = reachable

    # with open("reachable_by_destinations.pkl", "wb") as f:
    #     pickle.dump(reachable_by_destinations, f)
    # with open("destinations.pkl", "wb") as f:
    #     pickle.dump(destinations, f)

    return destinations, reachable_by_destinations


def unserialize_stations(reachable_by_destinations: dict[str, list[dict]],
                         max_duration: int) -> list[Station]:
    reachable_stations = []
    # for each destination (that has a list of durations)
    for destination, durations in reachable_by_destinations.items():

        # each duration has a list of stations
        for stops_by_duration in durations:

            # for each station, create a Station instance or, if it already exists, add the duration to the
            # existing instance
            for stop in stops_by_duration['stations']:

                if (station := next((x for x in reachable_stations if x.name == stop['name']), None)) is None:
                    coordinates = (stop['location']['latitude'], stop['location']['longitude'])
                    station = Station(name=stop['name'],
                                      coordinates=coordinates,
                                      products=stop['products'], )
                    reachable_stations.append(station)
                station.add_duration(destination, stops_by_duration['duration'])

    # if a station lacks a connection to one of the destinations, add a duration of MAX_DURATION
    for station in reachable_stations:
        for destination in reachable_by_destinations.keys():
            if destination not in station.durations:
                station.add_duration_not_found(destination)

    # remove stations with an average duration > MAX_DURATION
    reachable_stations_in_time = [station for station in reachable_stations
                                  if station.get_weighted_duration() <= max_duration]
    logger.info(f'Found {len(reachable_stations_in_time)} reachable stations with average duration '
                f'up to {max_duration} minutes.')

    return reachable_stations_in_time


def unserialize_destinations(destinations_raw: list[dict]) -> list[Destination]:
    destinations = []
    for destination_raw in destinations_raw:
        coordinates = destination_raw['location']['latitude'], destination_raw['location']['longitude']
        destination = Destination(name=destination_raw['name'],
                                  coordinates=coordinates,
                                  products=destination_raw['products'])
        destinations.append(destination)
    return destinations
