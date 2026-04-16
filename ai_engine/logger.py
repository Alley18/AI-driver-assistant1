"""
ADAMS Event Logger
==================
Persists driver-state events and the corresponding AI safety responses to a
rolling CSV log file.  Each row captures a full decision cycle: the raw
telemetry that triggered the AI, and the structured JSON advice it returned.

Authors : ADAMS Team
Version : 2.0.0
"""

import csv
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# Module logger
# ---------------------------------------------------------------------------
logger = logging.getLogger("adams.logger")

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
LOG_DIR: Path = Path("logs")
LOG_FILE: Path = LOG_DIR / "driving_history.csv"

_CSV_FIELDNAMES: tuple[str, ...] = (
    "timestamp",
    "input",
    "level",
    "message",
    "buzzer_active",
    "suggested_route",
)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def log_event(detection: str, ai_response_json: str) -> bool:
    """
    Append a single driver-state event to the CSV log.

    The function is intentionally fault-tolerant: it logs a warning on any
    error rather than raising, so a logging failure never crashes the pipeline.

    Parameters
    ----------
    detection : str
        The raw telemetry string that was sent to the AI brain
        (e.g. ``"Time: 14:30, Emotion: Stressed, Eye openness: 35%"``).
    ai_response_json : str
        The JSON string returned by :class:`~ai_engine.brain.AdamsBrain`.
        Expected keys: ``level``, ``message``, ``buzzer_active``,
        ``suggested_route``.

    Returns
    -------
    bool
        ``True`` if the row was written successfully, ``False`` otherwise.
    """
    try:
        data = _parse_ai_response(ai_response_json)
        if data is None:
            return False

        row = {
            "timestamp":       datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "input":           detection.strip(),
            "level":           data.get("level", "UNKNOWN"),
            "message":         data.get("message", ""),
            "buzzer_active":   data.get("buzzer_active", False),
            "suggested_route": data.get("suggested_route", "N/A"),
        }

        _ensure_log_dir()
        _write_row(row)

        logger.debug("Event logged: [%s] %s", row["level"], row["message"])
        return True

    except Exception:
        logger.exception("Unexpected error in log_event — event was NOT saved")
        return False


def read_recent_events(n: int = 50) -> list[dict]:
    """
    Return the *n* most-recent log rows as a list of dicts.

    Parameters
    ----------
    n : int
        Maximum number of rows to return (most recent first).

    Returns
    -------
    list[dict]
        Each element has the same keys as ``_CSV_FIELDNAMES``.
        Returns an empty list if the log file does not yet exist.
    """
    if not LOG_FILE.exists():
        return []

    try:
        with LOG_FILE.open(newline="", encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))
        return rows[-n:][::-1]  # most-recent first
    except Exception:
        logger.exception("Failed to read log file")
        return []


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------
def _parse_ai_response(raw_json: str) -> Optional[dict]:
    """Safely deserialise the AI response JSON string."""
    try:
        return json.loads(raw_json)
    except json.JSONDecodeError:
        logger.warning("log_event received invalid JSON — skipping row.\n  Raw: %r", raw_json[:200])
        return None


def _ensure_log_dir() -> None:
    """Create the log directory if it does not already exist."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)


def _write_row(row: dict) -> None:
    """Append *row* to the CSV log, writing a header if the file is new."""
    file_is_new = not LOG_FILE.exists() or LOG_FILE.stat().st_size == 0

    with LOG_FILE.open("a", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=_CSV_FIELDNAMES)
        if file_is_new:
            writer.writeheader()
        writer.writerow(row)


# ---------------------------------------------------------------------------
# Smoke test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    sample_detection = "Time: 14:30, Emotion: Stressed, Eye openness: 35%"
    sample_response = json.dumps({
        "level": "WARNING",
        "message": "Please pull over and rest.",
        "buzzer_active": False,
        "suggested_route": "SCENIC",
    })

    success = log_event(sample_detection, sample_response)
    print("Logged:", success)

    recent = read_recent_events(5)
    print("Recent events:", recent)