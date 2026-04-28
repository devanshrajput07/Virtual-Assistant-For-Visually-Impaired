import logging
import traceback
from typing import Callable
from core.voice import talk, accept_command_text
from core.ai_chat import chat_with_groq
from config.settings import SMALL_TALK, WEBSITE_MAP, APP_MAP

logger = logging.getLogger("aura.dispatcher")

def _vision(module: str, func: str) -> Callable | None:
    try:
        mod = __import__(f"vision.{module}", fromlist=[func])
        return getattr(mod, func)
    except (ImportError, AttributeError) as exc:
        logger.debug("Vision module %s.%s unavailable: %s", module, func, exc)
        return None

HELP_CATEGORIES = {
    "vision": "Vision: say detect objects, describe surroundings, read text, navigate, how do I look, who is in front, read document, or how far.",
    "media": "Media: say play a song, play something relaxing, pause, next song, or volume up and down.",
    "productivity": "Productivity: say set timer, set reminder, set alarm, add to my list, read my list, or find file.",
    "information": "Information: say weather, news, time, date, define a word, translate, or daily briefing.",
    "communication": "Communication: say WhatsApp, call someone, add contact, read clipboard, or emergency SOS.",
    "system": "System: say screenshot, battery, system info, brightness up or down, or open an app.",
    "fun": "Fun: say joke, quote, flip a coin, roll a dice, spell a word, or convert currency.",
}

def command_help(command: str = "") -> None:
    command = command.lower()
    for cat, text in HELP_CATEGORIES.items():
        if cat in command and "help" in command:
            talk(text)
            return
    talk("I can help with vision, media, productivity, information, communication, system, and fun commands. Say 'help' followed by the category name, like 'help vision'.")

