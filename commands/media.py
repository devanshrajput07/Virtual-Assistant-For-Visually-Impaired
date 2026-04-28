import pywhatkit
import pyautogui
from core.voice import talk, accept_command_text

def command_play_music(command):
    song = command.replace("play", "").strip()
    if not song:
        talk("Please specify what you would like me to play. For example, say: play jazz music.")
        return
    talk(f"Playing {song}")
    pywhatkit.playonyt(song)

def command_media_control(command):
    try:
        if "pause" in command or "stop" in command or "resume" in command:
            pyautogui.press("playpause")
            talk("Toggled play/pause.")
        elif "next" in command or "skip" in command:
            pyautogui.press("nexttrack")
            talk("Playing next track.")
        elif "previous" in command or "back" in command or "last" in command:
            pyautogui.press("prevtrack")
            talk("Playing previous track.")
        else:
            talk("Say pause, next song, or previous song.")
    except Exception as e:
        talk("Sorry, I couldn't control media playback.")

MOOD_MAP = {
    "happy": "happy upbeat music playlist",
    "sad": "comforting soothing music playlist",
    "relaxing": "relaxing calm music playlist",
    "relax": "relaxing calm lo-fi music playlist",
    "chill": "chill vibes lo-fi playlist",
    "energetic": "high energy workout music playlist",
    "energy": "pump up energetic music playlist",
    "focus": "deep focus study music playlist",
    "study": "study concentration music playlist",
    "sleep": "sleep relaxation ambient music",
    "party": "party dance music hits playlist",
    "romantic": "romantic love songs playlist",
    "motivational": "motivational inspirational music playlist",
    "angry": "intense heavy metal rock playlist",
    "workout": "gym workout power music playlist",
    "morning": "good morning fresh start playlist",
    "rain": "rainy day cozy music playlist",
}

def command_mood_music(command):
    mood = None
    for keyword, query in MOOD_MAP.items():
        if keyword in command:
            mood = keyword
            break

    if not mood:
        talk("What mood are you in? Try saying something like 'play something relaxing' or 'I'm feeling energetic'.")
        return

    search_query = MOOD_MAP[mood]
    talk(f"Playing {mood} music for you.")
    pywhatkit.playonyt(search_query)
