import cv2
import json
import os
import numpy as np

FACES_DIR = "data/faces"
FACES_DB = "data/faces.json"

HAAR_CASCADE = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
face_cascade = cv2.CascadeClassifier(HAAR_CASCADE)

def ensure_dirs():
    os.makedirs(FACES_DIR, exist_ok=True)
    if not os.path.exists(FACES_DB):
        with open(FACES_DB, "w") as f:
            json.dump({}, f)

def load_face_db():
    ensure_dirs()
    try:
        with open(FACES_DB, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_face_db(db):
    ensure_dirs()
    with open(FACES_DB, "w") as f:
        json.dump(db, f, indent=2)

def compute_face_histogram(face_img):
    hsv = cv2.cvtColor(face_img, cv2.COLOR_BGR2HSV)
    hist = cv2.calcHist([hsv], [0, 1], None, [50, 60], [0, 180, 0, 256])
    cv2.normalize(hist, hist, 0, 1, cv2.NORM_MINMAX)
    return hist.flatten().tolist()

def register_face(talk, name):
    ensure_dirs()
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    if not cap.isOpened():
        talk("Camera not detected.")
        return

    talk(f"Please look at the camera. I'll remember your face as {name}.")
    
    for _ in range(20):
        cap.read()
        
    best_face = None
    best_area = 0

    for _ in range(30):
        ret, frame = cap.read()
        if not ret:
            continue
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.3, 5, minSize=(40, 40))

        for (x, y, w, h) in faces:
            area = w * h
            if area > best_area:
                best_area = area
                best_face = frame[y:y+h, x:x+w]

    cap.release()

    if best_face is None:
        talk("I couldn't detect a face. Please make sure your face is clearly visible and try again.")
        return

    histogram = compute_face_histogram(best_face)

    face_path = os.path.join(FACES_DIR, f"{name.lower().replace(' ', '_')}.jpg")
    success = cv2.imwrite(face_path, best_face)
    if not success:
        talk("Internal error: Could not save face image. Please check folder permissions.")
        return

    db = load_face_db()
    db[name.lower()] = {
        "name": name,
        "histogram": histogram,
        "image": face_path
    }
    save_face_db(db)
    talk(f"Got it! I've saved {name}'s face. I'll recognize them next time.")

def recognize_face(talk):
    db = load_face_db()
    if not db:
        talk("I don't have any faces saved yet. Say 'remember this face as' followed by a name to register someone.")
        return

    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    if not cap.isOpened():
        talk("Camera not detected.")
        return

    talk("Looking at who's in front of you.")
    
    for _ in range(20):
        cap.read()
        
    best_face = None
    best_area = 0

    for _ in range(20):
        ret, frame = cap.read()
        if not ret:
            continue
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.3, 5, minSize=(80, 80))

        for (x, y, w, h) in faces:
            area = w * h
            if area > best_area:
                best_area = area
                best_face = frame[y:y+h, x:x+w]

    cap.release()

    if best_face is None:
        talk("I can't see anyone in front of the camera right now.")
        return

    current_hist = compute_face_histogram(best_face)
    current_hist_np = np.array(current_hist, dtype=np.float32)

    best_match = None
    best_score = 0

    for key, data in db.items():
        saved_hist = np.array(data["histogram"], dtype=np.float32)
        score = cv2.compareHist(current_hist_np, saved_hist, cv2.HISTCMP_CORREL)
        if score > best_score:
            best_score = score
            best_match = data["name"]

    if best_match and best_score > 0.5:
        confidence = "pretty sure" if best_score > 0.7 else "think"
        talk(f"I {confidence} that's {best_match} in front of you!")
    else:
        talk("I can see someone, but I don't recognize them. Would you like me to remember this face?")
