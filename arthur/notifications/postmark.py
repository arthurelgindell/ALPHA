"""
Postmark Email Client
Send transactional emails via Postmark API
"""

import os
import json
import logging
from dataclasses import dataclass
from typing import Optional
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

logger = logging.getLogger(__name__)


@dataclass
class EmailResult:
  """Result from sending an email"""
  success: bool
  message_id: Optional[str] = None
  error: Optional[str] = None
  to: Optional[str] = None


class PostmarkNotifier:
  """
  Send emails via Postmark API

  Usage:
    notifier = PostmarkNotifier()
    result = notifier.send(
      to="recipient@example.com",
      subject="Hello",
      body="Message content"
    )
  """

  API_URL = "https://api.postmarkapp.com/email"

  def __init__(self, server_token: Optional[str] = None):
    """
    Initialize Postmark client

    Args:
      server_token: Postmark Server API token. If not provided,
                   reads from POSTMARK_SERVER_TOKEN env var.
    """
    self.server_token = server_token or os.getenv("POSTMARK_SERVER_TOKEN", "")
    if not self.server_token:
      logger.warning("No Postmark server token provided")

  def send(
    self,
    to: str,
    subject: str,
    body: str,
    from_addr: Optional[str] = None,
    html_body: Optional[str] = None,
    tag: Optional[str] = None,
    message_stream: str = "outbound"
  ) -> EmailResult:
    """
    Send an email via Postmark

    Args:
      to: Recipient email address
      subject: Email subject line
      body: Plain text email body
      from_addr: Sender email (must be verified in Postmark)
      html_body: Optional HTML version of body
      tag: Optional tag for tracking
      message_stream: Postmark message stream (default: outbound)

    Returns:
      EmailResult with success status and message ID
    """
    if not self.server_token:
      return EmailResult(
        success=False,
        error="No Postmark server token configured",
        to=to
      )

    # Default sender to recipient if not specified
    sender = from_addr or to

    # Build request payload
    payload = {
      "From": sender,
      "To": to,
      "Subject": subject,
      "TextBody": body,
      "MessageStream": message_stream
    }

    if html_body:
      payload["HtmlBody"] = html_body

    if tag:
      payload["Tag"] = tag

    try:
      # Create request
      request = Request(
        self.API_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
          "Accept": "application/json",
          "Content-Type": "application/json",
          "X-Postmark-Server-Token": self.server_token
        },
        method="POST"
      )

      # Send request
      with urlopen(request, timeout=30) as response:
        result = json.loads(response.read().decode("utf-8"))

        logger.info(f"Email sent successfully to {to}: {result.get('MessageID')}")

        return EmailResult(
          success=True,
          message_id=result.get("MessageID"),
          to=to
        )

    except HTTPError as e:
      error_body = e.read().decode("utf-8") if e.fp else str(e)
      logger.error(f"Postmark API error: {e.code} - {error_body}")
      return EmailResult(
        success=False,
        error=f"HTTP {e.code}: {error_body}",
        to=to
      )

    except URLError as e:
      logger.error(f"Network error sending email: {e}")
      return EmailResult(
        success=False,
        error=f"Network error: {e.reason}",
        to=to
      )

    except Exception as e:
      logger.error(f"Unexpected error sending email: {e}")
      return EmailResult(
        success=False,
        error=str(e),
        to=to
      )

  def send_daily_summary(
    self,
    to: str,
    subject: str,
    body: str,
    from_addr: Optional[str] = None
  ) -> EmailResult:
    """
    Send daily summary email with appropriate tag

    Args:
      to: Recipient email
      subject: Email subject
      body: Email body text
      from_addr: Sender email (defaults to recipient)

    Returns:
      EmailResult
    """
    return self.send(
      to=to,
      subject=subject,
      body=body,
      from_addr=from_addr,
      tag="daily-summary"
    )
