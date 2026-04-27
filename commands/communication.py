"""
commands/communication.py
All communication-related commands for AURA.
Contacts stored in MongoDB Atlas (no JSON files).

Fixes:
  - Stale CONTACTS global eliminated — always read from DB
  - Emergency SOS with real location
  - Proper logging throughout
"""

import urllib.parse
import webbrowser
import datetime
import logging
import requests
import re

from core.voice import talk, accept_command_text

logger = logging.getLogger("aura.commands.communication")



def _get_contacts() -> dict[str, str]:
    """Always fetch fresh contacts from MongoDB."""
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
        cmd = " ".join(cmd.split())  # normalise whitespace

        # Find contact name in command
        contact_name = None
        for name in contacts:
            if name in cmd:
                contact_name = name
                break

        if not contact_name:
            talk("Who should I send the message to?")
            response = accept_command_text()
            if not response:
                return
            contact_name = response.lower().strip()
            if contact_name not in contacts:
                talk(f"Sorry, I don't have {contact_name} saved as a contact.")
                return

        message = cmd.replace(contact_name, "").strip()
        if not message:
            talk("What message should I send?")
            message = accept_command_text()
            if not message:
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



def command_speed_dial(command: str) -> None:
    contacts = _get_contacts()

    contact_name = command.lower()
    fillers = r'\b(?:call|dial|phone|ring)\b'
    contact_name = re.sub(fillers, '', contact_name)
    contact_name = contact_name.strip()

    if not contact_name:
        talk("Who should I call?")
        contact_name = accept_command_text()
        if not contact_name:
            return
        contact_name = contact_name.lower().strip()

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
    # Find contact flagged as emergency in MongoDB first
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

    # Fallback: look for well-known names
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

    # Get approximate location from IP or use provided GPS
    location_str = "Unknown location"
    maps_link = ""
    try:
        if gps_lat and gps_lon:
            # We have highly accurate coordinates from the browser!
            lat, lon = gps_lat, gps_lon
            maps_link = f" Location: https://maps.google.com/?q={lat},{lon}"
            
            # Try to get the city name from those coordinates (Reverse Geocoding)
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
            # Fallback to IP-based Geolocation (often inaccurate depending on ISP routing)
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

    talk(f"Sending emergency SOS to {name_display}. Stay calm.")
    webbrowser.open(f"https://wa.me/{number}?text={encoded}")
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
