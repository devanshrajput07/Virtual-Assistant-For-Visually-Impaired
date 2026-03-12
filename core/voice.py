import speech_recognition as sr
import pyttsx3
import threading
import datetime
import time
from collections import deque

_tts_lock = threading.Lock()
listener = sr.Recognizer()
_talk_handler = None
_web_message_queue = deque()
_queue_lock = threading.Lock()

def set_talk_handler(handler):
    global _talk_handler
    _talk_handler = handler

def get_web_updates():
    """Retrieve and clear all pending messages for the web UI"""
    global _web_message_queue
    with _queue_lock:
        updates = list(_web_message_queue)
        _web_message_queue.clear()
        return updates

def talk(text):
    """Speak text aloud using a thread-safe singleton engine, or route to web UI"""
    # Always push to the web queue if a web interaction is happening
    global _web_message_queue
    with _queue_lock:
        _web_message_queue.append(text)

    if _talk_handler:
        _talk_handler(text)
        return
        
    with _tts_lock:
        try:
            engine = pyttsx3.init(driverName='sapi5')
            engine.setProperty('rate', 140)
            voices = engine.getProperty('voices')
            if voices:
                engine.setProperty('voice', voices[0].id)
            engine.say(text)
            engine.runAndWait()
            del engine
        except Exception as e:
            print(f"TTS Error: {e}")

def accept_command_text():
    """Wrapper that returns only the text from accept_command.
    Adds a slight delay so the browser TTS has time to speak the follow-up question
    before the microphone starts listening, preventing TTS echo loops."""
    # Only delay if we're in a web context
    if _talk_handler is not None:
        time.sleep(2.5)
    return accept_command()

def accept_command():
    """Listen via microphone and transcribe via Google Speech Recognition"""
    try:
        with sr.Microphone() as source:
            print("🎙️ Listening...")
            listener.adjust_for_ambient_noise(source, duration=0.1)
            voice = listener.listen(source, timeout=8, phrase_time_limit=10)
            command = listener.recognize_google(voice)
            if command:
                command = command.lower()
                print(f"🧏 You said: {command}")
                return command
    except sr.UnknownValueError:
        pass
    except sr.RequestError:
        pass
    return None

def greeting_message():
    """Speak a time-appropriate greeting"""
    hour = datetime.datetime.now().hour
    if hour < 12:
        talk("Good Morning!")
    elif hour < 18:
        talk("Good Afternoon!")
    else:
        talk("Good Evening!")
    talk("I am AURA, your voice assistant. How can I help you today?")
