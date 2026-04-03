from deepface import DeepFace

img_path = "test.jpg"

result = DeepFace.analyze(img_path=img_path, actions=["emotion"])

# Clean output
emotion = result[0]["dominant_emotion"]
confidence = result[0]["face_confidence"]

print("Detected Emotion:", emotion)
print("Confidence:", confidence)