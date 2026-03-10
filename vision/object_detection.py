"""
object_detection.py
Enhanced version — Stable, Accurate, and Always Speaks Out Results
"""

from ultralytics import YOLO
import cv2
import numpy as np
import time


# Load YOLOv8 small model
model = YOLO("models/yolov8s.pt")


def detect_objects_from_camera(talk, target=None, max_frames=30, show_view=False):
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        talk("Camera not detected.")
        return

    talk("Scanning the area, please wait.")
    detected_objects = []
    frame_count = 0

    while frame_count < max_frames:
        ret, frame = cap.read()
        if not ret:
            continue

        results = model(frame, stream=True)
        frame_count += 1

        for result in results:
            for box in result.boxes:
                cls = int(box.cls[0])
                name = model.names[cls]
                conf = float(box.conf[0])

                if conf < 0.45:
                    continue

                x1, y1, x2, y2 = map(int, box.xyxy[0])
                cx = (x1 + x2) / 2

                norm_cx = cx / frame.shape[1]

                if norm_cx < 0.4:
                    direction = "left"
                elif norm_cx > 0.6:
                    direction = "right"
                else:
                    direction = "center"

                detected_objects.append((name.lower(), direction))

                if show_view:
                    color = (0, 255, 0)
                    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                    cv2.putText(
                        frame,
                        f"{name} ({direction})",
                        (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.6,
                        color,
                        2,
                    )

        if show_view:
            cv2.imshow("Live Object Detection", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    cap.release()
    cv2.destroyAllWindows()

    if not detected_objects:
        talk("I couldn't detect any objects clearly.")
        return

    summary = {}
    for obj, direction in detected_objects:
        if obj not in summary:
            summary[obj] = []
        summary[obj].append(direction)

    stable_summary = {obj: max(set(dirs), key=dirs.count) for obj, dirs in summary.items()}

    

    # If a target object was specified (like “phone”)
    if target:
        target = target.lower().strip()
        found = False
        for obj, direction in stable_summary.items():
            if target in obj or obj in target:
                talk(f"I see your {target} on the {direction}.")
                found = True
                break
        if not found:
            talk(f"I couldn't find your {target} around.")
    else:
        sentence = ", ".join(f"{obj} on the {dir}" for obj, dir in stable_summary.items())
        talk(f"I can see {sentence}.")