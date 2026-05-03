import urllib.parse
import webbrowser
import datetime
import logging
import requests
import re
import pyautogui
import time
import win32gui
import win32api
import win32con
import threading
from core.voice import talk, accept_command_text

logger = logging.getLogger("aura.commands.communication")

def _get_contacts() -> dict[str, str]:
    try:
        from core.db import get_all_contacts
        return get_all_contacts()
    except Exception as exc:
        logger.error("Could not load contacts from DB: %s", exc)
        return {}

def save_contact(name: str, number: str) -> None:
    try:
        from core.db import save_contact as db_save
        db_save(name, number)
        talk(f"Contact {name} has been saved with number {number}.")
        logger.info("Contact saved: %s → %s", name, number)
    except Exception as exc:
        logger.error("Failed to save contact: %s", exc)
        talk("Sorry, I couldn't save that contact.")

def command_send_whatsapp_message(command: str = "") -> None:
    try:
        contacts = _get_contacts()
        cmd = command.lower()
        fillers = r'\b(?:send|message|to|on|whatsapp|saying|through|using|a)\b'
        cmd = re.sub(fillers, ' ', cmd)
        cmd = " ".join(cmd.split())

        contact_name = None
        for name in contacts:
            if name in cmd:
                contact_name = name
                break

        if not contact_name:
            talk("Please specify who to send the message to. For example, say: send a message to John saying hello.")
            return

        message = cmd.replace(contact_name, "").strip()
        if not message:
            talk("Please specify the message. For example, say: send a message to John saying hello.")
            return

        number = contacts[contact_name]
        encoded = urllib.parse.quote(message)
        url = f"https://wa.me/{number.replace('+', '')}?text={encoded}"
        talk(f"Opening WhatsApp to send your message to {contact_name}.")
        webbrowser.open(url)
        logger.info("WhatsApp to %s: %s", contact_name, message)

    except Exception as exc:
        logger.error("WhatsApp command failed: %s", exc)
        talk("Sorry, I couldn't send the message.")

def command_whatsapp_call(command: str = "") -> None:
    try:
        contacts = _get_contacts()
        cmd = command.lower()
        
        mode = "video" if "video" in cmd else "audio" if "audio" in cmd else None

        contact_name = None
        sorted_contacts = sorted(contacts.keys(), key=len, reverse=True)
        
        for name in sorted_contacts:
            if re.search(rf'\b{re.escape(name)}\b', cmd):
                contact_name = name
                break
        
        if not contact_name:
            fillers = r'\b(?:make|start|an?|whatsapp|video|audio|call|to|on|for|please|hey|aura|ka|with)\b'
            name_query = re.sub(fillers, ' ', cmd)
            name_query = " ".join(name_query.split()).strip()
            
            if name_query:
                for name in sorted_contacts:
                    if name == name_query or name in name_query or name_query in name:
                        contact_name = name
                        break

        if not contact_name:
            talk("Who would you like to call?")
            contact_name = accept_command_text()
            if not contact_name:
                return
            contact_name = contact_name.lower().strip()
            
            found = False
            for name in sorted_contacts:
                if name == contact_name or name in contact_name:
                    contact_name = name
                    found = True
                    break
            
            if not found:
                talk(f"Sorry, I couldn't find {contact_name} in your contacts.")
                return

        if not mode:
            talk(f"Would you like an audio call or a video call with {contact_name}?")
            call_type = accept_command_text()
            if not call_type:
                return
            call_type = call_type.lower()
            mode = "video" if "video" in call_type else "audio"

        number = "".join(filter(str.isdigit, contacts[contact_name]))
        
        url = f"whatsapp://send?phone={number}"
        
        talk(f"Starting {mode} call with {contact_name} via WhatsApp.")
        threading.Thread(target=webbrowser.open, args=(url,), daemon=True).start()
        
        time.sleep(1.5)
        pyautogui.press('enter') 
        
        time.sleep(10)
        
        def find_whatsapp():
            hwnds = []
            win32gui.EnumWindows(lambda h, l: l.append(h) if "WhatsApp" in win32gui.GetWindowText(h) else None, hwnds)
            return hwnds[0] if hwnds else None

        hwnd = find_whatsapp()
        if not hwnd:
            talk("Could not find WhatsApp window.")
            return

        try:
            win32gui.ShowWindow(hwnd, 5)
            win32api.keybd_event(win32con.VK_MENU, 0, 0, 0)
            win32gui.SetForegroundWindow(hwnd)
            win32api.keybd_event(win32con.VK_MENU, 0, win32con.KEYEVENTF_KEYUP, 0)
        except Exception as e:
            logger.warning("Focus failed: %s", e)

        time.sleep(1)
        rect = win32gui.GetWindowRect(hwnd)
        win_left, win_top, win_right, win_bottom = rect
        
        call_btn_x = win_right - 180
        call_btn_y = win_top + 60
        
        talk(f"Opening call menu for {contact_name}...")
        pyautogui.moveTo(call_btn_x, call_btn_y, duration=0.5)
        pyautogui.click()
        time.sleep(2)
        
        if mode == "video":
            talk("Starting video call...")
            pyautogui.moveTo(win_right - 200, win_top + 180, duration=0.5)
            pyautogui.click()
        else:
            talk("Starting voice call...")
            pyautogui.moveTo(win_right - 400, win_top + 180, duration=0.5)
            pyautogui.click()
            
        logger.info("WhatsApp %s call sequence completed for %s", mode, contact_name)

    except Exception as exc:
        logger.error("WhatsApp call command failed: %s", exc)
        talk("Sorry, I couldn't initiate the call.")

