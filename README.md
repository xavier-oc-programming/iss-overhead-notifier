# ISS Overhead Notifier

Polls the ISS position every 60 seconds and sends an email notification when the station is overhead and it is dark outside.

## Table of Contents

- [Quick start](#quick-start)
- [Builds comparison](#builds-comparison)
- [Usage](#usage)
- [Data flow](#data-flow)
- [Features](#features)
- [Navigation flow](#navigation-flow)
- [Architecture](#architecture)
- [Module reference](#module-reference)
- [Configuration reference](#configuration-reference)
- [Data schema](#data-schema)
- [Environment variables](#environment-variables)
- [Design decisions](#design-decisions)
- [Course context](#course-context)
- [Dependencies](#dependencies)

---

## Quick start

```bash
pip install -r requirements.txt
cp .env.example .env   # fill in your Gmail address, app password, and recipient
python menu.py         # select 1 (original) or 2 (advanced), or run builds directly
```

Run a build directly:

```bash
python original/main.py
python advanced/main.py
```

---

## Builds comparison

| Feature | Original | Advanced |
|---------|----------|----------|
| ISS position check | ✓ | ✓ |
| Sunrise/sunset check | ✓ | ✓ |
| Email notification | ✓ | ✓ |
| 60-second polling loop | ✓ | ✓ |
| Credentials via `.env` | — | ✓ |
| OOP (`ISSClient`, `EmailNotifier`) | — | ✓ |
| All constants in `config.py` | — | ✓ |
| Per-iteration error handling | — | ✓ |
| Run counter logging | — | ✓ |
| Configurable overhead threshold | — | ✓ |

---

## Usage

Both builds run as a polling loop. Start them and leave them running. They will log to stdout and send an email when the ISS is visible.

**Original:**

```bash
python original/main.py
# (no output until an email is sent)
```

**Advanced:**

```bash
python advanced/main.py
# [run 1] ISS overhead=False, night=True — no action.
# [run 2] ISS overhead=False, night=True — no action.
# [run 3] ISS overhead=True, night=True — email sent.
```

**Environment variables** required in `.env`:

```
MY_EMAIL=your_gmail@gmail.com
MY_PASSWORD=your_app_password
TO_EMAIL=recipient@example.com
```

---

## Data flow

```
1. WAIT        time.sleep(60) — pause before each check
2. FETCH ISS   GET http://api.open-notify.org/iss-now.json
                 → JSON: { "iss_position": { "latitude": "...", "longitude": "..." } }
3. FETCH SUN   GET https://api.sunrise-sunset.org/json?lat=...&lng=...&formatted=0
                 → JSON: { "results": { "sunrise": "2024-01-01T06:30:00+00:00",
                                        "sunset":  "2024-01-01T18:45:00+00:00" } }
4. CHECK       ISS lat/lon within ±5° of MY_LAT/MY_LONG?
               Current hour outside sunrise..sunset window?
5. NOTIFY      If both true → SMTP sendmail to TO_EMAIL
               Otherwise    → log and sleep
```

---

## Features

**ISS position polling.** Every 60 seconds the script hits the Open Notify API and reads the current ISS latitude and longitude. No API key required.

**Sunrise/sunset gating.** Before sending a notification the script checks the Sunrise-Sunset API for the current sunrise and sunset hours at your location. An email is only sent if it is dark — there is no point alerting you to an invisible station.

**Email notification.** When both conditions are met a plain-text email with subject "Look Up!" is sent via Gmail SMTP using `starttls` and an app password.

**Per-iteration error handling (advanced only).** Each loop iteration is wrapped in `try/except`. An API timeout or SMTP failure prints an error and moves on to the next iteration — the bot does not crash.

**Run counter logging (advanced only).** Every iteration prints its run number, the overhead and night booleans, and whether an email was sent. This makes it easy to see the bot is alive without opening the terminal constantly.

**Configurable threshold (advanced only).** `OVERHEAD_THRESHOLD` in `config.py` controls the degree window. Change it once; it takes effect everywhere.

---

## Navigation flow

### a) Terminal menu tree

```
python menu.py
│
├── 1  →  original/main.py   (runs until Ctrl-C; menu reappears after)
├── 2  →  advanced/main.py   (runs until Ctrl-C; menu reappears after)
└── q  →  exit
         (any other input → "Invalid choice. Try again." → re-prompt)
```

### b) Execution flow

```
┌─────────────────────────────────────────┐
│  START  advanced/main.py                │
│  Load .env, init ISSClient + Notifier   │
└───────────────┬─────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────┐
│  time.sleep(CHECK_INTERVAL)             │
└───────────────┬─────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────┐
│  try:                                   │
│    ISSClient.is_overhead()              │
│      API error → raise → except block  │
│    ISSClient.is_night()                 │
│      API error → raise → except block  │
│                                         │
│    overhead AND night?                  │
│      YES → EmailNotifier.send()         │
│              SMTP error → raise → except│
│              success → log "email sent" │
│      NO  → log "no action"              │
│                                         │
│  except Exception as e:                 │
│    print error, continue loop           │
└───────────────┬─────────────────────────┘
                │
                └──── back to sleep ──────┘
```

---

## Architecture

```
iss-overhead-notifier/
│
├── menu.py              # interactive launcher — runs original/ or advanced/
├── art.py               # LOGO ascii art printed by menu.py
├── requirements.txt     # pip dependencies
├── .env.example         # template for required environment variables
├── .gitignore
├── README.md
│
├── docs/
│   └── COURSE_NOTES.md  # original exercise description and concepts
│
├── original/
│   ├── main.py          # course build verbatim (credentials via os.environ)
│   └── config.py        # location + SMTP constants (credentials via os.environ)
│
└── advanced/
    ├── config.py        # all constants grouped by category
    ├── iss_client.py    # ISSClient — ISS position + night check
    ├── notifier.py      # EmailNotifier — SMTP send
    └── main.py          # orchestrator — wires classes, owns the run loop
```

---

## Module reference

### `ISSClient` (advanced/iss_client.py)

| Method | Returns | Description |
|--------|---------|-------------|
| `is_overhead()` | `bool` | `True` if ISS lat/lon is within `OVERHEAD_THRESHOLD` degrees of `MY_LAT`/`MY_LONG`. Raises `requests.HTTPError` on API failure. |
| `is_night()` | `bool` | `True` if the current UTC hour is outside the sunrise–sunset window at `MY_LAT`/`MY_LONG`. Raises `requests.HTTPError` on API failure. |

### `EmailNotifier` (advanced/notifier.py)

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(sender, password, recipient)` | `None` | Stores SMTP credentials. No connection opened at init. |
| `send(subject, body)` | `None` | Sends a plain-text email via Gmail SMTP with `starttls`. Raises `smtplib.SMTPException` on failure. |

---

## Configuration reference

All constants live in `advanced/config.py`.

| Constant | Default | Description |
|----------|---------|-------------|
| `ISS_API_URL` | `http://api.open-notify.org/iss-now.json` | Open Notify real-time ISS position endpoint |
| `SUNRISE_SUNSET_API_URL` | `https://api.sunrise-sunset.org/json` | Sunrise-Sunset API endpoint |
| `MY_LAT` | `40.416775` | Observer latitude (Madrid, Spain) |
| `MY_LONG` | `-3.703790` | Observer longitude (Madrid, Spain) |
| `OVERHEAD_THRESHOLD` | `5` | Degrees — ISS must be within this range on both axes |
| `SMTP_HOST` | `smtp.gmail.com` | Gmail SMTP server |
| `SMTP_PORT` | `587` | SMTP STARTTLS port |
| `CHECK_INTERVAL` | `60` | Seconds to sleep between position checks |

---

## Data schema

### ISS position API response

```json
{
  "message": "success",
  "timestamp": 1700000000,
  "iss_position": {
    "latitude": "40.1234",
    "longitude": "-3.5678"
  }
}
```

Fields used: `iss_position.latitude`, `iss_position.longitude` (both returned as strings; cast to `float`).

### Sunrise-Sunset API response

```json
{
  "results": {
    "sunrise": "2024-01-15T07:32:00+00:00",
    "sunset":  "2024-01-15T17:51:00+00:00"
  },
  "status": "OK"
}
```

Fields used: `results.sunrise` and `results.sunset`. Only the hour component (index 1 after splitting on `T` then `:`) is extracted.

### Email output

```
To:      TO_EMAIL
From:    MY_EMAIL
Subject: Look Up!

The ISS is above you in the sky!
```

No files are written. No state is persisted between runs.

---

## Environment variables

Copy `.env.example` to `.env` and fill in values.

| Variable | Required | Description |
|----------|----------|-------------|
| `MY_EMAIL` | Yes | Gmail address used to send the notification |
| `MY_PASSWORD` | Yes | Gmail **app password** (not your main password) |
| `TO_EMAIL` | Yes | Address to receive the "Look Up!" email |

> Generate a Gmail app password at: Google Account → Security → 2-Step Verification → App passwords.

---

## Design decisions

**`config.py` — zero magic numbers.** Every URL, coordinate, threshold, port, and interval is named in one place. A future change to the overhead window or check frequency requires editing exactly one line.

**Separate `ISSClient` and `EmailNotifier` modules.** Each class has one job. `ISSClient` can be tested without an SMTP server; `EmailNotifier` can be tested without hitting any external API. Swapping the HTTP library or the email provider touches exactly one file.

**Credentials via `.env`, never hardcoded.** The original course file stored a real Gmail app password as a string literal. The advanced build (and the `original/` copy) reads credentials from environment variables so the source code is safe to commit and share.

**`.env.example` committed, `.env` gitignored.** Anyone cloning the repo knows exactly which variables they need without ever seeing a real credential. The `.gitignore` entry was present from the very first commit so there is no window during which a real `.env` could have been staged.

**`Path(__file__).parent` for all paths.** The script works correctly whether it is launched from `menu.py` (which sets `cwd` to the script's own directory) or invoked directly from any other working directory.

**Pure-logic modules raise exceptions instead of `sys.exit()`.** `ISSClient` and `EmailNotifier` signal failure by raising. `main.py` decides what to do — in this case, log the error and keep looping. This separation means the modules can be reused or tested without side effects.

**`sys.path.insert` pattern.** Both `iss_client.py` and `notifier.py` insert their own directory at the front of `sys.path` so sibling imports (`from config import ...`) work whether the file is run directly or imported by `main.py`.

**`subprocess.run` with `cwd=`.** `menu.py` launches each build with `cwd` set to the build's own directory. This means the launched script's relative imports and any relative file paths resolve correctly without altering the parent process's working directory.

**`while True` in `menu.py` vs recursion.** The menu re-renders by looping, not by calling itself. A recursive approach would grow the stack on every menu return — harmless for a few invocations, but wrong in principle.

**Console cleared before every menu render.** Each loop iteration clears the terminal before printing the menu. This prevents the output of the previous build from cluttering the menu and gives a clean UX.

**`time.sleep` at the bottom of the loop.** The check runs immediately on startup (conceptually — actually sleeps first to match the original course build), then waits. Putting `sleep` at the bottom of the loop body means the interval is consistent regardless of how long the API calls take.

**`try/except` per iteration, not around the whole loop.** A network timeout or an SMTP error on one check does not kill the bot. The exception is caught, logged, and the loop continues. Wrapping the entire `while True` would cause the bot to die on the first transient failure.

**Run count as a one-element list.** `run_count: list[int] = [0]` is a mutable cell that can be incremented inside the loop body without `global` or `nonlocal`. It is the idiomatic Python pattern for shared mutable state in a closure or loop where `nonlocal` is unavailable or undesirable.

---

## Course context

Built as **Day 33** of *100 Days of Code: The Complete Python Pro Bootcamp* by Dr. Angela Yu.

**Concepts covered in the original build:**
- Making HTTP GET requests with query parameters (`requests.get`, `params={}`)
- Parsing nested JSON API responses
- `response.raise_for_status()` for automatic HTTP error handling
- Reading datetime strings from API responses and comparing hours
- Sending email via `smtplib` with STARTTLS and app passwords
- Polling with `while True` and `time.sleep()`

**The advanced build extends into:**
- OOP design — encapsulating API concerns in `ISSClient` and email concerns in `EmailNotifier`
- Credential management with `python-dotenv`
- Centralised configuration in `config.py`
- Per-iteration error handling in a polling loop
- Module isolation and testability

See [docs/COURSE_NOTES.md](docs/COURSE_NOTES.md) for the full concept breakdown.

---

## Dependencies

| Module | Used in | Purpose |
|--------|---------|---------|
| `requests` | original, advanced | HTTP GET requests to Open Notify and Sunrise-Sunset APIs |
| `smtplib` | original, advanced | Sending email via Gmail SMTP (standard library) |
| `datetime` | original, advanced | Getting current hour for sunrise/sunset comparison (standard library) |
| `time` | original, advanced | `time.sleep()` for polling interval (standard library) |
| `python-dotenv` | advanced | Loading `.env` credentials into `os.environ` |
| `os` | original, advanced | `os.environ.get()` for credential access (standard library) |
| `pathlib` | advanced | `Path(__file__).parent` for portable file paths (standard library) |
| `sys` | advanced | `sys.path.insert` for sibling imports (standard library) |
