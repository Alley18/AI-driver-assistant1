from datetime import datetime

def build_emotion_response(emotion, confidence):
    response = {
        "emotion": emotion,
        "confidence": round(confidence, 2),
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "status": "success"
    }
    return response

# test
if __name__ == "__main__":
    result = build_emotion_response("happy", 0.89)
    print(result)