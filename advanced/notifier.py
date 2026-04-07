import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import smtplib
from config import SMTP_HOST, SMTP_PORT


class EmailNotifier:
    """Sends email notifications via Gmail SMTP."""

    def __init__(self, sender: str, password: str, recipient: str) -> None:
        self._sender = sender
        self._password = password
        self._recipient = recipient

    def send(self, subject: str, body: str) -> None:
        """Send an email with the given subject and body. Raises on failure."""
        msg = f"Subject:{subject}\n\n{body}"
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as connection:
            connection.starttls()
            connection.login(self._sender, self._password)
            connection.sendmail(
                from_addr=self._sender,
                to_addrs=self._recipient,
                msg=msg,
            )
