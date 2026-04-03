from deepface import DeepFace

# sample test image
img_path = "test.jpg"

result = DeepFace.analyze(img_path=img_path, actions=['emotion'])

print("Result:", result[0]["dominant_emotion"])
print("Confidence:", result[0]["emotion"][result[0]["dominant_emotion"]])