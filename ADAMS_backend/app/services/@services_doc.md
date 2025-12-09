# Services


## Scope/purpose
- Holds the business logic and computation separate from routes.
- Routes should not contain raw logic; instead, they call services that implement the actual functionality.


# Future plan 
- 

## Functions

def parse_feedback_response(feedback_text: str) -> Dict[str, str]:
    """Parses LLM response into structured feedback and action."""
    try:
        if "Feedback:" in feedback_text and "Recommended Action:" in feedback_text:
            feedback = feedback_text.split("Feedback:")[1].split("Recommended Action:")[0].strip()
            action = feedback_text.split("Recommended Action:")[1].strip()
        else:
            # Fallback parsing
            feedback = feedback_text.strip()
            action = "Keep up the good work and stay focused!"
        return {"feedback": feedback, "recommended_action": action}
    except Exception:
        return {
            "feedback": "Great driving session!",
            "recommended_action": "Stay safe on the road!"
        }