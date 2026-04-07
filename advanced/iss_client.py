import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import requests
from datetime import datetime
from config import (
    ISS_API_URL,
    SUNRISE_SUNSET_API_URL,
    MY_LAT,
    MY_LONG,
    OVERHEAD_THRESHOLD,
)


class ISSClient:
    """Fetches ISS position and sunrise/sunset data from public APIs."""

    def is_overhead(self) -> bool:
        """Return True if the ISS is within OVERHEAD_THRESHOLD degrees of MY_LAT/MY_LONG."""
        response = requests.get(ISS_API_URL)
        response.raise_for_status()
        data = response.json()

        iss_lat = float(data["iss_position"]["latitude"])
        iss_lon = float(data["iss_position"]["longitude"])

        lat_ok = (MY_LAT - OVERHEAD_THRESHOLD) <= iss_lat <= (MY_LAT + OVERHEAD_THRESHOLD)
        lon_ok = (MY_LONG - OVERHEAD_THRESHOLD) <= iss_lon <= (MY_LONG + OVERHEAD_THRESHOLD)
        return lat_ok and lon_ok

    def is_night(self) -> bool:
        """Return True if it is currently dark at MY_LAT/MY_LONG."""
        params = {"lat": MY_LAT, "lng": MY_LONG, "formatted": 0}
        response = requests.get(SUNRISE_SUNSET_API_URL, params=params)
        response.raise_for_status()
        data = response.json()

        sunrise = int(data["results"]["sunrise"].split("T")[1].split(":")[0])
        sunset = int(data["results"]["sunset"].split("T")[1].split(":")[0])
        hour_now = datetime.now().hour

        return hour_now >= sunset or hour_now <= sunrise
