# ISS Overhead Notifier

Checks the ISS position every 5 minutes via GitHub Actions and sends an email notification when the station is overhead and it is dark outside.

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

**Local (original build or manual advanced run):**

```bash
pip install -r requirements.txt
cp .env.example .env   # fill in your Gmail address, app password, and recipient
python menu.py         # select 1 (original) or 2 (advanced), or run builds directly
```

**Automated (advanced build via GitHub Actions):**

1. Fork or push this repo to your GitHub account.
2. Go to **Settings → Secrets and variables → Actions**.
3. Add three repository secrets: `MY_EMAIL`, `MY_PASSWORD`, `TO_EMAIL`.
4. The workflow runs automatically every 5 minutes — no server required.

To trigger a check manually: **Actions → ISS Overhead Check → Run workflow**.

---

## Builds comparison

| Feature | Original | Advanced |
|---------|----------|----------|
| ISS position check | ✓ | ✓ |
| Sunrise/sunset check | ✓ | ✓ |
| Email notification | ✓ | ✓ |
| 60-second polling loop | ✓ | — |
| Credentials via `.env` | — | ✓ |
| OOP (`ISSClient`, `EmailNotifier`) | — | ✓ |
| All constants in `config.py` | — | ✓ |
| GitHub Actions scheduling (every 5 min) | — | ✓ |
| Single-run, serverless | — | ✓ |
| Configurable overhead threshold | — | ✓ |
| Manual trigger via Actions tab | — | ✓ |

---

## Usage

**Original** — polling loop, run locally and leave it running:

```bash
python original/main.py
# (no output until an email is sent)
```

**Advanced** — single-run, triggered by GitHub Actions every 5 minutes:

```bash
# Run manually for one check:
python advanced/main.py
# ISS overhead=False, night=True — no action.
```

GitHub Actions output (visible in the Actions tab):

```
ISS overhead=True, night=True — email sent.
```

**Credentials** for local runs go in `.env`:

```
MY_EMAIL=your_gmail@gmail.com
MY_PASSWORD=your_app_password
TO_EMAIL=recipient@example.com
```

For GitHub Actions, add the same three values as repository secrets (never in `.env`).

---

## Data flow

```
1. TRIGGER     GitHub Actions cron (*/5 * * * *) or manual dispatch
2. FETCH ISS   GET http://api.open-notify.org/iss-now.json
                 → JSON: { "iss_position": { "latitude": "...", "longitude": "..." } }
3. FETCH SUN   GET https://api.sunrise-sunset.org/json?lat=...&lng=...&formatted=0
                 → JSON: { "results": { "sunrise": "2024-01-01T06:30:00+00:00",
                                        "sunset":  "2024-01-01T18:45:00+00:00" } }
4. CHECK       ISS lat/lon within ±5° of MY_LAT/MY_LONG?
               Current hour outside sunrise..sunset window?
5. NOTIFY      If both true → SMTP sendmail to TO_EMAIL
               Otherwise    → log and exit 0
```

---

## Features

**ISS position check.** The script hits the Open Notify API and reads the current ISS latitude and longitude. No API key required.

**Sunrise/sunset gating.** Before sending a notification the script checks the Sunrise-Sunset API for the current sunrise and sunset hours at your location. An email is only sent if it is dark — there is no point alerting you to an invisible station.

**Email notification.** When both conditions are met a plain-text email with subject "Look Up!" is sent via Gmail SMTP using `starttls` and an app password.

**GitHub Actions scheduling (advanced only).** The workflow runs every 5 minutes on GitHub's infrastructure — no Raspberry Pi, no VPS, no always-on process. Free for public repositories.

**Manual trigger (advanced only).** The `workflow_dispatch` event lets you trigger a check instantly from the Actions tab without waiting for the next cron tick. Useful for testing.

**Configurable threshold (advanced only).** `OVERHEAD_THRESHOLD` in `config.py` controls the degree window. Change it once; it takes effect everywhere.

---

## Navigation flow

### a) Terminal menu tree

```
python menu.py
│
├── 1  →  original/main.py   (polling loop; runs until Ctrl-C; menu reappears after)
├── 2  →  advanced/main.py   (single check; exits immediately; menu reappears after)
└── q  →  exit
         (any other input → "Invalid choice. Try again." → re-prompt)
```

### b) Execution flow (advanced)

```
┌─────────────────────────────────────────────┐
│  TRIGGER  GitHub Actions cron / manual      │
│  Set env vars from repository secrets       │
│  pip install -r requirements.txt            │
│  python advanced/main.py                    │
└───────────────┬─────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────────┐
│  Load .env (local only — no-op on Actions)  │
│  Init ISSClient + EmailNotifier             │
└───────────────┬─────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────────┐
│  ISSClient.is_overhead()                    │
│    API error → exception propagates → exit 1│
│  ISSClient.is_night()                       │
│    API error → exception propagates → exit 1│
│                                             │
│  overhead AND night?                        │
│    YES → EmailNotifier.send()               │
│            SMTP error → exception → exit 1  │
│            success → print + exit 0         │
│    NO  → print "no action" + exit 0         │
└─────────────────────────────────────────────┘
```

---

## Architecture

