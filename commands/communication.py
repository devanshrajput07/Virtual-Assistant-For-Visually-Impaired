import json
import urllib.parse
import webbrowser
import datetime
import os
import requests
import subprocess
from core.voice import talk, accept_command_text
from core.ai_chat import conversation_history

CONTACTS_FILE = "data/contacts.json"

def load_contacts():
    try:
        with open(CONTACTS_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        with open(CONTACTS_FILE, "w") as f:
            json.dump({}, f)
        return {}

CONTACTS = load_contacts()

def save_contact(name, number):
    try:
        with open(CONTACTS_FILE, "r") as f:
            contacts = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        contacts = {}
    contacts[name.lower()] = number
    with open(CONTACTS_FILE, "w") as f:
        json.dump(contacts, f, indent=4)
    talk(f"Saved contact {name} with number {number}.")
    global CONTACTS
    CONTACTS = contacts

def command_send_whatsapp_message(command=None):
    try:
        if not command:
            talk("What should I send and to whom?")
            command = accept_command_text()
            if not command: return

        cmd = command.lower()
        fillers = ["send", "message", "to", "on", "whatsapp", "saying", "through", "using"]
        for word in fillers: cmd = cmd.replace(word, "")
        cmd = cmd.strip()

        contact_name = None
        for name in CONTACTS.keys():
            if name in cmd:
                contact_name = name
                break

        if not contact_name:
            talk("Who should I send the message to?")
            contact_name = accept_command_text()
            if not contact_name or contact_name.lower() not in CONTACTS:
                talk("Sorry, I don't have that contact saved.")
                return
            contact_name = contact_name.lower()

        message = cmd.replace(contact_name, "").strip()
        if not message:
            talk("What message should I send?")
            message = accept_command_text()
            if not message: return

        number = CONTACTS[contact_name]
        encoded_message = urllib.parse.quote(message)
        url = f"https://wa.me/{number.replace('+', '')}?text={encoded_message}"
        talk(f"Opening WhatsApp to send '{message}' to {contact_name}.")
        webbrowser.open(url)
    except Exception as e:
        talk(f"Sorry, could not send the message. {e}")

def command_speed_dial(command):
    contact_name = command
    for keyword in ["call", "dial", "phone", "ring"]:
        contact_name = contact_name.replace(keyword, "")
    contact_name = contact_name.strip().lower()
    
    if not contact_name:
        talk("Who should I call?")
        contact_name = accept_command_text()
        if not contact_name: return
        contact_name = contact_name.lower()
    
    if contact_name in CONTACTS:
        number = CONTACTS[contact_name].replace("+", "")
        talk(f"Opening WhatsApp call to {contact_name}.")
        webbrowser.open(f"https://wa.me/{number}")
    else:
        talk(f"Sorry, I don't have {contact_name} in my contacts.")

def command_read_clipboard():
    try:
        result = subprocess.run(['powershell', '-command', 'Get-Clipboard'], 
                              capture_output=True, text=True, timeout=5)
        text = result.stdout.strip()
        if text: talk(f"Your clipboard says: {text}")
        else: talk("Your clipboard is empty.")
    except Exception as e:
        talk("Sorry, I couldn't read the clipboard.")

def command_emergency_sos():
    emergency_contact = CONTACTS.get("emergency") or CONTACTS.get("sos") or CONTACTS.get("mom") or CONTACTS.get("dad")
    if not emergency_contact:
        talk("No emergency contact found. Please save a contact named 'emergency' first.")
        return
    
    try:
        loc_data = requests.get("http://ip-api.com/json/", timeout=5).json()
        location = f"{loc_data.get('city', 'Unknown')}, {loc_data.get('country', '')}"
        lat = loc_data.get('lat', '')
        lon = loc_data.get('lon', '')
        maps_link = f"https://maps.google.com/?q={lat},{lon}" if lat and lon else ""
    except:
        location = "Unknown location"
        maps_link = ""
    
    message = f"🚨 EMERGENCY SOS from VAVI Assistant! I need help. My approximate location: {location}. {maps_link}"
    number = emergency_contact.replace("+", "")
    encoded = urllib.parse.quote(message)
    
    talk("Sending emergency SOS now!")
    webbrowser.open(f"https://wa.me/{number}?text={encoded}")
    talk("Emergency message sent via WhatsApp. Stay safe.")

def command_export_conversation():
    if not conversation_history:
        talk("There's no conversation to save yet.")
        return
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    desktop = os.path.join(os.path.expanduser("~"), "Desktop")
    filepath = os.path.join(desktop, f"vavi_chat_{timestamp}.txt")
    
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"VAVI Conversation Log - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
            f.write("=" * 50 + "\n\n")
            for msg in conversation_history:
                role = "You" if msg["role"] == "user" else "VAVI"
                f.write(f"{role}: {msg['content']}\n\n")
        talk(f"Conversation saved to your Desktop.")
    except Exception as e:
        talk("Sorry, I couldn't save the conversation.")
