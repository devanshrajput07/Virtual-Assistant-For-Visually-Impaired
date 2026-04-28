import cv2
import time
import logging
import threading
from typing import Callable, Optional

logger = logging.getLogger("aura.vision.navigation")

CONFIDENCE_THRESHOLD = 0.50
MIN_OBSTACLE_AREA_RATIO = 0.02
UPDATE_INTERVAL = 2.5

def continuous_navigation(
    talk_fn: Callable[[str], None],
    duration_seconds: int = 60,
) -> None:
    from vision.object_detection import get_yolo_model
    model = get_yolo_model()

    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    if not cap.isOpened():
        talk_fn("Camera not detected. Navigation cannot start.")
        logger.warning("Navigation: camera not available.")
        return

    talk_fn("Navigation started. I will guide you for one minute.")
    logger.info("Navigation session started (duration %ds).", duration_seconds)
    
    for _ in range(20):
        cap.read()

    start_time = time.time()
    consecutive_failures = 0
    last_announce_time = 0
    last_dir = ""

    try:
        while time.time() - start_time < duration_seconds:
            scores = {"left": 0, "center": 0, "right": 0}
            large_center = False
            frames_processed = 0

            for _ in range(5):
                cap.read()

            while frames_processed < 5 and (time.time() - start_time < duration_seconds):
                ret, frame = cap.read()
                if not ret:
                    consecutive_failures += 1
                    if consecutive_failures >= 15:
                        talk_fn("Camera feed lost. Stopping navigation.")
                        return
                    time.sleep(0.05)
                    continue
                consecutive_failures = 0

                results = model(frame, stream=True, verbose=False)
                frame_h, frame_w = frame.shape[:2]

                for r in results:
                    for box in r.boxes:
                        conf = float(box.conf[0])
                        if conf < CONFIDENCE_THRESHOLD:
                            continue

                        x1, y1, x2, y2 = box.xyxy[0]
                        area = (x2 - x1) * (y2 - y1)
                        if area < (frame_h * frame_w * MIN_OBSTACLE_AREA_RATIO):
                            continue

                        cx = (x1 + x2) / 2
                        weight = 2 if area > (frame_h * frame_w * 0.10) else 1

                        if cx < frame_w / 3:
                            scores["left"] += weight
                        elif cx > frame_w * 2 / 3:
                            scores["right"] += weight
                        else:
                            scores["center"] += weight
                            if area > (frame_h * frame_w * 0.15):
                                large_center = True

                frames_processed += 1

            if frames_processed == 0:
                continue

            if all(v == 0 for v in scores.values()):
                new_dir = "clear"
            elif large_center:
                new_dir = "front_urgent"
            elif scores["center"] > max(scores["left"], scores["right"]):
                new_dir = "front_blocked"
            elif scores["left"] > scores["right"]:
                new_dir = "left_blocked"
            elif scores["right"] > scores["left"]:
                new_dir = "right_blocked"
            else:
                new_dir = "uncertain"

            now = time.time()
            if new_dir != last_dir or (now - last_announce_time) >= 5.0:
                if new_dir == "clear":
                    talk_fn("Path clear.")
                elif new_dir == "front_urgent":
                    talk_fn("WARNING — large obstacle ahead. Stop.")
                elif new_dir == "front_blocked":
                    talk_fn("Obstacle ahead. Move sideways.")
                elif new_dir == "left_blocked":
                    talk_fn("Obstacle on left. Move right.")
                elif new_dir == "right_blocked":
                    talk_fn("Obstacle on right. Move left.")
                elif new_dir == "uncertain":
                    talk_fn("Obstacles around. Move slowly.")
                
                last_dir = new_dir
                last_announce_time = now

        talk_fn("Navigation session complete.")

    finally:
        cap.release()
        cv2.destroyAllWindows()
        logger.info("Navigation session ended after %.1fs.", time.time() - start_time)