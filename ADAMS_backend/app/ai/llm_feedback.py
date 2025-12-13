import os
import requests
import re
from typing import Dict
from pydantic import BaseModel, Field


# Global config (loaded from .env)
API_KEY = os.getenv("PERPLEXITY_API_KEY")
BASE_URL = "https://api.perplexity.ai/chat/completions"


class DrivingFeedback(BaseModel):
    feedback: str = Field(..., description="2-3 sentences of supportive, human-like feedback")
    recommended_action: str = Field(..., description="1 sentence of simple, realistic action")


def generate_driving_coach_feedback(session_summary_json: str, trend_json: str) -> Dict[str, str]:
    if not API_KEY:
        raise ValueError("PERPLEXITY_API_KEY not set")
    
    system_message = """You are a friendly, concise driving coach.
        Your job is to generate short, human-like, motivating feedback based strictly on the provided JSON summaries.

        Follow these rules:
        - Do NOT mention JSON, numbers, or trends directly.
        - Praise improvements clearly and naturally.
        - Gently acknowledge any declines without scolding.
        - Highlight ONE clear area the driver should improve next.
        - Suggest ONE simple, realistic action they can take before or during the next drive.
        - Keep the tone supportive, warm, and practical (like a real coach).
        - Output ONLY valid JSON matching the schema: feedback (2-3 sentences) and recommended_action (1 sentence).
        - Do NOT give generic advice unrelated to the detected behaviors.
        - Do not repeat any content from the input JSON.
        - Do not restate numeric values or mention trends literally.
        - Focus on interpreting the patterns naturally."""

    user_message = f"Session: {session_summary_json}\nTrend: {trend_json}"
    model = "sonar-pro"

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message}
        ],
        "max_tokens": 300,
        "temperature": 0.4, 
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "name": "driving_feedback",
                "schema": DrivingFeedback.model_json_schema()
            }
        }
    }

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }

    response = requests.post(BASE_URL, json=payload, headers=headers, timeout=30)
    response.raise_for_status()
    
    content = response.json()["choices"][0]["message"]["content"]
    feedback_data = DrivingFeedback.model_validate_json(content)
    
    return {
        "feedback": feedback_data.feedback.strip(),
        "recommended_action": feedback_data.recommended_action.strip()
    }


def parse_feedback_response(feedback_dict: Dict[str, str]) -> Dict[str, str]:
    """Legacy fallback - now rarely needed with structured outputs.
        in case someone take over this project, might try delete this and see if it affect the schema
    """
    feedback = feedback_dict.get("feedback", "")
    action = feedback_dict.get("recommended_action", "")
    
    # Ensure sentence limits as backup
    sentences = re.split(r'[.!?]+', feedback)[:3]
    feedback = '. '.join(s.strip() for s in sentences if s.strip()) + '.'
    
    return {
        "feedback": feedback,
        "recommended_action": action
    }
