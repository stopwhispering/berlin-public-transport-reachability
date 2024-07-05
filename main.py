import logging
from argparse import ArgumentParser
from pathlib import Path
from typing import Literal

import requests_cache

from berlin_public_transport_reachability.entities import (
    Destination,
    ReachableInMinutes,
)
from berlin_public_transport_reachability.fetch import (
    fetch_api_data,
    load_ortsteile,
    unserialize_stations,
)
from berlin_public_transport_reachability.map import ReachableMap
from berlin_public_transport_reachability.settings import settings

logging.basicConfig(level=logging.INFO, force=True)
logging.getLogger("urllib3.connectionpool").setLevel(logging.WARNING)
logging.getLogger("requests_cache").setLevel(logging.INFO)
logger = logging.getLogger(__name__)

requests_cache.install_cache(
    "test_cache", backend="sqlite", expire_after=2592000
)  # 30 days


def parse_action() -> Literal["stations", "districts"]:
    parser = ArgumentParser()
    parser.add_argument(
        "-a",
        "--action",
        help="Set action to 'stations' (default) or 'districts'",
        default="stations",
        choices=["stations", "districts"],
    )
    return parser.parse_args().action  # type: ignore[no-any-return]


if __name__ == "__main__":
    destinations: list[Destination]
    reachable_by_destinations: dict[str, list[ReachableInMinutes]]
    destinations, reachable_by_destinations = fetch_api_data(
        destinations=settings.destination.destinations,
        max_duration=settings.general.max_duration + 60,
        max_transfers=settings.destination.max_transfers,
        time=settings.destination.time,
    )

    # destinations = unserialize_destinations(destinations_raw=destinations_raw)
    stations = unserialize_stations(
        reachable_by_destinations=reachable_by_destinations,
        max_duration=settings.general.max_duration,
    )

    # depending on cli argument, draw either stations or districts
    if (action := parse_action()) == "stations":
        logger.info("Drawing Stations")
        ReachableMap(
            destinations=destinations,
            stations=stations,
            circle_radius=settings.general.circle_radius,
        ).draw_reachable_stations()
    elif action == "districts":
        logger.info("Drawing Districts")
        ortsteile = load_ortsteile(
            path=Path("./static/lor_ortsteile.geojson"), stations=stations
        )
        ReachableMap(
            destinations=destinations,
            stations=stations,
            circle_radius=settings.general.circle_radius,
        ).draw_ortsteile(ortsteile=ortsteile)
