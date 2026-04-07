import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import os
import time
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

from config import CHECK_INTERVAL
from iss_client import ISSClient
from notifier import EmailNotifier

client = ISSClient()
notifier = EmailNotifier(
    sender=os.environ["MY_EMAIL"],
    password=os.environ["MY_PASSWORD"],
    recipient=os.environ["TO_EMAIL"],
)

run_count: list[int] = [0]

while True:
    run_count[0] += 1
    try:
        overhead = client.is_overhead()
        night = client.is_night()
        if overhead and night:
            notifier.send(
                subject="Look Up!",
                body="The ISS is above you in the sky!",
            )
            print(f"[run {run_count[0]}] ISS overhead and dark — email sent.")
        else:
            print(
                f"[run {run_count[0]}] ISS overhead={overhead}, night={night} — no action."
            )
    except Exception as e:
        print(f"[run {run_count[0]}] Error: {e}")
    time.sleep(CHECK_INTERVAL)
