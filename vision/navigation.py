import cv2
import time
import numpy as np
from ultralytics import YOLO

model = YOLO("models/yolov8n.pt")

def continuous_navigation(talk, listen_for_stop=None, update_interval=3, session_duration=30):
    """
    Guides the user by detecting obstacles in real-time for a fixed session duration.
    """

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        talk("Camera not detected.")
        return

    talk("Navigation mode activated. I will guide you for the next 30 seconds.")

    last_direction = None
    last_update_time = time.time()
    start_time = time.time()

    while True:
        # Check if session has expired
        if time.time() - start_time > session_duration:
            talk("Navigation session completed. Ask me to guide you again if you need to keep moving.")
            break
            
        ret, frame = cap.read()
        if not ret:
            continue

        results = model(frame, stream=True)
        frame_h, frame_w = frame.shape[:2]
        directions = {"left": 0, "center": 0, "right": 0}

        for r in results:
            for box in r.boxes:
                cls = int(box.cls[0])
                name = model.names[cls]
                conf = float(box.conf[0])
                if conf < 0.5:
                    continue

                # Ignore small objects
                x1, y1, x2, y2 = box.xyxy[0]
                area = (x2 - x1) * (y2 - y1)
                if area < (frame_h * frame_w * 0.02):
                    continue

                # Determine horizontal direction
                cx = (x1 + x2) / 2
                if cx < frame_w / 3:
                    directions["left"] += 1
                elif cx > frame_w * 2 / 3:
                    directions["right"] += 1
                else:
                    directions["center"] += 1

        # Find most blocked direction
        left, center, right = directions["left"], directions["center"], directions["right"]
        new_direction = None

        if all(v == 0 for v in directions.values()):
            new_direction = "clear"
        elif center > max(left, right):
            new_direction = "front_blocked"
        elif left > right:
            new_direction = "left_blocked"
        elif right > left:
            new_direction = "right_blocked"
        else:
            new_direction = "uncertain"

        # Speak only if direction changed or enough time passed
        now = time.time()
        if new_direction != last_direction and (now - last_update_time > update_interval):
            if new_direction == "clear":
                talk("Path is clear ahead.")
            elif new_direction == "front_blocked":
                talk("Obstacle ahead. Move slightly left or right.")
            elif new_direction == "left_blocked":
                talk("Obstacle on the left. Move to your right.")
            elif new_direction == "right_blocked":
                talk("Obstacle on the right. Move to your left.")
            elif new_direction == "uncertain":
                talk("Obstacles detected around. Move slowly.")
            
            last_update_time = now
            last_direction = new_direction

    cap.release()
    cv2.destroyAllWindows()