def command_speed_dial(command: str) -> None:
    contacts = _get_contacts()
    contact_name = command.lower()
    fillers = r'\b(?:call|dial|phone|ring)\b'
    contact_name = re.sub(fillers, '', contact_name)
    contact_name = contact_name.strip()

    if not contact_name:
        talk("Please specify who to call. For example, say: call John.")
        return

    if contact_name in contacts:
        number = contacts[contact_name].replace("+", "")
        talk(f"Opening WhatsApp call to {contact_name}.")
        webbrowser.open(f"https://wa.me/{number}")
    else:
        talk(f"Sorry, I don't have {contact_name} in my contacts.")

def command_read_clipboard() -> None:
    try:
        import subprocess
        result = subprocess.run(
            ["powershell", "-command", "Get-Clipboard"],
            capture_output=True, text=True, timeout=5
        )
        text = result.stdout.strip()
        if text:
            talk(f"Your clipboard contains: {text}")
        else:
            talk("Your clipboard is empty.")
    except Exception as exc:
        logger.warning("Clipboard read failed: %s", exc)
        talk("Sorry, I couldn't access the clipboard.")

def command_emergency_sos(gps_lat: float = None, gps_lon: float = None) -> None:
    emergency_number = None
    emergency_name = None
    try:
        db_obj = __import__("core.db", fromlist=["get_db"]).get_db()
        doc = db_obj.contacts.find_one({"is_emergency": True}, {"_id": 0})
        if doc:
            emergency_number = doc["phone"]
            emergency_name = doc["name"].title()
    except Exception as exc:
        logger.warning("Could not query emergency contact flag: %s", exc)

    if not emergency_number:
        contacts = _get_contacts()
        for fallback in ["emergency", "sos", "mom", "dad", "help"]:
            if fallback in contacts:
                emergency_number = contacts[fallback]
                emergency_name = fallback.title()
                break

    if not emergency_number:
        talk("No emergency contact found. Please save a contact and mark it as emergency first.")
        return

    location_str = "Unknown location"
    maps_link = ""
    try:
        if gps_lat and gps_lon:
            lat, lon = gps_lat, gps_lon
            maps_link = f" Location: https://maps.google.com/?q={lat},{lon}"
            headers = {"User-Agent": "AURA-VoiceAssistant/1.0"}
            rev_url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lon}"
            try:
                rev_data = requests.get(rev_url, headers=headers, timeout=5).json()
                addr = rev_data.get("address", {})
                city = addr.get("city", addr.get("town", addr.get("village", addr.get("county", ""))))
                state = addr.get("state", "")
                if city:
                    location_str = f"{city}, {state}".strip(", ")
                else:
                    location_str = "Live GPS Coordinates"
            except Exception:
                location_str = "Live GPS Coordinates"
        else:
            loc = requests.get("http://ip-api.com/json/", timeout=5).json()
            city = loc.get("city", "")
            country = loc.get("country", "")
            lat, lon = loc.get("lat", ""), loc.get("lon", "")
            location_str = f"{city}, {country}".strip(", ")
            if lat and lon:
                maps_link = f" Location: https://maps.google.com/?q={lat},{lon}"
    except Exception as exc:
        logger.warning("Could not get location for SOS: %s", exc)

    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    name_display = emergency_name or "Emergency Contact"
    message = (
        f"🚨 EMERGENCY SOS from AURA!\n"
        f"I need immediate help. Please respond right away.\n"
        f"Time: {now}\n"
        f"Approximate location: {location_str}.{maps_link}\n"
        f"— Sent via AURA Voice Assistant"
    )
    encoded = urllib.parse.quote(message)
    number = emergency_number.replace("+", "")

    import pyautogui
    import time

    talk(f"Sending emergency SOS to {name_display}. Stay calm.")
    webbrowser.open(f"https://wa.me/{number}?text={encoded}")
    
    time.sleep(8)
    pyautogui.press('enter')
    
    talk(f"Emergency message sent to {name_display} via WhatsApp. Help is on the way. Stay safe.")
    logger.warning("SOS sent to %s (%s) from location: %s", name_display, number, location_str)

def command_export_conversation() -> None:
    try:
        from core.ai_chat import get_conversation_history
        history = get_conversation_history()

        if not history:
            talk("There's no conversation to save yet.")
            return

        import os
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        filepath = os.path.join(desktop, f"aura_chat_{timestamp}.txt")

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"AURA Conversation Log — {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
            f.write("=" * 50 + "\n\n")
            for msg in history:
                role = "You" if msg["role"] == "user" else "AURA"
                f.write(f"{role}: {msg['content']}\n\n")

        talk("Conversation saved to your Desktop.")
        logger.info("Conversation exported to %s", filepath)

    except Exception as exc:
        logger.error("Export failed: %s", exc)
        talk("Sorry, I couldn't save the conversation.")
