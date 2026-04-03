from flask import Flask, jsonify
from deepface import DeepFace
from datetime import datetime

app = Flask(__name__)

@app.route("/emotion-detect", methods=["GET"])
def emotion_detect():
    try:
        result = DeepFace.analyze(img_path="test.jpg", actions=["emotion"])

        emotion = result[0]["dominant_emotion"]
        confidence = float(result[0]["emotion"][emotion])

        response = {
            "emotion": emotion,
            "confidence": round(confidence, 2),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "status": "success"
        }

        return jsonify(response)

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        })

if __name__ == "__main__":
    app.run(debug=True, port=5001)