import threading
import time
import datetime
import logging

logger = logging.getLogger("aura.alerts")

def add_medication_reminder(talk_fn, med_name: str, times: list[str]) -> None:
    try:
        from core.db import add_alert
        add_alert("medication", {"name": med_name, "times": times})
        time_str = ", ".join(times)
        talk_fn(f"Medication reminder set for {med_name} at {time_str}.")
        logger.info("Medication reminder added: %s at %s", med_name, time_str)
    except Exception as exc:
        logger.error("Failed to save medication reminder: %s", exc)
        talk_fn("Sorry, I couldn't save the medication reminder.")

def trigger_emergency_alert(talk_fn) -> None:
    logger.warning("EMERGENCY ALERT TRIGGERED")
    talk_fn("Emergency alert activated! Sending SOS now.")

def start_proactive_monitor(talk_fn) -> threading.Thread:
    def monitor_loop():
        last_battery_warn: float = 0.0
        last_med_check: str = ""

        while True:
            try:
                import psutil
                battery = psutil.sensors_battery()
                if battery and not battery.power_plugged:
                    now_ts = time.time()
                    pct = battery.percent
                    if pct <= 10 and (now_ts - last_battery_warn) > 120:
                        talk_fn(f"Critical warning! Battery is at {int(pct)} percent. Please charge immediately.")
                        last_battery_warn = now_ts
                    elif pct <= 20 and (now_ts - last_battery_warn) > 300:
                        talk_fn(f"Warning: battery is at {int(pct)} percent. Consider charging soon.")
                        last_battery_warn = now_ts
                    elif pct <= 30 and (now_ts - last_battery_warn) > 600:
                        talk_fn(f"Heads up — your battery is at {int(pct)} percent.")
                        last_battery_warn = now_ts
            except ImportError:
                pass
            except Exception as exc:
                logger.debug("Battery check error: %s", exc)

            try:
                now = datetime.datetime.now()
                current_time = now.strftime("%H:%M")
                current_date = now.strftime("%Y-%m-%d")
                check_key = f"{current_date}_{current_time}"

                if check_key != last_med_check:
                    last_med_check = check_key
                    try:
                        from core.db import get_alerts
                        meds = get_alerts(alert_type="medication", active_only=True)
                    except Exception as db_exc:
                        logger.debug("Could not fetch meds from DB: %s", db_exc)
                        meds = []

                    for med in meds:
                        data = med.get("data", {})
                        med_name = data.get("name", "")
                        for t in data.get("times", []):
                            try:
                                med_time_obj = datetime.datetime.strptime(t, "%I:%M %p")
                                med_time = med_time_obj.strftime("%H:%M")
                            except ValueError:
                                med_time = t
                            if med_time == current_time:
                                talk_fn(f"Medication reminder: it's time to take your {med_name}.")
                                logger.info("Medication reminder fired: %s", med_name)
            except Exception as exc:
                logger.warning("Medication monitor error: %s", exc)

            time.sleep(30)

    t = threading.Thread(target=monitor_loop, daemon=True, name="ProactiveMonitor")
    t.start()
    logger.info("Proactive monitor started.")
    return t
