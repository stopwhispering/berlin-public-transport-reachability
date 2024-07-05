import datetime
from dataclasses import dataclass
from typing import Literal, NotRequired, TypedDict

import requests

from berlin_public_transport_reachability.coordinates_finder import (
    Location,
    get_coordinates_by_addresss,
)
from berlin_public_transport_reachability.entities import abbreviation_map


class ProductsResponse(TypedDict):
    suburban: bool
    subway: bool
    tram: bool
    bus: bool
    ferry: bool
    express: bool
    regional: bool


def products_to_string(products: ProductsResponse) -> str:
    """Convert list of products to string"""
    abbreviations = [abbreviation_map[k] for k, v in products.items() if v]
    return ", ".join(abbreviations)


class OriginDestinationResponse(TypedDict):
    type: Literal["stop", "location"]  # noqa: A003
    name: NotRequired[str]
    address: NotRequired[str]
    poi: NotRequired[bool]
    products: NotRequired[ProductsResponse]


class LegResponse(TypedDict):
    origin: OriginDestinationResponse
    destination: OriginDestinationResponse
    departure: str  # ISO 8601, e.g. '2023-05-18T15:10:00+02:00'
    arrival: str  # ISO 8601
    walking: NotRequired[bool]
    distance: NotRequired[int]


class JourneyResponse(TypedDict):
    legs: list[LegResponse]


class ResultsResponse(TypedDict):
    journeys: list[JourneyResponse]


def fetch_journeys(
    location_origin: Location, location_destination: Location
) -> list[JourneyResponse]:
    params = {
        "from.latitude": location_origin.latitude,
        "from.longitude": location_origin.longitude,
        "from.address": location_origin.address,
        "to.latitude": location_destination.latitude,
        "to.longitude": location_destination.longitude,
        "to.address": location_destination.address,
    }
    url = "https://v5.bvg.transport.rest/journeys"
    response = requests.get(url, params=params, timeout=15)
    results: ResultsResponse = response.json()
    if "journeys" not in results:
        raise ValueError(
            f"No journeys found from {location_origin} to {location_destination}"
        )
    return results["journeys"]


@dataclass
class Journey:
    origin_address: str
    destination_address: str
    departure: datetime.datetime
    arrival: datetime.datetime
    duration: datetime.timedelta
    count_stopvers: int

    def __str__(self) -> str:
        return (
            f"Journey from {self.origin_address} to {self.destination_address}:\n"
            f"Departure: {self.departure}\n"
            f"Arrival: {self.arrival}\n"
            f"Duration: {self.duration}\n"
            f"Stopvers: {self.count_stopvers}\n"
        )


def parse_journey(journey: JourneyResponse) -> Journey:
    legs: list[LegResponse] = journey["legs"]
    legs = [leg for leg in legs if not (leg.get("walking") and leg["distance"] < 800)]

    departure = datetime.datetime.fromisoformat(legs[0]["departure"])
    arrival = datetime.datetime.fromisoformat(legs[-1]["arrival"])
    duration = arrival - departure

    origin_address = legs[0]["origin"].get("name") or legs[0]["origin"].get("address")
    if not origin_address:
        raise ValueError(f"Could not find origin address for {journey}")
    destination_address = (
        legs[-1]["destination"].get("name") or legs[-1]["destination"]["address"]
    )
    count_stopvers = len(legs) - 1

    return Journey(
        origin_address=origin_address,
        destination_address=destination_address,
        departure=departure,
        arrival=arrival,
        duration=duration,
        count_stopvers=count_stopvers,
    )


def fetch_quickest_journey(origin_address: str, destination_address: str) -> Journey:
    location_origin: Location = get_coordinates_by_addresss(origin_address)
    location_destination: Location = get_coordinates_by_addresss(destination_address)
    journey_responses = fetch_journeys(location_origin, location_destination)
    journeys: list[Journey] = []
    for journey_response in journey_responses:
        parsed_journey = parse_journey(journey_response)
        journeys.append(parsed_journey)
    return min(journeys, key=lambda j: j.duration)


def print_journeys(origin_address: str, destination_address: str) -> None:
    location_origin: Location = get_coordinates_by_addresss(origin_address)
    location_destination: Location = get_coordinates_by_addresss(destination_address)
    journeys = fetch_journeys(location_origin, location_destination)

    print(f"{len(journeys)} journeys")
    durations: list[datetime.timedelta] = []
    for journey in journeys:
        legs = journey["legs"]
        print(f"{len(legs)} legs")

        if not legs:
            raise ValueError(f"No legs found for journey: {journey}")

        for leg in legs:
            departure: datetime.datetime = datetime.datetime.fromisoformat(
                leg["departure"]
            )
            origin = (
                f"{leg['origin']['type']} "
                f"{leg['origin'].get('name') or leg['origin'].get('address')}"
            )
            if leg["origin"]["type"] == "stop":
                origin += f" ({products_to_string(leg['origin']['products'])})"
            elif leg["origin"]["type"] == "location" and leg.get("walking"):
                origin += " (by foot)"
            else:
                raise NotImplementedError(
                    f"Unknown destination type: {leg['destination']['type']}"
                )

            arrival: datetime.datetime = datetime.datetime.fromisoformat(leg["arrival"])
            destination = (
                f"{leg['destination']['type']} "
                f"{leg['destination'].get('name') or leg['destination'].get('address')}"
            )
            if leg["destination"]["type"] == "stop":
                destination += (
                    f" ({products_to_string(leg['destination']['products'])})"
                )
            elif leg["destination"]["type"] == "location" and leg.get("walking"):
                destination += " (by foot)"
            else:
                raise NotImplementedError(
                    f"Unknown destination type: {leg['destination']['type']}"
                )

            duration = arrival - departure
            # print(f"Departure: {departure} from {origin}. Arrival: {arrival} at {destination}. ")
            print(f"{duration} from {origin}. to {destination}. ")

        first_departure = datetime.datetime.fromisoformat(legs[0]["departure"])
        total_duration: datetime.timedelta = arrival - first_departure
        durations.append(total_duration)
        print(f"Duration: {total_duration}")
        print("-----------")

    print(f"Min duration: {min(durations)}")
    print(f"Origin: {location_origin}")
    print(f"Destination: {location_destination}")
