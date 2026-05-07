"""
ADAMS Brain
===========
AI safety controller for the Advanced Driver Alertness Monitoring System.
Uses the Groq API (LLaMA 3.3-70B) to generate structured JSON safety
instructions from driver telemetry AND power a full conversational
driving assistant.

Authors : ADAMS Team
Version : 3.0.0
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
RouteType  = Literal["FASTEST", "SCENIC", "REST_STOP"]

# ---------------------------------------------------------------------------
# System prompt — structured safety alert (unchanged from v2)
# ---------------------------------------------------------------------------
_SAFETY_SYSTEM_PROMPT = """
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

# ---------------------------------------------------------------------------
# Conversational assistant system prompt — v3 addition
# ---------------------------------------------------------------------------
_ASSISTANT_SYSTEM_PROMPT = """
You are ADAMS, an intelligent in-car AI driving assistant — like a calm,
knowledgeable co-pilot sitting in the passenger seat.

Your personality:
- Warm, clear, and concise. Never robotic.
- Proactive about safety but never preachy.
- You speak like a trusted friend who happens to know everything about
  driving, navigation, vehicle health, and road conditions.

Your capabilities:
- Answer questions about the current route, ETA, traffic, or nearby places.
- Give driving tips, safety reminders, and wellness nudges.
- Help with vehicle-related questions (tyre pressure, fuel economy, etc.).
- Play music, set reminders, send messages — describe what you would do.
- Make small talk to keep drowsy drivers engaged if needed.
- Respond to emergencies calmly and with clear action steps.

Current driver context will be injected into each message so you can
personalise your responses (e.g. if they are drowsy, steer the conversation
toward taking a break; if they are happy and calm, be lighter in tone).

Rules:
- Keep spoken responses short: 1-3 sentences unless the driver asks for detail.
- Never read out URLs or complex data — summarise in plain English.
- If the driver sounds confused or stressed, simplify your language.
- Always prioritise safety over any other task.
""".strip()

_REQUIRED_KEYS: frozenset[str] = frozenset(
    {"level", "message", "buzzer_active", "suggested_route"}
)


