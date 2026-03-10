"""
depth_estimation.py
Robust loader for MiDaS depth estimation:
 - Tries multiple callable names from torch.hub
 - Chooses an appropriate transform automatically
 - Falls back to local model file if provided (models/*.pt)
"""

import torch
import cv2
import numpy as np
import os
import glob
import traceback

MODEL_DIR = "models"
MODEL_LOCAL_PATH = None
if os.path.isdir(MODEL_DIR):
    pts = glob.glob(os.path.join(MODEL_DIR, "*.pt"))
    if pts:
        MODEL_LOCAL_PATH = pts[0]

def try_load_midas_from_hub():
    """Attempt several common MiDaS callables and return (midas, transforms, used_name)."""
    candidates = [
        "DPT_Small",
        "DPT_Hybrid",
        "DPT_Large",
        "MiDaS_small",
        "MiDaS",
        "dpt_s_384",           # sometimes different names appear
        "DPT_Swin2Tiny_256",
    ]
    hub_transforms = None
    last_err = None

    for name in candidates:
        try:
            midas = torch.hub.load("intel-isl/MiDaS", name, trust_repo=True)
            hub_transforms = torch.hub.load("intel-isl/MiDaS", "transforms", trust_repo=True)
            print(f"[MiDaS] Loaded model with callable '{name}'")
            return midas, hub_transforms, name
        except Exception as e:
            last_err = e
            print(f"[MiDaS] Callable '{name}' not available: {e.__class__.__name__}: {e}")
            # continue trying
    # if we reach here, none succeeded
    raise RuntimeError("All torch.hub MiDaS callable attempts failed.") from last_err


def load_midas_model():
    """
    Load MiDaS model robustly:
     - First try local .pt if present (but midas repo code expects hub wrapper; local usage may still require repo code)
     - Then try multiple hub callables
    Returns: midas_model, transforms_module, used_name (str)
    """
    if MODEL_LOCAL_PATH and os.path.exists(MODEL_LOCAL_PATH):
        try:
            midas, hub_transforms, used_name = try_load_midas_from_hub()
            try:
                state = torch.load(MODEL_LOCAL_PATH, map_location="cpu")
                # Some checkpoints are pure weights, some are dicts with 'model' key
                if isinstance(state, dict) and 'model' in state:
                    state_dict = state['model']
                else:
                    state_dict = state
                try:
                    midas.load_state_dict(state_dict)
                    print("[MiDaS] Loaded local checkpoint into hub model.")
                except Exception:
                    # If direct load fails, try to load as whole object (works for some .pt)
                    midas = torch.load(MODEL_LOCAL_PATH, map_location="cpu")
                    print("[MiDaS] Replaced model by loaded checkpoint object.")
                return midas, hub_transforms, used_name
            except Exception as e:
                print(f"[MiDaS] Could not load checkpoint into hub model: {e.__class__.__name__}: {e}")
                # fall back to hub-only loading below
        except Exception as e:
            print(f"[MiDaS] Hub attempts failed while trying to use local checkpoint: {e.__class__.__name__}: {e}")
            # fall through to hub attempts

    # No usable local checkpoint path or local attempt failed → try hub callables
    midas, hub_transforms, used_name = try_load_midas_from_hub()
    return midas, hub_transforms, used_name


try:
    midas, hub_transforms, MIDAS_CALLABLE = load_midas_model()
except:
    raise

if hasattr(hub_transforms, "dpt_transform"):
    transform_fn = getattr(hub_transforms, "dpt_transform")
elif hasattr(hub_transforms, "swin2_transform"):
    transform_fn = getattr(hub_transforms, "swin2_transform")
elif hasattr(hub_transforms, "small_transform"):
    transform_fn = getattr(hub_transforms, "small_transform")
elif hasattr(hub_transforms, "midas_transform"):
    transform_fn = getattr(hub_transforms, "midas_transform")
else:
    transform_fn = getattr(hub_transforms, "dpt_transform", None) or getattr(hub_transforms, "transform", None) or hub_transforms

midas.eval()

def estimate_depth(frame):
    """
    Input: BGR OpenCV frame (H,W,3)
    Output: normalized depth map (H', W') as numpy float32 array (0..1)
    """
    img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    input_tensor = transform_fn(img)
    if isinstance(input_tensor, (list, tuple)):
        input_tensor = input_tensor[0]

    if input_tensor.dim() == 3:
        input_batch = input_tensor.unsqueeze(0)
    else:
        input_batch = input_tensor

    with torch.no_grad():
        prediction = midas(input_batch)
        if isinstance(prediction, (list, tuple)):
            prediction = prediction[0]
        depth_map = prediction.squeeze().cpu().numpy()

    # Normalize to 0..1
    minv = np.min(depth_map)
    maxv = np.max(depth_map)
    if maxv - minv > 1e-6:
        depth_map = (depth_map - minv) / (maxv - minv)
    else:
        depth_map = np.zeros_like(depth_map, dtype=np.float32)

    # Optionally resize depth_map to original frame size for easier ROI mapping
    depth_map_resized = cv2.resize(depth_map, (frame.shape[1], frame.shape[0]), interpolation=cv2.INTER_CUBIC)
    return depth_map_resized


def estimate_object_distance(frame, boxes):
    """
    boxes: list of (x1, y1, x2, y2, label) in pixel coords
    returns: list of (label, avg_depth_value) where avg_depth_value is normalized 0..1 (lower=far? model-specific)
    """
    depth_map = estimate_depth(frame)
    distances = []
    for (x1, y1, x2, y2, label) in boxes:
        # clamp coords
        x1i = max(0, int(round(x1)))
        y1i = max(0, int(round(y1)))
        x2i = min(frame.shape[1]-1, int(round(x2)))
        y2i = min(frame.shape[0]-1, int(round(y2)))
        if x2i <= x1i or y2i <= y1i:
            continue
        roi = depth_map[y1i:y2i, x1i:x2i]
        if roi.size == 0:
            continue
        avg_depth = float(np.mean(roi))
        distances.append((label, avg_depth))
    return distances