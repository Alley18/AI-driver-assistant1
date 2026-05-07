"""
ADAMS Brain
===========
AI safety controller for the Advanced Driver Alertness Monitoring System.
Uses the Groq API (LLaMA 3.3-70B) to generate structured JSON safety
instructions from driver telemetry.

Authors : ADAMS Team
Version : 3.0.0
"""

import os
import json
import logging
import time
from typing import Literal

from groq import Groq
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logger = logging.getLogger("adams.brain")

# ---------------------------------------------------------------------------
# .env discovery — searches the module's own directory then the project root
# ---------------------------------------------------------------------------
_basedir = os.path.abspath(os.path.dirname(__file__))
for _candidate in (
    os.path.join(_basedir, ".env"),
    os.path.join(_basedir, "..", ".env"),
):
    if os.path.exists(_candidate):
        load_dotenv(_candidate)
        logger.debug("Loaded .env from %s", _candidate)
        break

# ---------------------------------------------------------------------------
# Type aliases
# ---------------------------------------------------------------------------
AlertLevel  = Literal["INFO", "WARNING", "DANGER", "ERROR"]
RouteType   = Literal["FASTEST", "SCENIC", "REST_STOP"]

# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------
_SYSTEM_PROMPT = """
You are the ADAMS Safety Controller (Advanced Driver Alertness Monitoring System).

Your sole job is to protect the driver's life. Analyse the incoming driver
telemetry and return a single JSON safety instruction following these rules:

DRIVER STATE → RESPONSE TABLE
| Condition                                        | level   | buzzer | route      |
|--------------------------------------------------|---------|--------|------------|
| Drowsy / eyes closed / eye openness < 20 %      | DANGER  | true   | REST_STOP  |
| Angry / stressed / fearful / severely distracted | WARNING | false  | SCENIC     |
| Mildly distracted (head yaw only)                | WARNING | false  | FASTEST    |
| Neutral / happy / calm / fully alert             | INFO    | false  | FASTEST    |

TONE RULES
- Messages must be calm, direct, and reassuring — never panic-inducing.
- Use second person ("You seem…", "Please…", "Time to…").
- Maximum 10 words per message. No punctuation except commas.
- Examples:
    DANGER  → "Pull over safely, you need rest now"
    WARNING → "Take a breath, stay focused on the road"
    INFO    → "All good, drive safe"

Return ONLY valid JSON — no markdown, no explanation — with exactly these keys:
  "level"           – one of INFO | WARNING | DANGER | ERROR   (string)
  "message"         – spoken alert, ≤ 10 words                  (string)
  "buzzer_active"   – true only for DANGER states               (boolean)
  "suggested_route" – one of FASTEST | SCENIC | REST_STOP       (string)
""".strip()

_REQUIRED_KEYS: frozenset[str] = frozenset(
    {"level", "message", "buzzer_active", "suggested_route"}
)

# ---------------------------------------------------------------------------
# Retry config
# ---------------------------------------------------------------------------
_MAX_RETRIES: int   = 2
_RETRY_DELAY: float = 1.5   # seconds


