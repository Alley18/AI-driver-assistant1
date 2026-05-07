"""
ADAMS Event Logger
==================
Persists driver-state events and the corresponding AI safety responses to a
rolling CSV log file.

Authors : ADAMS Team
Version : 2.1.0
"""

import csv
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger("adams.logger")

LOG_DIR: Path = Path("logs")
LOG_FILE: Path = LOG_DIR / "driving_history.csv"

_CSV_FIELDNAMES: tuple[str, ...] = (
    "timestamp",
    "input",
    "level",
    "message",
    "spoken_text",
    "buzzer",
    "driver_state",
    "trigger",
    "suggested_route",
)


def log_event(detection: str, ai_response_json: str) -> bool:
    """
    Append a single event row to the CSV log.

    detection:
        Can be either:
        - plain telemetry string
        - JSON string containing structured live alert data

    ai_response_json:
        Can be either:
        - JSON from AdamsBrain
        - lightweight JSON for instant voice alerts
    """
    try:
        detection_data = _parse_json_if_possible(detection)
        ai_data = _parse_json_if_possible(ai_response_json)

        row = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "input": "",
            "level": "INFO",
            "message": "",
            "spoken_text": "",
            "buzzer": False,
            "driver_state": "Monitoring",
            "trigger": "",
            "suggested_route": "N/A",
        }

        # Detection side
        if isinstance(detection_data, dict):
            row["timestamp"] = str(detection_data.get("timestamp", row["timestamp"]))
            row["input"] = str(detection_data.get("input", ""))
            row["level"] = str(detection_data.get("level", row["level"]))
            row["message"] = str(detection_data.get("message", ""))
            row["spoken_text"] = str(
                detection_data.get("spoken_text")
                or detection_data.get("message")
                or ""
            )
            row["buzzer"] = _to_bool(detection_data.get("buzzer", False))
            row["driver_state"] = str(
                detection_data.get("driver_state")
                or detection_data.get("trigger")
                or row["driver_state"]
            )
            row["trigger"] = str(detection_data.get("trigger", ""))
        else:
            row["input"] = str(detection).strip()

        # AI response side
        if isinstance(ai_data, dict):
            row["level"] = str(ai_data.get("level", row["level"]))
            row["message"] = str(ai_data.get("message", row["message"]))
            row["spoken_text"] = str(
                ai_data.get("spoken_text")
                or ai_data.get("message")
                or row["spoken_text"]
            )
            row["buzzer"] = _to_bool(
                ai_data.get("buzzer", ai_data.get("buzzer_active", row["buzzer"]))
            )
            row["suggested_route"] = str(
                ai_data.get("suggested_route", row["suggested_route"])
            )
            row["driver_state"] = str(
                ai_data.get("driver_state", row["driver_state"])
            )

        if not row["message"] and row["spoken_text"]:
            row["message"] = row["spoken_text"]

        if not row["spoken_text"] and row["message"]:
            row["spoken_text"] = row["message"]

        _ensure_log_dir()
        _write_row(row)

        logger.debug("Event logged: [%s] %s", row["level"], row["message"])
        return True

    except Exception:
        logger.exception("Unexpected error in log_event — event was NOT saved")
        return False


def read_recent_events(n: int = 50) -> list[dict]:
    if not LOG_FILE.exists():
        return []

    try:
        with LOG_FILE.open(newline="", encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))
        return rows[-n:][::-1]
    except Exception:
        logger.exception("Failed to read log file")
        return []


def _parse_json_if_possible(raw: str) -> Optional[dict]:
    try:
        parsed = json.loads(raw)
        return parsed if isinstance(parsed, dict) else None
    except Exception:
        return None


def _to_bool(value) -> bool:
    return str(value).strip().lower() in ("true", "1", "yes")


def _ensure_log_dir() -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)


def _write_row(row: dict) -> None:
    file_is_new = not LOG_FILE.exists() or LOG_FILE.stat().st_size == 0

    with LOG_FILE.open("a", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=_CSV_FIELDNAMES)
        if file_is_new:
            writer.writeheader()
        writer.writerow(row)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    sample_detection = json.dumps({
        "timestamp": "2026-04-16 20:10:00",
        "trigger": "VOICE_DROWSY",
        "input": "Eyes closed detected",
        "level": "WARNING",
        "message": "Wake up!",
        "spoken_text": "Wake up!",
        "buzzer": True,
        "driver_state": "Drowsy",
    })

    sample_response = json.dumps({
        "level": "WARNING",
        "message": "Please pull over and rest.",
        "buzzer": True,
        "suggested_route": "SCENIC",
    })

    success = log_event(sample_detection, sample_response)
    print("Logged:", success)
    print(read_recent_events(5))