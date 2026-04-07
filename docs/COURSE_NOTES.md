# Course Notes — Day 33: API Endpoints and Parameters

**Course:** 100 Days of Code: The Complete Python Pro Bootcamp by Dr. Angela Yu
**Day:** 33 — Part 1

## Exercise description

Build an ISS overhead notifier that:
1. Polls the Open Notify API every 60 seconds to get the current ISS latitude/longitude.
2. Checks the Sunrise-Sunset API to determine whether it is currently dark at your location.
3. If the ISS is within ±5° of your position AND it is nighttime, sends you an email saying "Look Up!".

## Concepts covered

- **API requests with query parameters** — using `requests.get(url, params={...})` to pass
  latitude/longitude to the sunrise-sunset API.
- **Parsing JSON responses** — extracting nested values from `response.json()`.
- **`response.raise_for_status()`** — automatically raising an exception on HTTP errors.
- **SMTP email via `smtplib`** — `starttls()`, `login()`, `sendmail()`.
- **`while True` polling loop with `time.sleep()`** — running a check on a fixed interval.
- **Datetime comparison** — using `datetime.now().hour` against API-returned sunrise/sunset hours.
- **App passwords** — using a Gmail app password instead of the main account password.

## APIs used

| API | Endpoint | Auth |
|-----|----------|------|
| Open Notify ISS Position | `http://api.open-notify.org/iss-now.json` | None |
| Sunrise-Sunset | `https://api.sunrise-sunset.org/json` | None |
| Gmail SMTP | `smtp.gmail.com:587` | App password |
