# main.py
import requests
from datetime import datetime
import smtplib
import time
from config import MY_LAT, MY_LONG, MY_EMAIL, MY_PASSWORD, TO_EMAIL, SMTP_PORT

# ----------------- FUNCTIONS -----------------
def is_iss_overhead():
    """Return True if ISS is within +5/-5 degrees of my position."""
    response = requests.get(url="http://api.open-notify.org/iss-now.json")
    response.raise_for_status()
    data = response.json()

    iss_latitude = float(data["iss_position"]["latitude"])
    iss_longitude = float(data["iss_position"]["longitude"])

    if (MY_LAT - 5) <= iss_latitude <= (MY_LAT + 5) and (MY_LONG - 5) <= iss_longitude <= (MY_LONG + 5):
        return True
    return False


def is_night():
    """Return True if it is currently dark at my position."""
    parameters = {
        "lat": MY_LAT,
        "lng": MY_LONG,
        "formatted": 0,
    }
    response = requests.get("https://api.sunrise-sunset.org/json", params=parameters)
    response.raise_for_status()
    data = response.json()

    sunrise = int(data["results"]["sunrise"].split("T")[1].split(":")[0])
    sunset = int(data["results"]["sunset"].split("T")[1].split(":")[0])

    time_now = datetime.now().hour

    if time_now >= sunset or time_now <= sunrise:
        return True
    return False


def send_email():
    """Send an email notification to look up at the ISS."""
    with smtplib.SMTP("smtp.gmail.com", SMTP_PORT) as connection:
        connection.starttls()
        connection.login(MY_EMAIL, MY_PASSWORD)
        connection.sendmail(
            from_addr=MY_EMAIL,
            to_addrs=TO_EMAIL,
            msg="Subject:Look Up!\n\nThe ISS is above you in the sky!"
        )

# ----------------- MAIN LOOP -----------------
while True:
    time.sleep(60)  # run every 60 seconds
    if is_iss_overhead() and is_night():
        send_email()
