import datetime
import logging

import pytz
import requests

from berlin_public_transport_reachability.entities import (
    Destination,
    ReachableInMinutes,
)
from berlin_public_transport_reachability.enums import TimeValue

logger = logging.getLogger(__name__)


# # example reachable-from url:
# url = ('https://v5.bvg.transport.rest/stops/reachable-from?latitude=52.521508&'
#        'longitude=13.411267&'
#        'address=S%2BU+Alexanderplatz&maxDuration=50&suburban=True&subway=True&tram=True&bus=True&'
#        'ferry=False&express=False&regional=False')


class BerlinTransportApi:
    """Fetch Berlin Public Transport data"""

    def __init__(
        self,
        max_duration: int,
        time: TimeValue,
        max_transfers: int,
    ):
        self.base_url = "https://v5.bvg.transport.rest"
        self.max_duration = max_duration
        self.time = time
        self.max_transfers = max_transfers

    def get_destination(self, query: str) -> Destination:
        """Get destination by query via location api"""
        url = self.base_url + "/locations"
        params: dict[str, str | int] = {
            "query": query,
            "results": 1,
        }
        response = requests.get(url, params=params, timeout=15)
        destination_ = response.json()[0]
        if query.lower() not in destination_["name"].lower():
            raise ValueError(
                f"Location not found. Found {destination_['name']} instead of {query}."
            )
        return Destination(**destination_)

    @staticmethod
    def _next_weekday(weekday: int) -> datetime.date:
        """Get next weekday (0 = Monday, 6 = Sunday)"""
        today = datetime.datetime.now(tz=pytz.timezone("Europe/Berlin")).date()
        days_ahead = weekday - today.weekday()
        if days_ahead <= 0:  # Target day already happened this week
            days_ahead += 7
        return today + datetime.timedelta(days_ahead)

    def _next_workday_noon_as_iso(self) -> str:
        """Get next workday at noon in iso format"""
        next_workday = self._next_weekday(weekday=0)
        noon = datetime.time(12, 0, 0, 0, tzinfo=pytz.timezone("Europe/Berlin"))
        next_workday_noon = datetime.datetime.combine(next_workday, noon)
        return next_workday_noon.isoformat()

    def _next_sunday_early_morning_as_iso(self) -> str:
        """Get next sunday early morning in iso format"""
        next_sunday = self._next_weekday(weekday=6)
        early_morning = datetime.time(4, 0, 0, 0, tzinfo=pytz.timezone("Europe/Berlin"))
        next_sunday_early_morning = datetime.datetime.combine(
            next_sunday, early_morning
        )
        return next_sunday_early_morning.isoformat()

    def get_reachable_stops_from(
        self, destination: Destination
    ) -> list[ReachableInMinutes]:
        """Get reachable stops for supplied destination within certain duration"""
        logger.info(f"Getting reachable stops for {destination.name} at {self.time}.")

        if self.time == TimeValue.NEXT_SUNDAY_EARLY_MORNING:
            when = self._next_sunday_early_morning_as_iso()
        elif self.time == TimeValue.NEXT_WORKDAY_NOON:
            when = self._next_workday_noon_as_iso()
        else:
            raise ValueError(f"Invalid time: {self.time}")

        url = self.base_url + "/stops/reachable-from"
        params: dict[str, int | float | str | bool] = {
            "latitude": destination.location.latitude,
            "longitude": destination.location.longitude,
            "address": destination.name,
            "when": when,
            "maxTransfers": 3,
            "maxDuration": self.max_duration,
            "suburban": True,  # S-Bahn
            "subway": True,  # U-Bahn
            "tram": True,  # Tram
            "bus": True,  # Bus
            "ferry": False,  # Ferry
            "express": False,  # ICE/IC
            "regional": False,  # RE/RB
        }

        response = requests.get(url, params=params, timeout=15)
        reachable_stops = response.json()

        logger.info(
            f"Found {len([station for r in reachable_stops for station in r['stations']])}"
            f" non-distinct "
            f"reachable stations from {destination.name} at {when} with duration "
            f"up to {self.max_duration} min."
        )
        return [ReachableInMinutes(**r) for r in reachable_stops]
