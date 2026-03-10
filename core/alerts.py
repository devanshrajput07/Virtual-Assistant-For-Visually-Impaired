import threading
import time
import json
import os
import datetime

ALERTS_FILE = "data/alerts.json"

def load_alerts():
    try:
        with open(ALERTS_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"medications": [], "custom": []}

def save_alerts(data):
    os.makedirs("data", exist_ok=True)
    with open(ALERTS_FILE, "w") as f:
        json.dump(data, f, indent=2)

def add_medication_reminder(talk, med_name, times):
    alerts = load_alerts()
    alerts["medications"].append({
        "name": med_name,
        "times": times,
        "active": True
    })
    save_alerts(alerts)
    time_str = ", ".join(times)
    talk(f"Medication reminder set for {med_name} at {time_str}.")

def start_proactive_monitor(talk):
    def monitor_loop():
        last_battery_warn = 0
        last_med_check = ""

        while True:
            try:
                import psutil
                battery = psutil.sensors_battery()
                if battery and not battery.power_plugged:
                    now = time.time()
                    if battery.percent <= 15 and (now - last_battery_warn) > 300:
                        talk(f"Warning! Battery is critically low at {battery.percent} percent. Please plug in your charger.")
                        last_battery_warn = now
                    elif battery.percent <= 30 and (now - last_battery_warn) > 600:
                        talk(f"Heads up, your battery is at {battery.percent} percent.")
                        last_battery_warn = now
            except:
                pass

            try:
                now = datetime.datetime.now()
                current_time = now.strftime("%H:%M")
                current_date = now.strftime("%Y-%m-%d")
                check_key = f"{current_date}_{current_time}"

                if check_key != last_med_check:
                    alerts = load_alerts()
                    for med in alerts.get("medications", []):
                        if not med.get("active", True):
                            continue
                        for t in med.get("times", []):
                            try:
                                med_time = datetime.datetime.strptime(t, "%I:%M %p").strftime("%H:%M")
                            except:
                                med_time = t
                            if med_time == current_time:
                                talk(f"Medication reminder: It's time to take your {med['name']}.")
                    last_med_check = check_key
            except:
                pass

            time.sleep(30)

    thread = threading.Thread(target=monitor_loop, daemon=True)
    thread.start()
    return thread
