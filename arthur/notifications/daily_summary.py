"""
Daily Summary Generator
Aggregates work performed in last 24 hours for executive summary email
"""

import os
import re
import subprocess
import socket
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)

# Project paths
PROJECT_ROOT = Path("/Users/arthurdell/ARTHUR")
CONTEXT_DIR = PROJECT_ROOT / ".claude" / "context"


@dataclass
class DailySummary:
  """Data structure for daily work summary"""
  date: datetime
  images_created: int = 0
  images_size_mb: float = 0.0
  videos_created: int = 0
  videos_duration_sec: float = 0.0
  carousels_created: int = 0
  tasks_completed: list[str] = field(default_factory=list)
  decisions_made: list[str] = field(default_factory=list)
  infrastructure_status: dict[str, str] = field(default_factory=dict)
  commits: list[str] = field(default_factory=list)
  commit_count: int = 0


def _get_files_created_since(directory: Path, since: datetime, extensions: list[str]) -> tuple[int, float]:
  """
  Count files created since a given time and their total size

  Args:
    directory: Directory to scan
    since: Datetime threshold
    extensions: List of file extensions to count (e.g., ['.png', '.jpg'])

  Returns:
    Tuple of (count, size_mb)
  """
  if not directory.exists():
    return 0, 0.0

  count = 0
  total_size = 0

  try:
    for f in directory.iterdir():
      if f.is_file() and f.suffix.lower() in extensions:
        try:
          mtime = datetime.fromtimestamp(f.stat().st_mtime)
          if mtime >= since:
            count += 1
            total_size += f.stat().st_size
        except (OSError, PermissionError):
          continue
  except Exception as e:
    logger.warning(f"Error scanning {directory}: {e}")

  return count, total_size / (1024 * 1024)  # Convert to MB


def _parse_progress_file(since: datetime) -> list[str]:
  """
  Extract completed tasks from progress.md

  Looks for lines with checkboxes or bullet points marked as completed
  """
  progress_file = CONTEXT_DIR / "progress.md"
  if not progress_file.exists():
    return []

  tasks = []
  try:
    content = progress_file.read_text()

    # Look for completed checkboxes: - [x] Task description
    checkbox_pattern = r'-\s*\[x\]\s*(.+)'
    for match in re.finditer(checkbox_pattern, content, re.IGNORECASE):
      task = match.group(1).strip()
      if task and len(task) > 3:
        tasks.append(task[:100])  # Truncate long tasks

    # Look for checkmark emoji: ✅ Task
    checkmark_pattern = r'✅\s*(.+)'
    for match in re.finditer(checkmark_pattern, content):
      task = match.group(1).strip()
      if task and len(task) > 3 and task not in tasks:
        tasks.append(task[:100])

  except Exception as e:
    logger.warning(f"Error parsing progress.md: {e}")

  return tasks[:10]  # Limit to 10 most recent


def _parse_decisions_file(since: datetime) -> list[str]:
  """
  Extract decisions made today from decisions.md

  Looks for headers matching today's date: ## YYYY-MM-DD:
  """
  decisions_file = CONTEXT_DIR / "decisions.md"
  if not decisions_file.exists():
    return []

  decisions = []
  today_str = since.strftime("%Y-%m-%d")

  try:
    content = decisions_file.read_text()

    # Look for date headers and extract decision titles
    # Pattern: ## 2026-01-06: Decision Title
    pattern = rf'##\s*{today_str}[:\s]+(.+)'
    for match in re.finditer(pattern, content):
      decision = match.group(1).strip()
      if decision:
        decisions.append(decision[:80])

  except Exception as e:
    logger.warning(f"Error parsing decisions.md: {e}")

  return decisions[:5]  # Limit to 5


def _get_git_commits(since: datetime) -> tuple[list[str], int]:
  """
  Get git commits from last 24 hours

  Returns:
    Tuple of (commit_messages, total_count)
  """
  commits = []
  count = 0

  try:
    result = subprocess.run(
      ["git", "log", "--since=24 hours ago", "--oneline", "--no-merges"],
      cwd=PROJECT_ROOT,
      capture_output=True,
      text=True,
      timeout=10
    )

    if result.returncode == 0 and result.stdout.strip():
      lines = result.stdout.strip().split('\n')
      count = len(lines)
      # Get first 5 commit messages (without hash)
      for line in lines[:5]:
        parts = line.split(' ', 1)
        if len(parts) > 1:
          commits.append(parts[1][:60])

  except Exception as e:
    logger.warning(f"Error getting git commits: {e}")

  return commits, count


