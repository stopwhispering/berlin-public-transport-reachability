import requests_cache

from berlin_public_transport_reachability.journey_finder import (
    Journey,
    fetch_quickest_journey,
)
from berlin_public_transport_reachability.settings import settings

# origin_address = "Neukölln, Berlin"
# origin_address = "Steglitz, Berlin"
origin_address = "Berlin - Dahlem"
# destination_address = "Mehringdamm, Berlin"

requests_cache.install_cache(
    "test_cache", backend="sqlite", expire_after=2592000
)  # 30 days

for dest in settings.destination.destinations:
    destination_address = dest + ", Berlin"
    # print_journeys(origin_address, destination_address)
    journey: Journey = fetch_quickest_journey(origin_address, destination_address)
    print(journey)
