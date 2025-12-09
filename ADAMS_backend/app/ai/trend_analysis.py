import numpy as np
from sklearn.linear_model import LinearRegression

def compute_linear_trend(values):
    """
    values = [v1, v2, v3, ...]
    returns slope (positive/negative), and interpretation label
    """
    if len(values) < 3:
        return 0, "not enough data"

    X = np.arange(len(values)).reshape(-1, 1)
    y = np.array(values)

    model = LinearRegression().fit(X, y)
    slope = model.coef_[0]

    if slope > 0.5:
        label = "increasing"
    elif slope < -0.5:
        label = "decreasing"
    else:
        label = "stable"

    return slope, label


def analyze_driver_trends(summary):
    """
    summary = list of session_summary.json objects
    """

    # === Extract Lists ===
    total_events = [s["total_events"] for s in summary]

    yawns = [s["event_counts"]["yawn_detected"] for s in summary]
    eyes_closed = [s["event_counts"]["eyes_closed_too_long"] for s in summary]
    distracted_events = [s["event_counts"]["distraction_detected"] for s in summary]
    drowsy_events = [s["event_counts"]["drowsiness_detected"] for s in summary]

    eyes_closed_seconds = [s["episode_durations"]["total_eyes_closed_seconds"] for s in summary]
    drowsy_seconds = [s["episode_durations"]["total_drowsy_seconds"] for s in summary]
    distracted_seconds = [s["episode_durations"]["total_distracted_seconds"] for s in summary]

    # === Apply Linear Regression ===
    total_events_trend = compute_linear_trend(total_events)
    yawn_trend = compute_linear_trend(yawns)
    eyes_closed_trend = compute_linear_trend(eyes_closed)
    distracted_events_trend = compute_linear_trend(distracted_events)
    drowsy_event_trend = compute_linear_trend(drowsy_events)

    eyes_closed_duration_trend = compute_linear_trend(eyes_closed_seconds)
    drowsy_duration_trend = compute_linear_trend(drowsy_seconds)
    distracted_duration_trend = compute_linear_trend(distracted_seconds)

    # === Build Result ===
    trends = {
        "events": {
            "total_events_trend": total_events_trend,
            "yawn_trend": yawn_trend,
            "eyes_closed_trend": eyes_closed_trend,
            "distracted_eventsiation_trend": distracted_events_trend,
            "drowsiness_events_trend": drowsy_event_trend
        },
        "durations": {
            "eyes_closed_duration_trend": eyes_closed_duration_trend,
            "drowsy_duration_trend": drowsy_duration_trend,
            "distracted_duration_trend": distracted_duration_trend
        }
    }

    return trends

