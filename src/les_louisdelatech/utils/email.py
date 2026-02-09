"""Email sending helpers (Gmail API).

We send provisioning/reset credentials by email (not Discord DM) because:
- Many users disable Discord DMs from server members
- Email provides a more reliable delivery channel

Implementation detail:
Gmail API `users().messages().send` expects a base64url encoded raw RFC 2822
message. We build that using `email.message.EmailMessage`.
"""

import base64
from email.message import EmailMessage

from googleapiclient.discovery import Resource


def _gmail_raw_message(*, from_addr: str, to_addr: str, subject: str, body: str) -> str:
    """Build a raw RFC 2822 message and return base64url-encoded content."""
    msg = EmailMessage()
    msg["To"] = to_addr
    msg["From"] = from_addr
    msg["Subject"] = subject
    msg.set_content(body, subtype="html")

    # Gmail API expects the RFC 2822 message in base64url encoding.
    return base64.urlsafe_b64encode(msg.as_bytes()).decode("ascii")


def send_email(
    gmail_sdk: Resource,
    *,
    from_addr: str,
    to_addr: str,
    subject: str,
    body: str,
):
    """Send a plain text email via Gmail API.

    Args:
        gmail_sdk: Gmail API client built with delegated credentials.
        from_addr: Must match the delegated sender mailbox in most setups.
        to_addr: Recipient.
        subject: Email subject.
        body: Plain text body.
    """
    raw = _gmail_raw_message(
        from_addr=from_addr,
        to_addr=to_addr,
        subject=subject,
        body=body,
    )
    return gmail_sdk.users().messages().send(userId="me", body={"raw": raw}).execute()
