import requests
import datetime
import pytz
import logging
from typing import Literal

logger = logging.getLogger(__name__)


# # example reachable-from url:
# url = ('https://v5.bvg.transport.rest/stops/reachable-from?latitude=52.521508&longitude=13.411267&'
#        'address=S%2BU+Alexanderplatz&maxDuration=50&suburban=True&subway=True&tram=True&bus=True&'
#        'ferry=False&express=False&regional=False')


class BerlinTransportApi:
    """Fetch Berlin Public Transport data"""
    def __init__(self,
                 max_duration: int,
                 time: Literal['next_sunday_early_morning', 'next_workday_noon'],
                 max_transfers: int):
        self.base_url = "https://v5.bvg.transport.rest"
        self.max_duration = max_duration
        self.time = time
        self.max_transfers = max_transfers

    def get_destination(self, query: str):
        """Get destination by query via location api"""
        url = self.base_url + "/locations"
        params = {
            "query": query,
            "results": 1
        }
        response = requests.get(url, params=params)
        destination = response.json()[0]
        if query.lower() not in destination['name'].lower():
            raise Exception(f"Location not found. Found {destination['name']} instead of {query}.")
        return destination

    @staticmethod
    def _next_weekday(weekday: int):
        """Get next weekday (0 = Monday, 6 = Sunday)"""
        today = datetime.date.today()
        days_ahead = weekday - today.weekday()
        if days_ahead <= 0:  # Target day already happened this week
            days_ahead += 7
        return today + datetime.timedelta(days_ahead)

    def _next_workday_noon_as_iso(self) -> str:
        """Get next workday at noon in iso format"""
        next_workday = self._next_weekday(weekday=0)
        noon = datetime.time(12, 0, 0, 0, tzinfo=pytz.timezone('Europe/Berlin'))
        next_workday_noon = datetime.datetime.combine(next_workday, noon)
        return next_workday_noon.isoformat()

    def _next_sunday_early_morning_as_iso(self) -> str:
        """Get next sunday early morning in iso format"""
        next_sunday = self._next_weekday(weekday=6)
        early_morning = datetime.time(4, 0, 0, 0, tzinfo=pytz.timezone('Europe/Berlin'))
        next_sunday_early_morning = datetime.datetime.combine(next_sunday, early_morning)
        return next_sunday_early_morning.isoformat()

    def get_reachable_stops_from(self,
                                 destination: dict) -> list[dict]:
        """Get reachable stops for supplied destination within certain duration"""
        logger.debug(f"Getting reachable stops for {destination['name']} at {self.time}.")

        if self.time == 'next_sunday_early_morning':
            when = self._next_sunday_early_morning_as_iso()
        elif self.time == 'next_workday_noon':
            when = self._next_workday_noon_as_iso()
        else:
            raise Exception(f"Invalid time: {self.time}")

        url = self.base_url + f"/stops/reachable-from"
        params = {
            "latitude": destination['location']['latitude'],
            "longitude": destination['location']['longitude'],
            "address": destination['name'],
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

        response = requests.get(url, params=params)
        reachable_stops = response.json()

        logger.debug(f"Found {len([station for r in reachable_stops for station in r['stations']])} non-distinct "
                     f"reachable stations from {destination['name']} at {when} with duration "
                     f"up to {self.max_duration} min.")
        return reachable_stops