```
iss-overhead-notifier/
│
├── .github/
│   └── workflows/
│       └── iss-check.yml    # cron schedule + secrets → runs advanced/main.py
│
├── menu.py                  # interactive launcher — runs original/ or advanced/
├── art.py                   # LOGO ascii art printed by menu.py
├── requirements.txt         # pip dependencies
├── .env.example             # template for required environment variables
├── .gitignore
├── README.md
│
├── docs/
│   └── COURSE_NOTES.md      # original exercise description and concepts
│
├── original/
│   ├── main.py              # course build verbatim (credentials via os.environ)
│   └── config.py            # location + SMTP constants (credentials via dummy values)
│
└── advanced/
    ├── config.py            # all constants grouped by category
    ├── iss_client.py        # ISSClient — ISS position + night check
    ├── notifier.py          # EmailNotifier — SMTP send
    └── main.py              # single-run orchestrator — check once, exit
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

All constants live in `advanced/config.py`. The check interval is controlled by the cron expression in `.github/workflows/iss-check.yml`.

| Constant | Default | Description |
|----------|---------|-------------|
| `ISS_API_URL` | `http://api.open-notify.org/iss-now.json` | Open Notify real-time ISS position endpoint |
| `SUNRISE_SUNSET_API_URL` | `https://api.sunrise-sunset.org/json` | Sunrise-Sunset API endpoint |
| `MY_LAT` | `40.416775` | Observer latitude (Madrid, Spain) |
| `MY_LONG` | `-3.703790` | Observer longitude (Madrid, Spain) |
| `OVERHEAD_THRESHOLD` | `5` | Degrees — ISS must be within this range on both axes |
| `SMTP_HOST` | `smtp.gmail.com` | Gmail SMTP server |
| `SMTP_PORT` | `587` | SMTP STARTTLS port |

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

**Local runs:** copy `.env.example` to `.env` and fill in values.
**GitHub Actions:** add the same variables as repository secrets (Settings → Secrets and variables → Actions).

| Variable | Required | Description |
|----------|----------|-------------|
| `MY_EMAIL` | Yes | Gmail address used to send the notification |
| `MY_PASSWORD` | Yes | Gmail **app password** (not your main password) |
| `TO_EMAIL` | Yes | Address to receive the "Look Up!" email |

> Generate a Gmail app password at: Google Account → Security → 2-Step Verification → App passwords.

---

## Design decisions

**GitHub Actions instead of a polling loop.** The original build runs a `while True` loop and needs an always-on machine (Raspberry Pi, VPS). The advanced build is a single-run script triggered by a cron workflow — GitHub runs it every 5 minutes on free infrastructure. No server to maintain, no process to restart, and the run history is logged automatically in the Actions tab.

**`config.py` — zero magic numbers.** Every URL, coordinate, threshold, and port is named in one place. A future change to the overhead window requires editing exactly one line.

**Separate `ISSClient` and `EmailNotifier` modules.** Each class has one job. `ISSClient` can be tested without an SMTP server; `EmailNotifier` can be tested without hitting any external API. Swapping the HTTP library or the email provider touches exactly one file.

**Credentials via secrets, never hardcoded.** Locally via `.env`, on GitHub Actions via repository secrets. The same `os.environ["MY_EMAIL"]` call works in both environments — `load_dotenv` is a no-op when no `.env` exists (GitHub Actions), and populates env vars when it does (local).

**`.env.example` committed, `.env` gitignored.** Anyone cloning the repo knows exactly which variables they need without ever seeing a real credential.

**`Path(__file__).parent` for all paths.** The script works correctly whether launched from `menu.py`, run directly, or invoked by GitHub Actions from the repo root.

**Pure-logic modules raise exceptions instead of `sys.exit()`.** `ISSClient` and `EmailNotifier` signal failure by raising. `main.py` (and GitHub Actions) decides what to do — a non-zero exit code marks the run as failed in the Actions UI.

**`sys.path.insert` pattern.** Sibling imports (`from config import ...`) work whether the file is run directly, imported by `main.py`, or invoked via `python advanced/main.py` from the repo root.

**`subprocess.run` with `cwd=`.** `menu.py` launches each build with `cwd` set to the build's own directory so relative imports resolve correctly.

**`while True` in `menu.py` vs recursion.** The menu re-renders by looping, not by calling itself — no stack growth on each return.

**Console cleared only on transition, not on invalid input.** The `clear` flag ensures the screen clears on first draw and after a build exits, but error messages stay visible long enough to read.

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
- Credential management with `python-dotenv` and GitHub Actions secrets
- Centralised configuration in `config.py`
- Serverless scheduling via GitHub Actions cron workflows
- Module isolation and testability

See [docs/COURSE_NOTES.md](docs/COURSE_NOTES.md) for the full concept breakdown.

---

## Dependencies

| Module | Used in | Purpose |
|--------|---------|---------|
| `requests` | original, advanced | HTTP GET requests to Open Notify and Sunrise-Sunset APIs |
| `smtplib` | original, advanced | Sending email via Gmail SMTP (standard library) |
| `datetime` | original, advanced | Getting current hour for sunrise/sunset comparison (standard library) |
| `time` | original | `time.sleep()` for polling interval (standard library) |
| `python-dotenv` | advanced | Loading `.env` credentials into `os.environ` for local runs |
| `os` | original, advanced | `os.environ` for credential access (standard library) |
| `pathlib` | advanced | `Path(__file__).parent` for portable file paths (standard library) |
| `sys` | advanced | `sys.path.insert` for sibling imports (standard library) |
