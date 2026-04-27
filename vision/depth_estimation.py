"""
vision/depth_estimation.py
Robust MiDaS depth estimation with:
  - Lazy loading (no import-time crash)
  - command_estimate_depth() function (was missing — caused NameError in dispatcher)
  - Human-readable distance buckets
  - Graceful fallback if MiDaS is unavailable
"""

import logging
import numpy as np
import cv2

logger = logging.getLogger("aura.vision.depth")

_midas = None
_transform_fn = None
_loaded = False          # True once we've attempted loading
_available = False       # True if load succeeded


def _load_midas():
    """Attempt to load MiDaS from torch.hub (lazy, once)."""
    global _midas, _transform_fn, _loaded, _available

    if _loaded:
        return _available
    _loaded = True

    try:
        import torch
        candidates = ["DPT_Small", "MiDaS_small", "DPT_Hybrid"]
        hub_transforms = None

        for name in candidates:
            try:
                _midas = torch.hub.load("intel-isl/MiDaS", name, trust_repo=True)
                hub_transforms = torch.hub.load("intel-isl/MiDaS", "transforms", trust_repo=True)
                logger.info("MiDaS loaded with callable '%s'.", name)
                break
            except Exception as exc:
                logger.debug("MiDaS callable '%s' unavailable: %s", name, exc)

        if _midas is None:
            raise RuntimeError("All MiDaS model variants failed to load.")

        # Choose transform
        _transform_fn = (
            getattr(hub_transforms, "dpt_transform", None)
            or getattr(hub_transforms, "small_transform", None)
            or getattr(hub_transforms, "midas_transform", None)
            or hub_transforms
        )
        _midas.eval()
        _available = True
        logger.info("MiDaS depth model is ready.")
    except Exception as exc:
        logger.warning("MiDaS unavailable — depth features disabled: %s", exc)
        _available = False

    return _available



def estimate_depth(frame: np.ndarray) -> np.ndarray | None:
    """
    Returns normalised depth map (0-1, higher=closer) or None if MiDaS unavailable.
    Input: BGR OpenCV frame (H, W, 3).
    """
    if not _load_midas():
        return None

    import torch

    img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    input_tensor = _transform_fn(img)

    if isinstance(input_tensor, (list, tuple)):
        input_tensor = input_tensor[0]
    if input_tensor.dim() == 3:
        input_tensor = input_tensor.unsqueeze(0)

    with torch.no_grad():
        prediction = _midas(input_tensor)
        if isinstance(prediction, (list, tuple)):
            prediction = prediction[0]
        depth_map = prediction.squeeze().cpu().numpy()

    # Normalise to 0-1
    mn, mx = depth_map.min(), depth_map.max()
    if mx - mn > 1e-6:
        depth_map = (depth_map - mn) / (mx - mn)
    else:
        depth_map = np.zeros_like(depth_map, dtype=np.float32)

    # Resize to match original frame
    depth_map = cv2.resize(depth_map, (frame.shape[1], frame.shape[0]), interpolation=cv2.INTER_CUBIC)
    return depth_map.astype(np.float32)


def estimate_object_distance(frame: np.ndarray, boxes: list) -> list[tuple[str, float]]:
    """
    Args:
        frame:  BGR OpenCV frame.
        boxes:  List of (x1, y1, x2, y2, label).
    Returns:
        List of (label, avg_depth_value) — higher value = object is closer.
    """
    depth_map = estimate_depth(frame)
    if depth_map is None:
        return []

    distances = []
    for (x1, y1, x2, y2, label) in boxes:
        x1i = max(0, int(round(x1)))
        y1i = max(0, int(round(y1)))
        x2i = min(frame.shape[1] - 1, int(round(x2)))
        y2i = min(frame.shape[0] - 1, int(round(y2)))
        if x2i <= x1i or y2i <= y1i:
            continue
        roi = depth_map[y1i:y2i, x1i:x2i]
        if roi.size == 0:
            continue
        distances.append((label, float(np.mean(roi))))
    return distances


def _depth_bucket(avg_depth: float) -> str:
    """Convert normalised depth value to human-readable distance label."""
    if avg_depth > 0.80:
        return "extremely close — under one metre"
    elif avg_depth > 0.60:
        return "very close — about one to two metres"
    elif avg_depth > 0.40:
        return "nearby — roughly two to four metres"
    elif avg_depth > 0.20:
        return "at a moderate distance — four to eight metres"
    else:
        return "far away — more than eight metres"


# Bug fix: this function was called by dispatcher but did NOT EXIST before.

def command_estimate_depth(talk_fn) -> None:
    """
    Called when user says 'how far' or 'distance'.
    Opens camera, takes one frame, estimates depth of central object.
    """
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    if not cap.isOpened():
        talk_fn("Camera not detected. Cannot estimate distance.")
        return

    talk_fn("Checking the distance, one moment.")

    try:
        # Read a few frames to let camera auto-expose
        for _ in range(5):
            cap.read()

        ret, frame = cap.read()
        if not ret:
            talk_fn("Could not capture a frame from the camera.")
            return

        if not _load_midas():
            # Fallback: use bounding-box-size heuristic via YOLO
            _depth_heuristic_fallback(frame, talk_fn)
            return

        depth_map = estimate_depth(frame)
        if depth_map is None:
            talk_fn("Depth estimation is not available right now.")
            return

        # Sample the central 20% of the frame
        h, w = depth_map.shape
        cy1, cy2 = int(h * 0.4), int(h * 0.6)
        cx1, cx2 = int(w * 0.4), int(w * 0.6)
        center_region = depth_map[cy1:cy2, cx1:cx2]
        avg = float(np.mean(center_region))

        label = _depth_bucket(avg)
        talk_fn(f"The object directly in front of you appears to be {label}.")
        logger.info("Depth estimate: %.2f → %s", avg, label)

    finally:
        cap.release()


def _depth_heuristic_fallback(frame: np.ndarray, talk_fn) -> None:
    """
    Simple size-based depth heuristic when MiDaS is unavailable.
    Runs YOLO and guesses distance from bounding-box area.
    """
    try:
        from vision.object_detection import get_yolo_model
        model = get_yolo_model()
        results = list(model(frame, stream=True, verbose=False))
        frame_h, frame_w = frame.shape[:2]
        frame_area = frame_h * frame_w

        found = []
        for r in results:
            for box in r.boxes:
                if float(box.conf[0]) < 0.5:
                    continue
                x1, y1, x2, y2 = box.xyxy[0]
                area_ratio = ((x2 - x1) * (y2 - y1)) / frame_area
                cls = int(box.cls[0])
                name = model.names[cls]
                found.append((name, float(area_ratio)))

        if not found:
            talk_fn("No objects detected close to you.")
            return

        # Pick the largest object (most likely closest)
        found.sort(key=lambda x: x[1], reverse=True)
        name, ratio = found[0]

        if ratio > 0.30:
            guess = "very close — within one to two metres"
        elif ratio > 0.10:
            guess = "nearby — about two to four metres"
        elif ratio > 0.04:
            guess = "at a moderate distance"
        else:
            guess = "far away"

        talk_fn(f"I can see a {name} which appears to be {guess}.")

    except Exception as exc:
        logger.warning("Depth heuristic fallback failed: %s", exc)
        talk_fn("Sorry, I couldn't estimate the distance right now.")