import cv2
import os
import numpy as np
from groq import Groq
from config.settings import GROQ_KEY

client = Groq(api_key=GROQ_KEY)

HAAR_CASCADE = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
face_cascade = cv2.CascadeClassifier(HAAR_CASCADE)

def detect_emotion(talk):
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    if not cap.isOpened():
        talk("Camera not detected.")
        return

    talk("Let me take a look at you.")
    best_face = None
    best_area = 0

    for _ in range(15):
        ret, frame = cap.read()
        if not ret:
            continue
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)

        for (x, y, w, h) in faces:
            area = w * h
            if area > best_area:
                best_area = area
                best_face = frame[y:y+h, x:x+w]

    cap.release()

    if best_face is None:
        talk("I couldn't see your face clearly. Please face the camera and try again.")
        return

    h, w = best_face.shape[:2]
    brightness = np.mean(best_face)
    hsv = cv2.cvtColor(best_face, cv2.COLOR_BGR2HSV)
    avg_saturation = np.mean(hsv[:, :, 1])
    avg_hue = np.mean(hsv[:, :, 0])

    face_description = (
        f"A face detected. Image properties: brightness={brightness:.0f}/255, "
        f"saturation={avg_saturation:.0f}/255, hue={avg_hue:.0f}/180, "
        f"face size={w}x{h} pixels."
    )

    prompt = (
        f"You are AURA, a caring voice assistant. Based on this camera analysis of a user's face: "
        f"{face_description}. "
        f"Make a warm, empathetic comment about how they might be feeling. "
        f"Be positive and supportive. If brightness is high, they might be in a well-lit happy environment. "
        f"If low, they might be tired. Keep response to 1-2 sentences. No markdown."
    )

    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "You are AURA, a warm and empathetic voice assistant."},
                {"role": "user", "content": prompt},
            ],
        )
        reply = response.choices[0].message.content.strip()
        talk(reply)
    except Exception as e:
        talk("I can see you, but I'm having trouble analyzing your expression right now.")
