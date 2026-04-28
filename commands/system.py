import os
import datetime
import pyautogui
import psutil
import subprocess
import webbrowser
import urllib.parse
import time
from core.voice import talk, accept_command_text
from config.settings import APP_MAP, WEBSITE_MAP

def command_take_screenshot():
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    desktop = os.path.join(os.path.expanduser("~"), "Desktop")
    try:
        filepath = os.path.join(desktop, f"screenshot_{timestamp}.png")
        screenshot = pyautogui.screenshot()
        screenshot.save(filepath)
        talk("Screenshot captured and saved to your Desktop.")
    except Exception:
        try:
            filepath = f"screenshot_{timestamp}.png"
            screenshot = pyautogui.screenshot()
            screenshot.save(filepath)
            talk(f"Screenshot saved to folder as {filepath}.")
        except Exception:
            talk(f"Could not take screenshot. Memory or display error.")

def command_volume_control(command):
    try:
        if "mute" in command or "silent" in command:
            pyautogui.press("volumemute")
            talk("Volume muted.")
        elif "up" in command or "increase" in command or "louder" in command:
            for _ in range(5): pyautogui.press("volumeup")
            talk("Volume increased.")
        elif "down" in command or "decrease" in command or "lower" in command or "softer" in command:
            for _ in range(5): pyautogui.press("volumedown")
            talk("Volume decreased.")
        elif "max" in command or "full" in command:
            for _ in range(20): pyautogui.press("volumeup")
            talk("Volume set to maximum.")
        elif "min" in command or "minimum" in command:
            for _ in range(20): pyautogui.press("volumedown")
            talk("Volume set to minimum.")
        else:
            talk("Say volume up, volume down, or mute.")
    except Exception as e:
        talk(f"Sorry, I couldn't control the volume. {e}")

def command_battery_status():
    try:
        battery = psutil.sensors_battery()
        if battery is None:
            talk("I couldn't detect a battery. You might be on a desktop.")
            return
        percent = battery.percent
        plugged = "plugged in" if battery.power_plugged else "not plugged in"
        secs_left = battery.secsleft

        if battery.power_plugged or secs_left == psutil.POWER_TIME_UNLIMITED:
            time_suffix = ", and it is charging."
        elif secs_left == psutil.POWER_TIME_UNKNOWN or secs_left < 0 or secs_left > 86400:
            # Windows can't report remaining time accurately — just skip it
            time_suffix = "."
        else:
            hours = secs_left // 3600
            mins = (secs_left % 3600) // 60
            if hours > 0:
                time_suffix = f", with approximately {hours} hours and {mins} minutes remaining."
            else:
                time_suffix = f", with approximately {mins} minutes remaining."

        talk(f"Battery is at {round(percent)} percent, {plugged}{time_suffix}")
    except Exception as e:
        talk(f"Sorry, I couldn't check the battery. {e}")

def command_system_info():
    try:
        cpu = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        mem_used = round(memory.used / (1024**3), 1)
        mem_total = round(memory.total / (1024**3), 1)
        talk(f"CPU usage is {cpu} percent. Memory usage is {mem_used} of {mem_total} gigabytes.")
    except Exception as e:
        talk(f"Sorry, I couldn't get system info. {e}")

def command_brightness_control(command):
    try:
        if "up" in command or "increase" in command or "brighter" in command:
            subprocess.run(['powershell', '(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1, [Math]::Min(100, (Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightness).CurrentBrightness + 20))'], capture_output=True, shell=True)
            talk("Brightness increased.")
        elif "down" in command or "decrease" in command or "dimmer" in command or "dim" in command:
            subprocess.run(['powershell', '(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1, [Math]::Max(0, (Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightness).CurrentBrightness - 20))'], capture_output=True, shell=True)
            talk("Brightness decreased.")
        elif "max" in command or "full" in command:
            subprocess.run(['powershell', '(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1, 100)'], capture_output=True, shell=True)
            talk("Brightness set to maximum.")
        elif "min" in command or "low" in command:
            subprocess.run(['powershell', '(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1, 10)'], capture_output=True, shell=True)
            talk("Brightness set to minimum.")
        else:
            talk("Say brightness up, brightness down, or brightness max.")
    except Exception as e:
        talk("Sorry, I couldn't control brightness on this device.")

def command_open_app(command):
    app_name = command.replace("open", "").replace("launch", "").replace("start", "").strip()
    if app_name in APP_MAP:
        talk(f"Opening {app_name}.")
        try: os.startfile(APP_MAP[app_name])
        except: subprocess.Popen(APP_MAP[app_name], shell=True)
    else:
        talk(f"Trying to open {app_name}.")
        try: os.startfile(app_name)
        except: talk(f"Sorry, I couldn't find {app_name}.")

def command_open_website(command):
    site = command.replace("open", "").replace("go to", "").replace("visit", "").strip()
    if site in WEBSITE_MAP:
        talk(f"Opening {site}.")
        webbrowser.open(WEBSITE_MAP[site])
    elif "." in site:
        url = site if site.startswith("http") else f"https://{site}"
        talk(f"Opening {site}.")
        webbrowser.open(url)
    else:
        talk(f"Sorry, I don't know that website. Let me search for it.")
        webbrowser.open(f"https://www.google.com/search?q={urllib.parse.quote(site)}")

def command_google_search(command):
    query = command
    for keyword in ["search for", "search", "google", "look up", "find me"]:
        query = query.replace(keyword, "")
    query = query.strip()
    if not query:
        talk("Please specify what you want to search for. For example, say: search for weather in London.")
        return
    talk(f"Searching for {query}.")
    webbrowser.open(f"https://www.google.com/search?q={urllib.parse.quote(query)}")

def command_find_file(command):
    filename = command
    for keyword in ["find file", "find my", "find", "locate file", "locate", "search file", "where is"]:
        filename = filename.replace(keyword, "")
    filename = filename.strip()
    
    if not filename:
        talk("Please specify the file you want to find. For example, say: find file document.")
        return
    
    talk(f"Searching for {filename}. This may take a moment.")
    search_dirs = [
        os.path.expanduser("~/Desktop"),
        os.path.expanduser("~/Documents"),
        os.path.expanduser("~/Downloads"),
    ]
    
    found = []
    for search_dir in search_dirs:
        if not os.path.exists(search_dir): continue
        try:
            for root, dirs, files in os.walk(search_dir):
                for f in files:
                    if filename.lower() in f.lower():
                        found.append(os.path.join(root, f))
                        if len(found) >= 5: break
                if len(found) >= 5: break
        except PermissionError: continue
    
    if found:
        talk(f"I found {len(found)} matching files.")
        for f in found[:3]: talk(os.path.basename(f))
    else:
        talk(f"Sorry, I couldn't find any files matching '{filename}'.")

def command_scan_qr():
    try:
        import cv2
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            talk("Camera not detected.")
            return
        
        talk("Hold the QR code in front of the camera.")
        detector = cv2.QRCodeDetector()
        
        start_time = time.time()
        while time.time() - start_time < 10:
            ret, frame = cap.read()
            if not ret: continue
            data, _, _ = detector.detectAndDecode(frame)
            if data:
                cap.release()
                talk(f"QR code found. It says: {data}")
                if data.startswith("http"):
                    talk("It's a link. Opening it now.")
                    webbrowser.open(data)
                return
        
        cap.release()
        talk("I couldn't detect any QR code.")
    except Exception as e:
        talk("Sorry, I couldn't scan the QR code.")
