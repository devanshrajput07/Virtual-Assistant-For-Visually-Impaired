import cv2
import pytesseract
import time

pages_read = []

def read_document_mode(talk, listen_for_command):
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    if not cap.isOpened():
        talk("Camera not detected.")
        return

    talk("Document reader mode activated. Hold your document steady in front of the camera. "
         "Say 'next page' to read another page, or 'stop reading' to exit.")

    while True:
        talk("Capturing page. Please hold still.")
        time.sleep(1.5)

        frames = []
        for _ in range(5):
            ret, frame = cap.read()
            if ret:
                frames.append(frame)
            time.sleep(0.1)

        if not frames:
            talk("I couldn't capture the page. Please try again.")
            continue

        frame = frames[-1]
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)

        try:
            text = pytesseract.image_to_string(gray, lang='eng').strip()
        except Exception:
            text = ""

        if not text or len(text) < 10:
            talk("I couldn't read any text on this page. Please adjust the document and try again.")
        else:
            pages_read.append(text)
            paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
            if not paragraphs:
                paragraphs = [text]

            talk(f"I found {len(paragraphs)} paragraph{'s' if len(paragraphs) > 1 else ''}.")
            for i, para in enumerate(paragraphs):
                talk(para)
                if i < len(paragraphs) - 1:
                    time.sleep(0.5)

        talk("Say 'next page' to continue, 'repeat' to re-read, or 'stop reading' to exit.")

        cmd = listen_for_command()
        if not cmd:
            continue

        cmd = cmd.lower()
        if "stop" in cmd or "exit" in cmd or "quit" in cmd:
            talk("Exiting document reader mode.")
            break
        elif "repeat" in cmd:
            if pages_read:
                talk("Re-reading the last page.")
                talk(pages_read[-1])
            else:
                talk("There's nothing to repeat yet.")

    cap.release()
