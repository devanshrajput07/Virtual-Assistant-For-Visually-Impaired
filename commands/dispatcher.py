import traceback
from core.voice import talk, accept_command_text
from core.ai_chat import chat_with_groq
from config.settings import SMALL_TALK, WEBSITE_MAP, APP_MAP
from .media import command_play_music, command_media_control, command_mood_music
from .productivity import (
    command_calculate, command_set_timer, command_set_reminder, 
    command_set_alarm, command_todo, command_convert_currency
)
from .information import (
    command_get_current_time, command_get_date, command_get_weather,
    command_search_wikipedia, command_tell_news, command_translate,
    command_define_word, command_daily_briefing
)
from .communication import (
    save_contact, command_send_whatsapp_message, command_speed_dial,
    command_read_clipboard, command_emergency_sos, command_export_conversation
)
from .system import (
    command_take_screenshot, command_volume_control, command_battery_status,
    command_system_info, command_brightness_control, command_open_app,
    command_open_website, command_google_search, command_find_file,
    command_scan_qr
)
from .fun import (
    command_tell_joke, command_motivational_quote, command_flip_coin,
    command_roll_dice, command_spell_word
)
from .smart import is_context_command, command_smart_context

def safe_import_vision(module_name, func_name):
    try:
        module = __import__(f"vision.{module_name}", fromlist=[func_name])
        return getattr(module, func_name)
    except ImportError:
        return None

HELP_CATEGORIES = {
    "vision": "Vision: Say 'detect objects', 'describe surroundings', 'read text', 'navigate', 'how do I look', 'who is in front', 'read document', or 'scan QR code'.",
    "media": "Media: Say 'play' a song, 'play something relaxing', 'pause', 'next song', or 'volume up/down'.",
    "productivity": "Productivity: Say 'set timer', 'set reminder', 'set alarm', 'add to my list', 'read my list', or 'find file'.",
    "information": "Information: Say 'weather', 'news', 'time', 'date', 'define' a word, 'translate', or 'daily briefing'.",
    "communication": "Communication: Say 'whatsapp', 'call' someone, 'add contact', 'read clipboard', or 'emergency SOS'.",
    "system": "System: Say 'screenshot', 'battery', 'system info', 'brightness up/down', or 'open' an app.",
    "fun": "Fun: Say 'joke', 'quote', 'flip a coin', 'roll a dice', 'spell' a word, or 'convert currency'.",
    "smart": "Smart: Say 'tell me more', 'repeat that', 'explain that', or 'set a reminder for that'.",
}

def command_help(command=""):
    command = command.lower()
    
    # Check for specific category first
    for cat, text in HELP_CATEGORIES.items():
        if cat in command and "help" in command:
            talk(text)
            return
            
    # Default help greeting
    talk("I can help you with vision, media, productivity, information, communication, system control, fun, and smart context. "
         "Which category would you like to hear about?")
    
    # Optional: enter a small loop to listen for category
    choice = accept_command_text()
    if choice:
        choice = choice.lower()
        for cat, text in HELP_CATEGORIES.items():
            if cat in choice:
                talk(text)
                return
        # If no category matched but they said something, try to guide them
        talk("I didn't catch that category. You can say something like 'help vision' at any time to hear related commands.")


