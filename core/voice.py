"""
core/voice.py
Thread-safe voice I/O for AURA.

Fixes applied:
  - Singleton pyttsx3 engine (was re-initialized on every TTS call → memory leak)
  - Engine auto-recovers on crash
  - Web message queue preserved
  - Custom talk-handler for web UI integration
  - Proper logging throughout
"""

import speech_recognition as sr
import pyttsx3
import threading
import datetime
import time
import logging
from collections import deque

logger = logging.getLogger("aura.voice")

listener = sr.Recognizer()
listener.energy_threshold = 300
listener.dynamic_energy_threshold = True
listener.pause_threshold = 0.8

_tts_lock = threading.Lock()
_tts_engine: pyttsx3.Engine | None = None


def _get_tts_engine() -> pyttsx3.Engine:
    """Return the singleton TTS engine, (re)initialising if needed."""
    global _tts_engine
    if _tts_engine is not None:
        return _tts_engine
    try:
        engine = pyttsx3.init(driverName="sapi5")
        engine.setProperty("rate", 155)
        engine.setProperty("volume", 1.0)
        voices = engine.getProperty("voices")
        # Prefer a female voice for AURA if available
        female = next((v for v in voices if "zira" in v.name.lower() or "female" in v.name.lower()), None)
        if female:
            engine.setProperty("voice", female.id)
        elif voices:
            engine.setProperty("voice", voices[0].id)
        _tts_engine = engine
        logger.debug("TTS engine initialised.")
    except Exception as exc:
        logger.error("TTS init failed: %s", exc)
        raise
    return _tts_engine


_talk_handler = None
_web_message_queue: deque = deque(maxlen=50)
_queue_lock = threading.Lock()


def set_talk_handler(handler):
    global _talk_handler
    _talk_handler = handler


def get_web_updates():
    """Retrieve and clear all pending messages for the web UI."""
    with _queue_lock:
        updates = list(_web_message_queue)
        _web_message_queue.clear()
        return updates



def talk(text: str) -> None:
    """Speak text aloud or route to web UI handler."""
    if not text:
        return

    logger.info("AURA says: %s", text)

    # Always push to web queue (UI polls this)
    with _queue_lock:
        _web_message_queue.append(text)

    # If a web handler is active, delegate and return
    if _talk_handler:
        _talk_handler(text)
        return

    # Desktop TTS (protected by lock so only one utterance at a time)
    with _tts_lock:
        global _tts_engine
        try:
            engine = _get_tts_engine()
            engine.say(text)
            engine.runAndWait()
        except Exception as exc:
            logger.warning("TTS error, reinitialising engine: %s", exc)
            _tts_engine = None  # force reinit on next call
            try:
                engine = _get_tts_engine()
                engine.say(text)
                engine.runAndWait()
            except Exception as exc2:
                logger.error("TTS failed after reinit: %s", exc2)



def accept_command() -> str | None:
    """Listen via microphone and transcribe using Google Speech Recognition."""
    try:
        with sr.Microphone() as source:
            logger.debug("Adjusting for ambient noise…")
            listener.adjust_for_ambient_noise(source, duration=0.3)
            logger.info("🎙️ Listening…")
            voice = listener.listen(source, timeout=8, phrase_time_limit=12)
        command = listener.recognize_google(voice)
        if command:
            command = command.lower().strip()
            logger.info("🧏 Heard: %s", command)
            return command
    except sr.WaitTimeoutError:
        logger.debug("Mic timeout — no speech detected.")
    except sr.UnknownValueError:
        logger.debug("Could not understand audio.")
    except sr.RequestError as exc:
        logger.warning("Google SR unavailable: %s", exc)
    except Exception as exc:
        logger.error("Unexpected error in accept_command: %s", exc)
    return None


def accept_command_text() -> str | None:
    """Wrapper with optional web-context delay to avoid TTS echo."""
    if _talk_handler is not None:
        time.sleep(2.5)  # let browser TTS finish before mic opens
    return accept_command()



def greeting_message() -> None:
    """Speak a time-appropriate greeting."""
    hour = datetime.datetime.now().hour
    if hour < 12:
        period = "Good Morning!"
    elif hour < 18:
        period = "Good Afternoon!"
    else:
        period = "Good Evening!"
    talk(period)
    talk("I am AURA, your intelligent voice assistant. How can I help you today?")
