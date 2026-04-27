"""
vision/object_detection.py
YOLO-based object detection with:
  - Lazy-loaded singleton model (no import-time crash)
  - MiDaS depth integration for distance announcements
  - Fixed frame-failure handling
  - Configurable confidence threshold
"""

import cv2
import logging
import time
from typing import Optional

logger = logging.getLogger("aura.vision.detection")

_yolo_model = None
YOLO_MODEL_PATH = "models/yolov8s.pt"
CONFIDENCE_THRESHOLD = 0.50
MAX_CONSECUTIVE_FAILURES = 10


def get_yolo_model():
    """Lazy-load and cache the YOLO model."""
    global _yolo_model
    if _yolo_model is None:
        try:
            from ultralytics import YOLO
            logger.info("Loading YOLO model from %s …", YOLO_MODEL_PATH)
            _yolo_model = YOLO(YOLO_MODEL_PATH)
            logger.info("YOLO model loaded successfully.")
        except Exception as exc:
            logger.error("Failed to load YOLO model: %s", exc)
            raise RuntimeError(f"YOLO model unavailable: {exc}") from exc
    return _yolo_model



def _depth_to_label(avg_depth: float) -> str:
    """
    MiDaS returns inverse relative depth (higher value = closer).
    Buckets derived from empirical testing.
    """
    if avg_depth > 0.75:
        return "very close"
    elif avg_depth > 0.50:
        return "close"
    elif avg_depth > 0.25:
        return "nearby"
    else:
        return "far away"


def _try_get_depth(frame, x1: int, y1: int, x2: int, y2: int) -> Optional[str]:
    """Best-effort depth estimation — returns human label or None."""
    try:
        from vision.depth_estimation import estimate_object_distance
        boxes = [(x1, y1, x2, y2, "obj")]
        distances = estimate_object_distance(frame, boxes)
        if distances:
            _, avg_depth = distances[0]
            return _depth_to_label(avg_depth)
    except Exception as exc:
        logger.debug("Depth estimation skipped: %s", exc)
    return None



def detect_objects_from_camera(talk_fn, target: Optional[str] = None, max_frames: int = 30, show_view: bool = False) -> None:
    """
    Scan the camera for up to `max_frames` and announce detected objects.

    Args:
        talk_fn:    Voice output function.
        target:     Optional specific object to locate (e.g. "phone").
        max_frames: Number of frames to analyse before summarising.
        show_view:  Whether to display an OpenCV window (desktop only).
    """
    model = get_yolo_model()

    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    if not cap.isOpened():
        talk_fn("Camera not detected. Please ensure a camera is connected.")
        logger.warning("Camera not available.")
        return

    talk_fn("Scanning the area, please wait.")
    detected_objects: list[tuple[str, str, str]] = []  # (name, direction, distance_label)
    frame_count = 0
    consecutive_failures = 0

    try:
        while frame_count < max_frames:
            ret, frame = cap.read()
            if not ret:
                consecutive_failures += 1
                if consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
                    logger.warning("Camera feed dropped after %d consecutive failures.", consecutive_failures)
                    break
                time.sleep(0.05)
                continue
            consecutive_failures = 0

            results = model(frame, stream=True, verbose=False)
            frame_count += 1
            frame_h, frame_w = frame.shape[:2]

            for result in results:
                for box in result.boxes:
                    cls = int(box.cls[0])
                    name = model.names[cls]
                    conf = float(box.conf[0])

                    if conf < CONFIDENCE_THRESHOLD:
                        continue

                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    cx = (x1 + x2) / 2
                    norm_cx = cx / frame_w

                    if norm_cx < 0.35:
                        direction = "left"
                    elif norm_cx > 0.65:
                        direction = "right"
                    else:
                        direction = "directly ahead"

                    dist_label = _try_get_depth(frame, x1, y1, x2, y2) or ""
                    detected_objects.append((name.lower(), direction, dist_label))

                    if show_view:
                        color = (0, 200, 100)
                        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                        label = f"{name} ({direction})"
                        cv2.putText(frame, label, (x1, y1 - 10),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 2)

            if show_view:
                cv2.imshow("AURA — Object Detection", frame)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break

    finally:
        cap.release()
        cv2.destroyAllWindows()

    if not detected_objects:
        talk_fn("I couldn't detect any objects clearly. Please make sure the camera has a clear view.")
        return

    # Count most common direction per object
    summary: dict[str, list[tuple[str, str]]] = {}
    for obj, direction, dist in detected_objects:
        summary.setdefault(obj, []).append((direction, dist))

    stable: dict[str, tuple[str, str]] = {}
    for obj, entries in summary.items():
        best_dir = max(set(e[0] for e in entries), key=lambda d: sum(1 for e in entries if e[0] == d))
        dist_labels = [e[1] for e in entries if e[1]]
        best_dist = max(set(dist_labels), key=dist_labels.count) if dist_labels else ""
        stable[obj] = (best_dir, best_dist)

    if target:
        target_lower = target.lower().strip()
        for obj, (direction, dist) in stable.items():
            if target_lower in obj or obj in target_lower:
                distance_info = f", {dist}" if dist else ""
                talk_fn(f"I found your {target_lower} on the {direction}{distance_info}.")
                return
        talk_fn(f"I couldn't find your {target_lower} nearby.")
    else:
        parts = []
        for obj, (direction, dist) in stable.items():
            distance_info = f", {dist}" if dist else ""
            parts.append(f"{obj} on the {direction}{distance_info}")
        sentence = "; ".join(parts)
        talk_fn(f"I can see: {sentence}.")
        logger.info("Detection complete: %s", sentence)