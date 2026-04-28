import cv2
from ultralytics import YOLO
from groq import Groq
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
GROQ_KEY = os.getenv("GROQ_API_KEY")
client = Groq(api_key=GROQ_KEY)

# Load YOLO model
model = YOLO("models/yolov8n.pt")

def describe_scene(talk):
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    if not cap.isOpened():
        talk("Camera not detected.")
        return

    talk("Scanning your surroundings, please wait.")
    
    for _ in range(20):
        cap.read()
        
    ret, frame = cap.read()
    cap.release()

    if not ret:
        talk("I couldn’t capture the image.")
        return

    results = model(frame)
    detected_objects = []
    directions = []

    frame_w = frame.shape[1]

    for box in results[0].boxes:
        cls = int(box.cls[0])
        name = model.names[cls]
        conf = float(box.conf[0])
        if conf < 0.5:
            continue

        x1, y1, x2, y2 = box.xyxy[0]
        cx = (x1 + x2) / 2

        if cx < frame_w / 3:
            pos = "left"
        elif cx > frame_w * 2 / 3:
            pos = "right"
        else:
            pos = "center"

        detected_objects.append(name)
        directions.append(pos)

    if not detected_objects:
        talk("I couldn’t detect anything clearly around you.")
        return

    detections_text = ", ".join([f"{obj} on the {dir}" for obj, dir in zip(detected_objects, directions)])
    prompt = f"Describe this scene naturally: I detected {detections_text}."

    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "You are an assistant for the visually impaired. Describe the detected objects naturally in 1-2 sentences. DO NOT invent distances, speeds, or motion. Only state what is present based on the provided list."},
                {"role": "user", "content": prompt},
            ],
        )
        description = response.choices[0].message.content.strip()
        talk(description)
    except Exception as e:
        talk(f"Error generating scene description: {e}")