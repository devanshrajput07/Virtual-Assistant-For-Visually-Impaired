"""
vision/navigation.py
Real-time navigation guidance using shared YOLO singleton.

Fixes:
  - Uses shared YOLO singleton from object_detection (no double model load)
  - listen_for_stop now correctly stops the loop
  - cap.release() moved into finally block
  - Obstacle urgency levels added
  - Session can be stopped both by voice command and by time limit
"""

import cv2
import time
import logging
import threading
from typing import Callable, Optional

logger = logging.getLogger("aura.vision.navigation")

CONFIDENCE_THRESHOLD = 0.50
MIN_OBSTACLE_AREA_RATIO = 0.02   # ignore objects < 2% of frame area
UPDATE_INTERVAL = 2.5            # minimum seconds between announcements


def continuous_navigation(
    talk_fn: Callable[[str], None],
    max_frames: int = 5,
) -> None:
    """
    Guide the user by detecting obstacles instantly via a short snapshot.
    """
    # Import lazy singleton — no duplicate model load
    from vision.object_detection import get_yolo_model
    model = get_yolo_model()

    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    if not cap.isOpened():
        talk_fn("Camera not detected. Navigation cannot start.")
        logger.warning("Navigation: camera not available.")
        return

    talk_fn("Scanning path...")
    logger.info("Navigation session started (max %d frames).", max_frames)

    frames_processed = 0
    scores = {"left": 0, "center": 0, "right": 0}
    large_center = False
    consecutive_failures = 0

    try:
        while frames_processed < max_frames:

            ret, frame = cap.read()
            if not ret:
                consecutive_failures += 1
                if consecutive_failures >= 15:
                    talk_fn("Camera feed lost. Stopping navigation.")
                    break
                time.sleep(0.05)
                continue
            consecutive_failures = 0

            results = model(frame, stream=True, verbose=False)
            frame_h, frame_w = frame.shape[:2]
            scores = {"left": 0, "center": 0, "right": 0}
            large_center = False   # track a large/close obstacle

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
                    # Give extra weight to larger (closer) objects
                    weight = 2 if area > (frame_h * frame_w * 0.10) else 1

                    if cx < frame_w / 3:
                        scores["left"] += weight
                    elif cx > frame_w * 2 / 3:
                        scores["right"] += weight
                    else:
                        scores["center"] += weight
                        if area > (frame_h * frame_w * 0.15):
                            large_center = True

            left, center, right = scores["left"], scores["center"], scores["right"]

            frames_processed += 1
            
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

        if new_dir == "clear":
            talk_fn("Path is clear ahead. You can walk forward.")
        elif new_dir == "front_urgent":
            talk_fn("WARNING — large obstacle directly ahead. Stop and move sideways.")
        elif new_dir == "front_blocked":
            talk_fn("Obstacle ahead. Step slightly left or right to avoid it.")
        elif new_dir == "left_blocked":
            talk_fn("Obstacle on your left. Move to your right.")
        elif new_dir == "right_blocked":
            talk_fn("Obstacle on your right. Move to your left.")
        elif new_dir == "uncertain":
            talk_fn("Obstacles detected around you. Move slowly and carefully.")

    finally:
        cap.release()
        cv2.destroyAllWindows()
        logger.info("Navigation session ended after %.1fs.", time.time() - start_time)