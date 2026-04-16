"""
ADAMS Brain
===========
AI safety controller for the Advanced Driver Alertness Monitoring System.
Uses the Groq API (LLaMA 3.3-70B) to generate structured JSON safety
instructions from driver telemetry.

Authors : ADAMS Team
Version : 2.0.0
"""

import os
import json
import logging
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
AlertLevel = Literal["INFO", "WARNING", "DANGER", "ERROR"]
RouteType = Literal["FASTEST", "SCENIC", "REST_STOP"]

# ---------------------------------------------------------------------------
# System prompt — defined at module level so it is easy to audit / version
# ---------------------------------------------------------------------------
_SYSTEM_PROMPT = """
You are the ADAMS Safety Controller (Advanced Driver Alertness Monitoring System).

Analyse the driver telemetry and return a JSON safety instruction following
these rules exactly:

| Driver state                              | level    | buzzer | route      |
|-------------------------------------------|----------|--------|------------|
| Sleepy / drowsy / eyes closed             | DANGER   | true   | REST_STOP  |
| Angry / stressed / fearful / distracted   | WARNING  | false  | SCENIC     |
| Neutral / happy / calm                    | INFO     | false  | FASTEST    |

Return ONLY valid JSON with exactly these four keys:
  "level"           – one of INFO | WARNING | DANGER | ERROR  (string)
  "message"         – a natural spoken alert, maximum 8 words  (string)
  "buzzer_active"   – whether to activate the buzzer           (boolean)
  "suggested_route" – one of FASTEST | SCENIC | REST_STOP      (string)
""".strip()

_REQUIRED_KEYS: frozenset[str] = frozenset(
    {"level", "message", "buzzer_active", "suggested_route"}
)


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
        Groq model identifier to use for completions.
    temperature : float
        Sampling temperature (lower = more deterministic / consistent).
    max_tokens : int
        Upper bound on completion length.
    """

    def __init__(
        self,
        model: str = "llama-3.3-70b-versatile",
        temperature: float = 0.3,
        max_tokens: int = 150,
    ) -> None:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise EnvironmentError(
                "GROQ_API_KEY is not set. "
                "Add it to your .env file in the project root."
            )

        self.client = Groq(api_key=api_key)
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
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
            return self._default_response("INFO", "Scanning environment.", False, "FASTEST")

        if isinstance(driver_state, dict):
            driver_state = json.dumps(driver_state)

        if len(driver_state.strip()) < 3:
            return self._default_response("INFO", "Scanning environment.", False, "FASTEST")

        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {"role": "user",   "content": f"Driver Telemetry: {driver_state}"},
                ],
                response_format={"type": "json_object"},
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )

            raw: str = completion.choices[0].message.content
            return self._validate_response(raw)

        except Exception:
            logger.exception("Groq API call failed")
            return self._default_response("ERROR", "Safety AI offline.", False, "FASTEST")

    def filter_notification(self, driver_level: AlertLevel, notification_text: str) -> str:
        """
        Focus-mode guard: suppress incoming notifications when the driver is
        in a high-risk state.

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

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _validate_response(self, raw: str) -> str:
        """
        Parse the model's raw output and verify all required keys are present.
        Returns the original JSON string if valid, otherwise a safe fallback.
        """
        try:
            parsed: dict = json.loads(raw)
        except json.JSONDecodeError:
            logger.warning("Brain returned non-JSON content: %r", raw[:120])
            return self._default_response("WARNING", "Check driver status.", False, "FASTEST")

        missing = _REQUIRED_KEYS - parsed.keys()
        if missing:
            logger.warning("Brain JSON missing keys %s: %s", missing, parsed)
            return self._default_response("WARNING", "Check driver status.", False, "FASTEST")

        return raw

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
                "level": level,
                "message": message,
                "buzzer_active": buzzer_active,
                "suggested_route": suggested_route,
            }
        )


# ---------------------------------------------------------------------------
# Quick smoke test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    brain = AdamsBrain()
    print("🧠 ADAMS Brain — smoke test\n" + "-" * 60)

    test_cases = [
        "Eye openness: 5%, Drowsy: True, Emotion: Tired, Confidence: 92%",
        "Eye openness: 85%, Drowsy: False, Emotion: Angry, Confidence: 78%",
        "Eye openness: 95%, Drowsy: False, Emotion: Happy, Confidence: 88%",
    ]

    for case in test_cases:
        response = brain.generate_advice(case)
        data = json.loads(response)
        print(
            f"INPUT  : {case}\n"
            f"OUTPUT : [{data['level']}] {data['message']} | "
            f"Buzzer: {data['buzzer_active']} | Route: {data['suggested_route']}\n"
            + "-" * 60
        )