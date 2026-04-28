import cv2
import pytesseract
from PIL import Image
import numpy as np
import tempfile
import os
import time

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def preprocess_image(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray = cv2.convertScaleAbs(gray, alpha=1.5, beta=20)
    thresh = cv2.adaptiveThreshold(
        gray, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        35, 11
    )
    kernel = np.ones((1, 1), np.uint8)
    processed = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
    return processed

def read_text_from_camera(talk):
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    if not cap.isOpened():
        talk("Camera not detected.")
        return

    talk("Please hold the text in front of the camera. Scanning in three seconds.")
    time.sleep(3)

    for _ in range(20):
        cap.read()
        
    ret, frame = cap.read()
    cap.release()

    if not ret:
        talk("I couldn't capture the image properly.")
        return

    processed = preprocess_image(frame)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
        cv2.imwrite(tmp.name, processed)
        tmp_path = tmp.name

    try:
        custom_config = r'--oem 3 --psm 6'
        text = pytesseract.image_to_string(Image.open(tmp_path), config=custom_config)
        os.unlink(tmp_path)
    except Exception as e:
        talk(f"Error while reading text: {e}")
        return

    text = text.strip().replace("\n\n", "\n")

    if text:
        talk("Here’s what I found:")
        talk(text)
    else:
        talk("Sorry, I couldn’t read any clear text from the image.")