def process_command(command):
    for trigger, response in SMALL_TALK.items():
        if trigger in command:
            talk(response)
            return

    if is_context_command(command):
        command_smart_context(command)

    elif ("what can you do" in command) or ("help" in command and "help me" not in command) or ("list categories" in command) or ("list commands" in command):
        command_help(command)

    elif "emergency" in command or "sos" in command:
        command_emergency_sos()

    elif "how do i look" in command or "how am i looking" in command or ("emotion" in command) or ("my mood" in command) or ("my face" in command):
        fn = safe_import_vision("emotion", "detect_emotion")
        if fn: fn(talk)

    elif "who is in front" in command or "recognize" in command or "who is this" in command or "who is that" in command:
        fn = safe_import_vision("face_recognition_module", "recognize_face")
        if fn: fn(talk)

    elif ("remember" in command and "face" in command) or ("save" in command and "face" in command):
        name = command
        for kw in ["hey aura", "aura", "remember this face as", "remember face as", "save this face as", "save face as", "remember", "face", "this", "as", "save"]:
            name = name.replace(kw, "")
        name = name.strip().title()
        if not name:
            talk("What name should I save this face as?")
            name = accept_command_text()
            if not name: return
            name = name.strip().title()
        fn = safe_import_vision("face_recognition_module", "register_face")
        if fn: fn(talk, name)

    elif "read document" in command or "read book" in command or "read page" in command or "document mode" in command or "reader mode" in command:
        import speech_recognition as sr
        from core.voice import listener
        def listen_for_cmd():
            try:
                with sr.Microphone() as source:
                    listener.adjust_for_ambient_noise(source)
                    voice = listener.listen(source, timeout=8, phrase_time_limit=5)
                    return listener.recognize_google(voice).lower()
            except:
                return None
        fn = safe_import_vision("document_reader", "read_document_mode")
        if fn: fn(talk, listen_for_cmd)

    elif "describe" in command or "what do you see" in command or "surroundings" in command or "what's around" in command:
        fn = safe_import_vision("scene_description", "describe_scene")
        if fn: fn(talk)

    elif "read" in command and ("text" in command or "written" in command or "sign" in command):
        fn = safe_import_vision("text_reader", "read_text_from_camera")
        if fn: fn(talk)

    elif "navigate" in command or "guide me" in command or "guide" in command:
        import speech_recognition as sr
        from core.voice import listener
        def listen_for_stop():
            try:
                with sr.Microphone() as source:
                    listener.adjust_for_ambient_noise(source)
                    voice = listener.listen(source, timeout=0.5, phrase_time_limit=2)
                    cmd = listener.recognize_google(voice).lower()
                    return "stop" in cmd or "exit" in cmd
            except:
                return False
        fn = safe_import_vision("navigation", "continuous_navigation")
        if fn: fn(talk, listen_for_stop)

    elif "where is my" in command or "find my" in command or "locate my" in command:
        target = command.replace("where is my", "").replace("find my", "").replace("locate my", "").strip()
        fn = safe_import_vision("object_detection", "detect_objects_from_camera")
        if fn: fn(talk, target)

    elif "detect" in command or "what is in front" in command or "identify" in command or ("scan" in command and "qr" not in command):
        fn = safe_import_vision("object_detection", "detect_objects_from_camera")
        if fn: fn(talk)

    elif "how far" in command or "distance" in command:
        fn = safe_import_vision("depth_estimation", "command_estimate_depth")
        if fn: fn()

    elif "qr" in command or "qr code" in command:
        command_scan_qr()
    elif "briefing" in command or ("good morning" in command and "brief" in command):
        command_daily_briefing()

    elif any(w in command for w in ["feeling", "mood", "something relaxing", "something energetic", "something happy",
                                     "something sad", "chill music", "focus music", "study music", "sleep music",
                                     "party music", "workout music"]):
        command_mood_music(command)

    elif "play" in command and "display" not in command:
        command_play_music(command)

    elif any(w in command for w in ["pause", "resume", "next song", "previous song", "skip song"]):
        command_media_control(command)
    elif ("date" in command) or ("day" in command and "today" in command):
        command_get_date()

    elif "time" in command:
        command_get_current_time()
    elif "alarm" in command or "wake" in command:
        command_set_alarm(command)
    elif "weather" in command or "temperature" in command or "forecast" in command:
        command_get_weather(command)
    elif any(w in command for w in ["calculate", "what is", "how much is", "compute"]) and \
         any(w in command for w in ["plus", "minus", "times", "divided", "add", "subtract",
                                     "multiply", "percent", "power", "root",
                                     "+", "-", "*", "/"]):
        command_calculate(command)
    elif "convert" in command and any(w in command for w in ["dollar", "rupee", "euro", "pound", "yen", "currency", "usd", "inr"]):
        command_convert_currency(command)
    elif "timer" in command or "countdown" in command:
        command_set_timer(command)

    elif "remind" in command or "reminder" in command:
        command_set_reminder(command)
    elif "medication" in command or "medicine" in command:
        from core.alerts import add_medication_reminder
        talk("What medication should I remind you about?")
        med = accept_command_text()
        if not med: return
        talk("At what time? Say something like 8 AM or 9 PM.")
        time_str = accept_command_text()
        if not time_str: return
        add_medication_reminder(talk, med, [time_str])

    elif "to do" in command or "todo" in command or ("list" in command and any(w in command for w in ["add", "read", "show", "clear", "done"])):
        command_todo(command)
    elif "who is" in command or "tell me about" in command:
        command_search_wikipedia(command)
    elif "joke" in command or "make me laugh" in command or "funny" in command:
        command_tell_joke()
    elif "news" in command or "headlines" in command:
        command_tell_news()
    elif "send message" in command or "whatsapp" in command or "send a message" in command:
        command_send_whatsapp_message(command)
    elif "call" in command or "dial" in command:
        command_speed_dial(command)
    elif "add contact" in command or "save contact" in command or "new contact" in command:
        talk("Please say the name of the contact.")
        name = accept_command_text()
        if not name:
            talk("Sorry, I didn't catch the name.")
            return
        talk("Now please say the phone number, including country code.")
        number = accept_command_text()
        if not number:
            talk("Sorry, I didn't catch the number.")
            return
        number = number.lower().replace("plus", "+").replace(" ", "").replace("-", "")
        if not number.startswith("+"):
            talk("Please include the country code, like plus nine one.")
            return
        save_contact(name, number)
    elif any(w in command for w in ["open", "launch", "start"]) or command in APP_MAP or command in WEBSITE_MAP:
        found_site = next((site for site in WEBSITE_MAP if site in command), None)
        found_app = next((app for app in APP_MAP if app in command), None)
        
        if found_site:
            command_open_website(f"open {found_site}")
        elif found_app:
            command_open_app(f"open {found_app}")
        else:
            target = command.replace("open", "").replace("launch", "").replace("start", "").strip()
            if target and ("." in target or target in ["website", "site"]):
                command_open_website(command)
            else:
                command_open_app(command)
    elif "search" in command or "google" in command or "look up" in command:
        command_google_search(command)
    elif "screenshot" in command or "screen capture" in command or "take a picture of screen" in command:
        command_take_screenshot()
    elif "clipboard" in command or "read what i copied" in command or "paste" in command:
        command_read_clipboard()
    elif "volume" in command or "mute" in command or "unmute" in command:
        command_volume_control(command)
    elif "brightness" in command or "screen light" in command:
        command_brightness_control(command)
    elif "battery" in command or "charge" in command or "power" in command:
        command_battery_status()
    elif "system info" in command or "cpu" in command or "memory usage" in command or "ram" in command:
        command_system_info()
    elif "find file" in command or "locate file" in command or "search file" in command:
        command_find_file(command)
    elif "translate" in command:
        command_translate(command)
    elif "define" in command or "meaning of" in command or "definition" in command:
        command_define_word(command)
    elif "quote" in command or "motivat" in command or "inspire" in command:
        command_motivational_quote()
    elif "flip" in command and "coin" in command:
        command_flip_coin()

    elif "roll" in command and ("dice" in command or "die" in command):
        command_roll_dice()
    elif "spell" in command:
        command_spell_word(command)
    elif "save" in command and ("chat" in command or "conversation" in command or "history" in command):
        command_export_conversation()
    else:
        reply = chat_with_groq(command)
        talk(reply)
