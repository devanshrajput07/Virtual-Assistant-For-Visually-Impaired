import speech_recognition as sr
import pyttsx3
import threading
import os
import datetime
from config.settings import GROQ_KEY
from groq import Groq

_tts_lock = threading.Lock()
listener = sr.Recognizer()

client = Groq(api_key=GROQ_KEY)

def talk(text):
    """Speak text aloud using a thread-safe singleton engine"""
    print(f"[VAVI] {text}")
    with _tts_lock:
        try:
            engine = pyttsx3.init(driverName='sapi5')
            engine.setProperty('rate', 170)
            voices = engine.getProperty('voices')
            if voices:
                engine.setProperty('voice', voices[0].id)
            engine.say(text)
            engine.runAndWait()
            del engine
        except Exception as e:
            print(f"TTS Error: {e}")

def accept_command_text():
    """Wrapper that returns only the text from accept_command"""
    cmd, _ = accept_command()
    return cmd

def accept_command():
    """Listen via microphone, save to temp file, and transcribe via Groq Whisper"""
    try:
        with sr.Microphone() as source:
            print("Listening (Auto-detecting language)...")
            listener.adjust_for_ambient_noise(source, duration=0.5)
            voice_audio = listener.listen(source, timeout=8, phrase_time_limit=12)
            
            temp_filename = "temp_voice_cmd.wav"
            with open(temp_filename, "wb") as f:
                f.write(voice_audio.get_wav_data())
            
            with open(temp_filename, "rb") as file:
                transcription = client.audio.transcriptions.create(
                    file=(temp_filename, file.read()),
                    model="whisper-large-v3",
                    response_format="verbose_json",
                )
            
            if os.path.exists(temp_filename):
                try: os.remove(temp_filename)
                except: pass
                
            command = transcription.text.strip().lower()
            detected_lang = transcription.language
            
            if command:
                print(f"You said ({detected_lang}): {command}")
                return command, detected_lang
    except Exception as e:
        print(f"Recognition Error: {e}")
    return None, None

def greeting_message():
    """Speak a time-appropriate greeting"""
    hour = datetime.datetime.now().hour
    if hour < 12:
        talk("Good Morning!")
    elif hour < 18:
        talk("Good Afternoon!")
    else:
        talk("Good Evening!")
    talk("I am VAVI, your voice assistant. How can I help you today?")
