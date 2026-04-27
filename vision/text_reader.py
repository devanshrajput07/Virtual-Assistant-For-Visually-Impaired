import cv2
import pytesseract
from PIL import Image
import numpy as np
import tempfile
import os
import time

# Point pytesseract to the Tesseract binary on Windows
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'


def preprocess_image(frame):
    """Enhance text clarity for better OCR recognition."""
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Increase contrast
    gray = cv2.convertScaleAbs(gray, alpha=1.5, beta=20)

    # Apply adaptive thresholding to handle variable lighting
    thresh = cv2.adaptiveThreshold(
        gray, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        35, 11
    )

    # Optional: remove small noise
    kernel = np.ones((1, 1), np.uint8)
    processed = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)

    return processed


def read_text_from_camera(talk):
    """Capture one frame, process it, and extract readable text."""
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    if not cap.isOpened():
        talk("Camera not detected.")
        return

    talk("Please hold the text in front of the camera. Scanning in three seconds.")
    time.sleep(3)

    ret, frame = cap.read()
    cap.release()

    if not ret:
        talk("I couldn't capture the image properly.")
        return

    # Preprocess image for better OCR
    processed = preprocess_image(frame)

    # Save temporary enhanced image
    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
        cv2.imwrite(tmp.name, processed)
        tmp_path = tmp.name

    try:
        # OCR configuration: only extract letters/numbers
        custom_config = r'--oem 3 --psm 6'
        text = pytesseract.image_to_string(Image.open(tmp_path), config=custom_config)
        os.unlink(tmp_path)
    except Exception as e:
        talk(f"Error while reading text: {e}")
        return

    # Clean up OCR output
    text = text.strip().replace("\n\n", "\n")

    if text:
        talk("Here’s what I found:")
        talk(text)
    else:
        talk("Sorry, I couldn’t read any clear text from the image.")
