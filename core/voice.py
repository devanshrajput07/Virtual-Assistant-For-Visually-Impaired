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
    global _tts_engine
    if _tts_engine is not None:
        return _tts_engine
    try:
        engine = pyttsx3.init(driverName="sapi5")
        engine.setProperty("rate", 155)
        engine.setProperty("volume", 1.0)
        voices = engine.getProperty("voices")
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
    with _queue_lock:
        updates = list(_web_message_queue)
        _web_message_queue.clear()
        return updates

def talk(text: str) -> None:
    if not text:
        return

    logger.info("AURA says: %s", text)
    with _queue_lock:
        _web_message_queue.append(text)

    if _talk_handler:
        _talk_handler(text)
        return

    threading.Thread(target=_talk_threaded, args=(text,), daemon=True).start()

def _talk_threaded(text: str) -> None:
    if not _tts_lock.acquire(blocking=False):
        logger.debug("TTS engine busy, skipping audio output.")
        return
    
    try:
        global _tts_engine
        engine = _get_tts_engine()
        engine.say(text)
        engine.runAndWait()
    except Exception as exc:
        logger.warning("TTS hardware error: %s", exc)
        _tts_engine = None
    finally:
        _tts_lock.release()

threading.Thread(target=_get_tts_engine, daemon=True).start()

import concurrent.futures
_executor = concurrent.futures.ThreadPoolExecutor(max_workers=2)

def accept_command() -> str | None:
    try:
        future = _executor.submit(_accept_command_logic)
        return future.result(timeout=30)
    except concurrent.futures.TimeoutError:
        logger.warning("Master Voice Watchdog triggered — total process exceeded 30s.")
        talk("I'm sorry, that's taking too long. Please try again.")
        return None
    except Exception as exc:
        logger.error("Master Watchdog error: %s", exc)
        return None

def _accept_command_logic() -> str | None:
    try:
        with sr.Microphone() as source:
            listener.adjust_for_ambient_noise(source, duration=0.3)
            logger.info("🎙️ Listening…")
            start_listen = time.time()
            voice = listener.listen(source, timeout=8, phrase_time_limit=7)
            logger.debug("Listening complete in %.2fs", time.time() - start_listen)
            
        if not voice or len(voice.get_wav_data()) < 500:
            logger.warning("Microphone produced zero data.")
            return None

        start_recog = time.time()
        command = listener.recognize_google(voice)
        logger.info("Recognized in %.2fs: %s", time.time() - start_recog, command)
        
        if command:
            return command.lower().strip()
    except Exception as exc:
        logger.debug("Logic error: %s", exc)
    return None

def accept_command_text() -> str | None:
    """Listens for voice input and returns the recognized text string."""
    return accept_command()

def greeting_message() -> None:
    hour = datetime.datetime.now().hour
    if hour < 12:
        period = "Good Morning!"
    elif hour < 18:
        period = "Good Afternoon!"
    else:
        period = "Good Evening!"
    talk(period)
    talk("I am AURA, your intelligent voice assistant. How can I help you today?")