def process_command(command: str, gps_lat: float = None, gps_lon: float = None) -> None:
    command = command.lower().strip()
    logger.info("Processing command: '%s'", command)

    if not command:
        return

    for trigger, response in SMALL_TALK.items():
        if trigger in command:
            talk(response)
            return

    try:
        from commands.smart import is_context_command, command_smart_context
        if is_context_command(command):
            command_smart_context(command)
            return
    except Exception as exc:
        logger.debug("Smart context check failed: %s", exc)

    try:
        if "help" in command or "what can you do" in command or "list commands" in command:
            command_help(command)

        elif "emergency" in command or "sos" in command or "help me" in command:
            from commands.communication import command_emergency_sos
            command_emergency_sos(gps_lat=gps_lat, gps_lon=gps_lon)

        elif any(k in command for k in ["how do i look", "how am i looking", "my emotion", "my mood", "my face", "emotion"]):
            fn = _vision("emotion", "detect_emotion")
            if fn:
                fn(talk)
            else:
                talk("Emotion detection is not available right now.")

        elif any(k in command for k in ["who is in front", "who is this", "who is that", "recognize face", "recognise face"]):
            fn = _vision("face_recognition_module", "recognize_face")
            if fn:
                fn(talk)
            else:
                talk("Face recognition is not available right now.")

        elif ("remember" in command and "face" in command) or ("save" in command and "face" in command):
            name = command
            for kw in ["remember this face as", "remember face as", "save this face as",
                        "save face as", "remember", "face", "this", "as", "save"]:
                name = name.replace(kw, "")
            name = name.strip().title()
            if not name:
                talk("Please specify the name. For example, say: remember this face as John.")
                return
            fn = _vision("face_recognition_module", "register_face")
            if fn:
                fn(talk, name)

        elif any(k in command for k in ["read document", "read book", "read page", "document mode", "reader mode"]):
            fn = _vision("document_reader", "read_document_mode")
            if fn:
                fn(talk)

        elif any(k in command for k in ["describe", "what do you see", "surroundings", "what's around", "look around"]):
            fn = _vision("scene_description", "describe_scene")
            if fn:
                fn(talk)
            else:
                talk("Scene description is not available right now.")

        elif "read" in command and any(k in command for k in ["text", "written", "sign", "label"]):
            fn = _vision("text_reader", "read_text_from_camera")
            if fn:
                fn(talk)

        elif any(k in command for k in ["navigate", "guide me", "guide", "walk me"]):
            fn = _vision("navigation", "continuous_navigation")
            if fn:
                fn(talk)
            else:
                talk("Navigation module is not available right now.")

        elif any(k in command for k in ["where is my", "find my", "locate my"]):
            target = command
            for kw in ["where is my", "find my", "locate my"]:
                target = target.replace(kw, "")
            target = target.strip()
            fn = _vision("object_detection", "detect_objects_from_camera")
            if fn:
                fn(talk, target, max_frames=5, show_view=False)

        elif any(k in command for k in ["detect", "what is in front", "identify", "what can you see", "what objects"]) \
                or ("scan" in command and "qr" not in command):
            fn = _vision("object_detection", "detect_objects_from_camera")
            if fn:
                fn(talk, max_frames=5, show_view=False)

        elif any(k in command for k in ["how far", "distance", "how close"]):
            fn = _vision("depth_estimation", "command_estimate_depth")
            if fn:
                fn(talk)

        elif "qr" in command or "qr code" in command:
            from commands.system import command_scan_qr
            command_scan_qr()

        elif "briefing" in command or ("good morning" in command and "brief" in command):
            from commands.information import command_daily_briefing
            command_daily_briefing(gps_lat=gps_lat, gps_lon=gps_lon)

        elif any(k in command for k in ["feeling", "mood", "something relaxing", "something energetic",
                                         "something happy", "something sad", "chill music", "focus music",
                                         "study music", "sleep music", "party music", "workout music"]):
            from commands.media import command_mood_music
            command_mood_music(command)

        elif "play" in command and "display" not in command:
            from commands.media import command_play_music
            command_play_music(command)

        elif any(k in command for k in ["pause", "resume", "next song", "previous song", "skip song"]):
            from commands.media import command_media_control
            command_media_control(command)

        elif "date" in command or ("day" in command and "today" in command):
            from commands.information import command_get_date
            command_get_date()

        elif "time" in command:
            from commands.information import command_get_current_time
            command_get_current_time()

        elif "alarm" in command or "wake me" in command:
            from commands.productivity import command_set_alarm
            command_set_alarm(command)

        elif any(k in command for k in ["weather", "temperature", "forecast"]):
            from commands.information import command_get_weather
            command_get_weather(command, gps_lat=gps_lat, gps_lon=gps_lon)

        elif any(k in command for k in ["calculate", "what is", "how much is", "compute"]) and \
             any(k in command for k in ["plus", "minus", "times", "divided", "add", "subtract",
                                         "multiply", "percent", "power", "root", "+", "-", "*", "/"]):
            from commands.productivity import command_calculate
            command_calculate(command)

        elif "convert" in command and any(k in command for k in ["dollar", "rupee", "euro", "pound", "yen", "currency"]):
            from commands.productivity import command_convert_currency
            command_convert_currency(command)

        elif any(k in command for k in ["timer", "countdown"]):
            from commands.productivity import command_set_timer
            command_set_timer(command)

        elif any(k in command for k in ["remind", "reminder"]):
            from commands.productivity import command_set_reminder
            command_set_reminder(command)

        elif any(k in command for k in ["medication", "medicine", "pill"]):
            from core.alerts import add_medication_reminder
            talk("What medication should I remind you about?")
            med = accept_command_text()
            if not med:
                return
            talk("At what time? Say something like 8 AM or 9 PM.")
            time_str = accept_command_text()
            if not time_str:
                return
            add_medication_reminder(talk, med, [time_str])

        elif any(k in command for k in ["to do", "todo", "my list", "task list"]) or \
             ("list" in command and any(k in command for k in ["add", "read", "show", "clear", "done"])):
            from commands.productivity import command_todo
            command_todo(command)

        elif any(k in command for k in ["who is", "what is", "tell me about", "wikipedia", "search for", "search on wikipedia"]):
            from commands.information import command_search_wikipedia
            command_search_wikipedia(command)

        elif any(k in command for k in ["joke", "make me laugh", "funny"]):
            from commands.fun import command_tell_joke
            command_tell_joke()

        elif any(k in command for k in ["news", "headlines"]):
            from commands.information import command_tell_news
            command_tell_news()

        elif any(k in command for k in ["send message", "whatsapp", "send a message"]):
            from commands.communication import command_send_whatsapp_message
            command_send_whatsapp_message(command)

        elif any(k in command for k in ["call", "dial"]):
            from commands.communication import command_speed_dial
            command_speed_dial(command)

        elif any(k in command for k in ["add contact", "save contact", "new contact"]):
            from commands.communication import save_contact
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
                number = "+" + number
            save_contact(name, number)

        elif any(k in command for k in ["open", "launch", "start"]) or \
             command in APP_MAP or command in WEBSITE_MAP:
            site = next((s for s in WEBSITE_MAP if s in command), None)
            app = next((a for a in APP_MAP if a in command), None)
            if site:
                from commands.system import command_open_website
                command_open_website(f"open {site}")
            elif app:
                from commands.system import command_open_app
                command_open_app(f"open {app}")
            else:
                target = command.replace("open", "").replace("launch", "").replace("start", "").strip()
                if target and ("." in target or target in ["website", "site"]):
                    from commands.system import command_open_website
                    command_open_website(command)
                else:
                    from commands.system import command_open_app
                    command_open_app(command)

        elif any(k in command for k in ["search", "google", "look up"]):
            from commands.system import command_google_search
            command_google_search(command)

        elif any(k in command for k in ["screenshot", "screen capture", "take a picture of screen"]):
            from commands.system import command_take_screenshot
            command_take_screenshot()

        elif any(k in command for k in ["clipboard", "read what i copied", "what did i copy"]):
            from commands.communication import command_read_clipboard
            command_read_clipboard()

        elif any(k in command for k in ["volume", "mute", "unmute"]):
            from commands.system import command_volume_control
            command_volume_control(command)

        elif any(k in command for k in ["brightness", "screen light"]):
            from commands.system import command_brightness_control
            command_brightness_control(command)

        elif any(k in command for k in ["battery", "charge", "power level"]):
            from commands.system import command_battery_status
            command_battery_status()

        elif any(k in command for k in ["system info", "cpu", "memory usage", "ram usage"]):
            from commands.system import command_system_info
            command_system_info()

        elif any(k in command for k in ["find file", "locate file", "search file"]):
            from commands.system import command_find_file
            command_find_file(command)

        elif "translate" in command:
            from commands.information import command_translate
            command_translate(command)

        elif any(k in command for k in ["define", "meaning of", "definition"]):
            from commands.information import command_define_word
            command_define_word(command)

        elif any(k in command for k in ["quote", "motivat", "inspire", "inspiration"]):
            from commands.fun import command_motivational_quote
            command_motivational_quote()

        elif "flip" in command and "coin" in command:
            from commands.fun import command_flip_coin
            command_flip_coin()

        elif "roll" in command and any(k in command for k in ["dice", "die"]):
            from commands.fun import command_roll_dice
            command_roll_dice()

        elif "spell" in command:
            from commands.fun import command_spell_word
            command_spell_word(command)

        elif "save" in command and any(k in command for k in ["chat", "conversation", "history"]):
            from commands.communication import command_export_conversation
            command_export_conversation()

        else:
            reply = chat_with_groq(command)
            talk(reply)

    except Exception as exc:
        logger.error("Command processing error for '%s': %s\n%s", command, exc, traceback.format_exc())
        talk("Sorry, something went wrong while processing that command. Please try again.")
