from pathlib import Path

from BerlinPublicTransportReachability.fetch import fetch_api_data, unserialize_stations, unserialize_destinations, \
    load_ortsteile
from BerlinPublicTransportReachability.map import ReachableMap
import pickle  # noqa
import logging

from settings import DESTINATIONS, CIRCLE_RADIUS, TIME, MAX_DURATION, MAX_TRANSFERS

logging.basicConfig(level=logging.DEBUG, force=True)
logging.getLogger('urllib3.connectionpool').setLevel(logging.WARNING)

if __name__ == '__main__':
    destinations_raw, reachable_by_destinations = fetch_api_data(destinations=DESTINATIONS,
                                                                 max_duration=MAX_DURATION + 60,
                                                                 max_transfers=MAX_TRANSFERS,
                                                                 time=TIME)
    # with open("reachable_by_destinations.pkl", "rb") as f:
    #     reachable_by_destinations = pickle.load(f)
    # with open("destinations.pkl", "rb") as f:
    #     destinations_raw = pickle.load(f)

    destinations = unserialize_destinations(destinations_raw=destinations_raw)
    stations = unserialize_stations(reachable_by_destinations=reachable_by_destinations,
                                    max_duration=MAX_DURATION)
    ortsteile = load_ortsteile(path=Path('./static/lor_ortsteile.geojson'), stations=stations)

    ReachableMap(destinations=destinations, stations=stations, circle_radius=CIRCLE_RADIUS).draw_reachable_stations()
    ReachableMap(destinations=destinations, stations=stations, circle_radius=CIRCLE_RADIUS).draw_ortsteile(
        ortsteile=ortsteile)
