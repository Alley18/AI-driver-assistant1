from deepface import DeepFace
from datetime import datetime

def process_emotion(image_path):
    result = DeepFace.analyze(img_path=image_path, actions=['emotion'])

    emotion = result[0]["dominant_emotion"]
    confidence = float(result[0]["emotion"][emotion])

    response = {
        "emotion": emotion,
        "confidence": round(confidence, 2),
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "status": "success"
    }

    return response


# test
if __name__ == "__main__":
    output = process_emotion("test.jpg")
    print(output)