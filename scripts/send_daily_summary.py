#!/usr/bin/env python3
"""
Daily Summary Email - Executed by launchd at 8am

Generates executive summary of ARTHUR work and sends via Postmark.

Usage:
  python3 scripts/send_daily_summary.py           # Send email
  python3 scripts/send_daily_summary.py --dry-run # Preview only
  python3 scripts/send_daily_summary.py --test    # Send test email
"""

import os
import sys
import argparse
import logging
from datetime import datetime

# Add project root to path
PROJECT_ROOT = "/Users/arthurdell/ARTHUR"
sys.path.insert(0, PROJECT_ROOT)

from arthur.notifications.daily_summary import (
  generate_daily_summary,
  format_email_body,
  format_email_subject
)
from arthur.notifications.postmark import PostmarkNotifier

# Configure logging
logging.basicConfig(
  level=logging.INFO,
  format="%(asctime)s - %(levelname)s - %(message)s",
  handlers=[
    logging.StreamHandler(sys.stdout),
    logging.FileHandler(f"{PROJECT_ROOT}/logs/daily-summary.log", mode="a")
  ]
)
logger = logging.getLogger(__name__)

# Configuration
DEFAULT_RECIPIENT = "arthur.dell@dellight.ai"
DEFAULT_SENDER = "alerts@dellight.ai"


def main():
  parser = argparse.ArgumentParser(description="Send ARTHUR daily summary email")
  parser.add_argument(
    "--dry-run",
    action="store_true",
    help="Generate summary and print to stdout without sending"
  )
  parser.add_argument(
    "--test",
    action="store_true",
    help="Send a test email with sample content"
  )
  parser.add_argument(
    "--to",
    type=str,
    default=DEFAULT_RECIPIENT,
    help=f"Recipient email (default: {DEFAULT_RECIPIENT})"
  )
  parser.add_argument(
    "--hours",
    type=int,
    default=24,
    help="Hours to look back (default: 24)"
  )
  args = parser.parse_args()

  logger.info("=" * 60)
  logger.info(f"ARTHUR Daily Summary - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
  logger.info("=" * 60)

  # Check for API token
  server_token = os.getenv("POSTMARK_SERVER_TOKEN", "")
  if not server_token and not args.dry_run:
    logger.error("POSTMARK_SERVER_TOKEN environment variable not set")
    logger.error("Set it with: export POSTMARK_SERVER_TOKEN='your-token'")
    sys.exit(1)

  # Generate summary
  logger.info(f"Generating summary for last {args.hours} hours...")

  if args.test:
    # Test mode - create sample summary
    from arthur.notifications.daily_summary import DailySummary
    summary = DailySummary(
      date=datetime.now(),
      images_created=5,
      images_size_mb=12.4,
      videos_created=2,
      videos_duration_sec=45,
      carousels_created=1,
      tasks_completed=["Implemented Postmark integration", "Fixed API key security issues"],
      decisions_made=["Cognitive DNA integration deployed"],
      infrastructure_status={"ALPHA": "✅", "BETA": "✅", "GAMMA": "✅"},
      commits=["feat: add daily summary email", "fix: security improvements"],
      commit_count=2
    )
    subject = "ARTHUR Daily Summary - TEST"
  else:
    summary = generate_daily_summary(
      lookback_hours=args.hours,
      check_infrastructure=True
    )
    subject = format_email_subject(summary)

  body = format_email_body(summary)

  # Print summary
  print("\n" + "=" * 60)
  print(f"Subject: {subject}")
  print("=" * 60)
  print(body)
  print("=" * 60 + "\n")

  # Dry run - don't send
  if args.dry_run:
    logger.info("DRY RUN - Email not sent")
    return

  # Send email
  logger.info(f"Sending email to {args.to}...")

  notifier = PostmarkNotifier(server_token=server_token)
  result = notifier.send_daily_summary(
    to=args.to,
    subject=subject,
    body=body,
    from_addr=DEFAULT_SENDER
  )

  if result.success:
    logger.info(f"✅ Email sent successfully!")
    logger.info(f"   Message ID: {result.message_id}")
  else:
    logger.error(f"❌ Failed to send email: {result.error}")
    sys.exit(1)


if __name__ == "__main__":
  main()