def _check_infrastructure() -> dict[str, str]:
  """
  Check infrastructure health status

  Returns:
    Dict of service -> status emoji
  """
  status = {}

  # Check ALPHA (local)
  status["ALPHA"] = "✅"

  # Check BETA
  try:
    import urllib.request
    with urllib.request.urlopen("http://beta:8420/health", timeout=5) as r:
      status["BETA"] = "✅" if r.status == 200 else "❌"
  except:
    status["BETA"] = "❌"

  # Check GAMMA
  try:
    import urllib.request
    with urllib.request.urlopen("http://gamma:8421/health", timeout=5) as r:
      status["GAMMA"] = "✅" if r.status == 200 else "❌"
  except:
    status["GAMMA"] = "❌"

  return status


def generate_daily_summary(
  lookback_hours: int = 24,
  check_infrastructure: bool = True
) -> DailySummary:
  """
  Generate summary of work performed in the last N hours

  Args:
    lookback_hours: How many hours to look back (default 24)
    check_infrastructure: Whether to ping infrastructure endpoints

  Returns:
    DailySummary dataclass with aggregated data
  """
  now = datetime.now()
  since = now - timedelta(hours=lookback_hours)

  summary = DailySummary(date=now)

  # Count images
  images_dir = PROJECT_ROOT / "images"
  summary.images_created, summary.images_size_mb = _get_files_created_since(
    images_dir, since, ['.png', '.jpg', '.jpeg', '.webp']
  )

  # Count videos
  videos_dir = PROJECT_ROOT / "videos"
  summary.videos_created, videos_size = _get_files_created_since(
    videos_dir, since, ['.mp4', '.mov', '.webm']
  )
  # Rough estimate: assume 10s per video on average
  summary.videos_duration_sec = summary.videos_created * 10

  # Count carousels (directories)
  carousels_dir = PROJECT_ROOT / "carousels"
  if carousels_dir.exists():
    for d in carousels_dir.iterdir():
      if d.is_dir():
        try:
          mtime = datetime.fromtimestamp(d.stat().st_mtime)
          if mtime >= since:
            summary.carousels_created += 1
        except:
          continue

  # Parse state files
  summary.tasks_completed = _parse_progress_file(since)
  summary.decisions_made = _parse_decisions_file(since)

  # Git commits
  summary.commits, summary.commit_count = _get_git_commits(since)

  # Infrastructure status
  if check_infrastructure:
    summary.infrastructure_status = _check_infrastructure()

  return summary


def format_email_body(summary: DailySummary) -> str:
  """
  Format DailySummary as email body text

  Args:
    summary: DailySummary dataclass

  Returns:
    Formatted plain text email body
  """
  hostname = socket.gethostname()
  date_str = summary.date.strftime("%Y-%m-%d")
  time_str = summary.date.strftime("%H:%M")

  lines = [
    f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
    "",
    "📊 PRODUCTION METRICS (Last 24 Hours)",
  ]

  # Metrics
  if summary.images_created > 0:
    lines.append(f"  • Images: {summary.images_created} created ({summary.images_size_mb:.1f}MB)")
  else:
    lines.append("  • Images: 0 created")

  if summary.videos_created > 0:
    lines.append(f"  • Videos: {summary.videos_created} generated ({summary.videos_duration_sec:.0f}s total)")
  else:
    lines.append("  • Videos: 0 generated")

  if summary.carousels_created > 0:
    lines.append(f"  • Carousels: {summary.carousels_created} projects")

  lines.append("")

  # Work completed
  if summary.tasks_completed:
    lines.append("🎯 WORK COMPLETED")
    for task in summary.tasks_completed[:5]:
      lines.append(f"  • {task}")
    lines.append("")

  # Decisions
  if summary.decisions_made:
    lines.append(f"🏗️ DECISIONS MADE ({len(summary.decisions_made)})")
    for decision in summary.decisions_made:
      lines.append(f"  • {decision}")
    lines.append("")

  # Infrastructure
  if summary.infrastructure_status:
    lines.append("🔧 INFRASTRUCTURE STATUS")
    status_line = "  "
    for name, status in summary.infrastructure_status.items():
      status_line += f"{name}: {status}  "
    lines.append(status_line.rstrip())
    lines.append("")

  # Code changes
  if summary.commit_count > 0:
    lines.append("📝 CODE CHANGES")
    lines.append(f"  • {summary.commit_count} commits")
    if summary.commits:
      for commit in summary.commits[:3]:
        lines.append(f"    - {commit}")
    lines.append("")

  lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
  lines.append(f"Generated by ARTHUR on {hostname} at {time_str}")

  return "\n".join(lines)


def format_email_subject(summary: DailySummary) -> str:
  """Generate email subject line"""
  date_str = summary.date.strftime("%Y-%m-%d")
  return f"ARTHUR Daily Summary - {date_str}"