# ---------------------------------------------------------------------------
# Main class
# ---------------------------------------------------------------------------
class AdamsBrain:
    """
    Dual-mode AI brain for ADAMS:

    1. **Safety mode** (``generate_advice``):
       Translates raw driver telemetry into structured JSON safety alerts —
       unchanged from v2.

    2. **Assistant mode** (``chat``):
       Full conversational driving assistant with persistent memory.
       Maintains a rolling conversation history so the driver can ask
       follow-up questions naturally.

    Parameters
    ----------
    model : str
        Groq model identifier to use for completions.
    temperature : float
        Sampling temperature (lower = more deterministic / consistent).
    max_tokens : int
        Upper bound on completion length.
    max_history_turns : int
        How many conversation turns to keep in memory (older turns are
        dropped to stay within the model's context window).
    """

    def __init__(
        self,
        model: str = "llama-3.3-70b-versatile",
        temperature: float = 0.3,
        max_tokens: int = 150,
        max_history_turns: int = 10,
    ) -> None:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise EnvironmentError(
                "GROQ_API_KEY is not set. "
                "Add it to your .env file in the project root."
            )

        self.client            = Groq(api_key=api_key)
        self.model             = model
        self.temperature       = temperature
        self.max_tokens        = max_tokens
        self.max_history_turns = max_history_turns

        # Conversation history for the assistant (list of role/content dicts)
        self._history: list[dict] = []

        # Latest driver context — injected automatically into every chat turn
        self._driver_context: str = "Driver state unknown."

        logger.info("AdamsBrain v3 ready (model=%s).", self.model)

    # ------------------------------------------------------------------
    # Context management
    # ------------------------------------------------------------------

    def update_driver_context(self, state: str | dict) -> None:
        """
        Update the stored driver telemetry context.

        Call this every time new telemetry arrives so that the
        conversational assistant always has up-to-date context when
        the driver speaks.

        Parameters
        ----------
        state : str or dict
            Latest driver telemetry snapshot.
        """
        if isinstance(state, dict):
            state = json.dumps(state)
        self._driver_context = state
        logger.debug("Driver context updated: %s", state[:80])

    def clear_history(self) -> None:
        """Wipe the conversation history (e.g. at the start of a new trip)."""
        self._history = []
        logger.info("Conversation history cleared.")

    # ------------------------------------------------------------------
    # Safety mode (v2 — unchanged)
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

        # Keep driver context in sync automatically
        self.update_driver_context(driver_state)

        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": _SAFETY_SYSTEM_PROMPT},
                    {"role": "user",   "content": f"Driver Telemetry: {driver_state}"},
                ],
                response_format={"type": "json_object"},
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )

            raw: str = completion.choices[0].message.content
            return self._validate_response(raw)

        except Exception:
            logger.exception("Groq API call failed (safety mode)")
            return self._default_response("ERROR", "Safety AI offline.", False, "FASTEST")

    # ------------------------------------------------------------------
    # Assistant mode (v3 — new)
    # ------------------------------------------------------------------

    def chat(self, driver_utterance: str) -> str:
        """
        Have a natural conversation with the driver.

        The latest driver telemetry context (set via ``update_driver_context``
        or automatically by ``generate_advice``) is injected into every turn
        so the assistant can tailor its responses to the driver's current state.

        Parameters
        ----------
        driver_utterance : str
            What the driver said (transcribed speech from AdamsEars).

        Returns
        -------
        str
            The assistant's spoken response (plain text, ready for AdamsVoice).
        """
        if not driver_utterance or not driver_utterance.strip():
            return "I didn't catch that — could you say it again?"

        # Build a context-enriched user message
        enriched_message = (
            f"[Driver telemetry: {self._driver_context}]\n"
            f"Driver says: {driver_utterance}"
        )

        # Append the new user turn to history
        self._history.append({"role": "user", "content": enriched_message})

        # Trim history to avoid context overflow
        # Keep the most recent N *pairs* of turns (user + assistant)
        max_messages = self.max_history_turns * 2
        if len(self._history) > max_messages:
            self._history = self._history[-max_messages:]

        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": _ASSISTANT_SYSTEM_PROMPT},
                    *self._history,
                ],
                temperature=self.temperature,
                max_tokens=300,   # Allow longer conversational replies
            )

            reply: str = completion.choices[0].message.content.strip()

            # Store the assistant turn so follow-ups have context
            self._history.append({"role": "assistant", "content": reply})

            return reply

        except Exception:
            logger.exception("Groq API call failed (assistant mode)")
            fallback = "I'm having trouble connecting. Please keep your eyes on the road."
            self._history.append({"role": "assistant", "content": fallback})
            return fallback

    # ------------------------------------------------------------------
    # Notification filter (v2 — unchanged)
    # ------------------------------------------------------------------

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
    print("🧠 ADAMS Brain v3 — smoke test\n" + "=" * 60)

    # ── Safety mode tests (v2 unchanged) ────────────────────────────────
    print("\n[SAFETY MODE]\n" + "-" * 60)
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

    # ── Assistant mode tests (v3 new) ───────────────────────────────────
    print("\n[ASSISTANT MODE]\n" + "-" * 60)

    # Simulate a drowsy driver asking for help
    brain.update_driver_context("Eye openness: 10%, Drowsy: True, Emotion: Tired")
    questions = [
        "How far is the next rest stop?",
        "Can you play something to keep me awake?",
        "What was that song you just played?",  # follow-up — tests memory
    ]
    for q in questions:
        answer = brain.chat(q)
        print(f"DRIVER : {q}")
        print(f"ADAMS  : {answer}\n" + "-" * 60)