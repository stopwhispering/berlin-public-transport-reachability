from dataclasses import dataclass

import requests

OPENCAGEDATA_API_KEY = "0bdced519d1b496db7aa2b0f4509aed3"


@dataclass
class Location:
    address: str
    latitude: str
    longitude: str


def get_coordinates_by_addresss(
    address: str = "Ernst Reuter Platz 7, 10587 Berlin",
) -> Location:
    params = {
        "q": address,
        "key": OPENCAGEDATA_API_KEY,
    }
    url = "https://api.opencagedata.com/geocode/v1/json"
    response = requests.get(url, params=params, timeout=15)
    result = response.json()
    if result.get("results") and result["results"][0].get("geometry"):
        # return result["results"][0]["geometry"]['lat'], result["results"][0]["geometry"]['lng']
        return Location(
            address=result["results"][0]["formatted"],
            latitude=result["results"][0]["geometry"]["lat"],
            longitude=result["results"][0]["geometry"]["lng"],
        )
    raise ValueError(f"Could not find coordinates for {address}")