# ---------------------------------------------------------------------------
# Main class
# ---------------------------------------------------------------------------
class AdamsBrain:
    """
    Interfaces with the Groq API to translate raw driver telemetry into
    actionable, structured safety advice.

    Parameters
    ----------
    model : str
        Groq model identifier.
    temperature : float
        Sampling temperature (lower = more deterministic / consistent).
    max_tokens : int
        Upper bound on completion length.
    """

    def __init__(
        self,
        model: str       = "llama-3.3-70b-versatile",
        temperature: float = 0.25,
        max_tokens: int  = 160,
    ) -> None:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise EnvironmentError(
                "GROQ_API_KEY is not set. "
                "Add it to your .env file in the project root."
            )

        self.client      = Groq(api_key=api_key)
        self.model       = model
        self.temperature = temperature
        self.max_tokens  = max_tokens

        # Rolling history of the last N telemetry snapshots for context
        self._history: list[dict] = []
        self._max_history: int    = 4

        logger.info("AdamsBrain ready (model=%s).", self.model)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate_advice(self, driver_state: str | dict) -> str:
        """
        Generate a structured safety instruction from driver telemetry.

        Parameters
        ----------
        driver_state : str or dict
            Telemetry snapshot.  Dicts are serialised to JSON before sending.

        Returns
        -------
        str
            A valid JSON string with keys: level, message, buzzer_active,
            suggested_route.  Falls back to a safe default on any error.
        """
        if not driver_state:
            return self._default_response(
                "INFO", "Scanning environment.", False, "FASTEST"
            )

        if isinstance(driver_state, dict):
            driver_state = json.dumps(driver_state, ensure_ascii=False)

        if len(driver_state.strip()) < 3:
            return self._default_response(
                "INFO", "Scanning environment.", False, "FASTEST"
            )

        # Build context-aware message list
        messages = self._build_messages(driver_state)

        last_exc: Exception | None = None

        for attempt in range(1, _MAX_RETRIES + 1):
            try:
                completion = self.client.chat.completions.create(
                    model           = self.model,
                    messages        = messages,
                    response_format = {"type": "json_object"},
                    temperature     = self.temperature,
                    max_tokens      = self.max_tokens,
                )

                raw: str = completion.choices[0].message.content
                validated = self._validate_response(raw)

                # Store in rolling history
                self._push_history(driver_state, validated)

                return validated

            except Exception as exc:
                last_exc = exc
                logger.warning(
                    "Groq API attempt %d/%d failed: %s",
                    attempt, _MAX_RETRIES, exc,
                )
                if attempt < _MAX_RETRIES:
                    time.sleep(_RETRY_DELAY)

        logger.error("All Groq retries exhausted. Last error: %s", last_exc)
        return self._default_response(
            "ERROR", "Safety AI offline.", False, "FASTEST"
        )

    def filter_notification(
        self,
        driver_level: AlertLevel,
        notification_text: str,
    ) -> str:
        """
        Focus-mode guard: suppress incoming notifications when the driver
        is in a high-risk state.

        Parameters
        ----------
        driver_level : AlertLevel
            Current alert level from the latest ``generate_advice`` call.
        notification_text : str
            The notification content that would otherwise be read aloud.

        Returns
        -------
        str
            Either the original notification (with an ``[ALLOWED]`` prefix)
            or a blocked-state message.
        """
        if driver_level in ("DANGER", "WARNING"):
            return "[BLOCKED] High-risk state: focus on the road."
        return f"[ALLOWED] {notification_text}"

    def clear_history(self) -> None:
        """Wipe the rolling telemetry history (e.g. between sessions)."""
        self._history.clear()
        logger.debug("Telemetry history cleared.")

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _build_messages(self, current_telemetry: str) -> list[dict]:
        """
        Construct the full message list for the API call, prepending recent
        telemetry context so the model can detect trends (e.g. worsening).
        """
        messages: list[dict] = [
            {"role": "system", "content": _SYSTEM_PROMPT}
        ]

        # Add previous turns as context (oldest first)
        for entry in self._history:
            messages.append({
                "role":    "user",
                "content": f"Driver Telemetry: {entry['telemetry']}",
            })
            messages.append({
                "role":    "assistant",
                "content": entry["response"],
            })

        # Add current turn
        messages.append({
            "role":    "user",
            "content": f"Driver Telemetry: {current_telemetry}",
        })

        return messages

    def _push_history(self, telemetry: str, response: str) -> None:
        """Append a telemetry/response pair and trim to the rolling window."""
        self._history.append(
            {"telemetry": telemetry, "response": response}
        )
        if len(self._history) > self._max_history:
            self._history.pop(0)

    def _validate_response(self, raw: str) -> str:
        """
        Parse the model's raw output and verify all required keys are present.
        Returns the original JSON string if valid, otherwise a safe fallback.
        """
        try:
            parsed: dict = json.loads(raw)
        except json.JSONDecodeError:
            logger.warning(
                "Brain returned non-JSON content: %r", raw[:120]
            )
            return self._default_response(
                "WARNING", "Check driver status.", False, "FASTEST"
            )

        missing = _REQUIRED_KEYS - parsed.keys()
        if missing:
            logger.warning(
                "Brain JSON missing keys %s: %s", missing, parsed
            )
            return self._default_response(
                "WARNING", "Check driver status.", False, "FASTEST"
            )

        # Sanitise values to allowed ranges
        allowed_levels  = {"INFO", "WARNING", "DANGER", "ERROR"}
        allowed_routes  = {"FASTEST", "SCENIC", "REST_STOP"}

        if parsed.get("level") not in allowed_levels:
            parsed["level"] = "WARNING"
        if parsed.get("suggested_route") not in allowed_routes:
            parsed["suggested_route"] = "FASTEST"
        if not isinstance(parsed.get("buzzer_active"), bool):
            parsed["buzzer_active"] = parsed.get("level") == "DANGER"
        if not isinstance(parsed.get("message"), str) or not parsed["message"].strip():
            parsed["message"] = "Stay alert."

        return json.dumps(parsed, ensure_ascii=False)

    @staticmethod
    def _default_response(
        level: AlertLevel,
        message: str,
        buzzer_active: bool,
        suggested_route: RouteType,
    ) -> str:
        """Return a pre-built fallback JSON string (no API call required)."""
        return json.dumps(
            {
                "level":          level,
                "message":        message,
                "buzzer_active":  buzzer_active,
                "suggested_route": suggested_route,
            },
            ensure_ascii=False,
        )


# ---------------------------------------------------------------------------
# Quick smoke test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    brain = AdamsBrain()
    print("🧠 ADAMS Brain — smoke test\n" + "-" * 60)

    test_cases = [
        "Eye openness: 5%,  Drowsy: True,  Emotion: Tired,   Confidence: 92%",
        "Eye openness: 85%, Drowsy: False, Emotion: Angry,   Confidence: 78%",
        "Eye openness: 95%, Drowsy: False, Emotion: Happy,   Confidence: 88%",
        "Eye openness: 40%, Drowsy: True,  Emotion: Neutral, Confidence: 65%",
    ]

    for case in test_cases:
        response = brain.generate_advice(case)
        data     = json.loads(response)
        print(
            f"INPUT  : {case}\n"
            f"OUTPUT : [{data['level']}] {data['message']} | "
            f"Buzzer: {data['buzzer_active']} | "
            f"Route: {data['suggested_route']}\n"
            + "-" * 60
        )