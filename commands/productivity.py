"""
commands/productivity.py
All productivity commands for AURA.
To-do and alert data stored in MongoDB Atlas.

Fixes:
  - Replaced eval() with simpleeval (safe expression evaluation)
  - Todo list uses MongoDB
  - Proper logging
"""

import re
import math
import time
import datetime
import threading
import logging

logger = logging.getLogger("aura.commands.productivity")

active_timers: list[threading.Thread] = []
active_reminders: list[threading.Thread] = []
active_alarms: list[threading.Thread] = []



def command_calculate(command: str) -> None:
    from core.voice import talk
    expr = command.lower()
    for kw in ["calculate", "what is", "what's", "compute", "solve", "how much is"]:
        expr = expr.replace(kw, "")

    replacements = {
        "plus": "+", "add": "+", "added to": "+",
        "minus": "-", "subtract": "-", "subtracted from": "-",
        "times": "*", "multiplied by": "*", "into": "*",
        "divided by": "/", "over": "/",
        "to the power of": "**", "raised to": "**", "power": "**",
        "modulo": "%", "mod": "%",
        "percent": "/100",
    }
    for word, symbol in replacements.items():
        expr = expr.replace(word, symbol)

    # Handle square root
    expr = re.sub(r"square root of\s*(\d+\.?\d*)", r"sqrt(\1)", expr)
    expr = expr.strip()

    try:
        from simpleeval import simple_eval, EvalWithCompoundTypes
        result = simple_eval(expr, functions={"sqrt": math.sqrt, "abs": abs, "round": round})
        if isinstance(result, float):
            result = round(result, 6)
            # Strip trailing zeros
            result = int(result) if result == int(result) else result
        talk(f"The answer is {result}.")
    except Exception:
        # Fallback: try stricter re-check before eval
        safe_chars = set("0123456789+-*/().%^ ")
        clean = re.sub(r"sqrt\([^)]*\)", "", expr)
        if all(c in safe_chars for c in clean):
            try:
                safe_globals = {"__builtins__": {}, "math": math, "sqrt": math.sqrt}
                result = eval(compile(expr, "<calc>", "eval"), safe_globals)  # noqa: S307
                if isinstance(result, float):
                    result = round(result, 6)
                talk(f"The answer is {result}.")
                return
            except Exception:
                pass
        talk("Sorry, I couldn't calculate that. Please try a simpler expression.")
        logger.debug("Calculator failed on: %s", expr)



def command_set_timer(command: str) -> None:
    from core.voice import talk
    minutes = 0
    seconds = 0

    min_m = re.search(r"(\d+)\s*minute", command)
    sec_m = re.search(r"(\d+)\s*second", command)
    if min_m:
        minutes = int(min_m.group(1))
    if sec_m:
        seconds = int(sec_m.group(1))

    total = minutes * 60 + seconds
    if total <= 0:
        talk("Please specify a duration, for example 5 minutes or 30 seconds.")
        return

    parts = []
    if minutes:
        parts.append(f"{minutes} minute{'s' if minutes != 1 else ''}")
    if seconds:
        parts.append(f"{seconds} second{'s' if seconds != 1 else ''}")
    label = " and ".join(parts)

    talk(f"Timer set for {label}.")
    logger.info("Timer set: %s", label)

    def _timer():
        time.sleep(total)
        talk(f"Time's up! Your {label} timer has finished.")

    t = threading.Thread(target=_timer, daemon=True, name=f"Timer-{label}")
    t.start()
    active_timers.append(t)



def command_set_reminder(command: str) -> None:
    from core.voice import talk, accept_command_text
    minutes = 0

    min_m = re.search(r"(\d+)\s*minute", command)
    hr_m = re.search(r"(\d+)\s*hour", command)
    if min_m:
        minutes += int(min_m.group(1))
    if hr_m:
        minutes += int(hr_m.group(1)) * 60

    # Extract reminder text (remove time words)
    reminder_text = command
    for kw in ["remind me to", "remind me", "reminder to", "reminder", "set a reminder to",
                "set reminder to", "after", "in"]:
        reminder_text = reminder_text.replace(kw, "")
    reminder_text = re.sub(r"\d+\s*(minute|hour|second)s?", "", reminder_text).strip()
    if not reminder_text:
        reminder_text = "your reminder"

    if minutes <= 0:
        talk("In how many minutes should I remind you?")
        response = accept_command_text()
        if response:
            m = re.search(r"(\d+)", response)
            if m:
                minutes = int(m.group(1))
        if minutes <= 0:
            talk("Sorry, I couldn't set the reminder.")
            return

    talk(f"I'll remind you in {minutes} minute{'s' if minutes != 1 else ''} to {reminder_text}.")
    logger.info("Reminder set: %d min → %s", minutes, reminder_text)

    def _reminder():
        time.sleep(minutes * 60)
        talk(f"Reminder: it's time to {reminder_text}!")

    t = threading.Thread(target=_reminder, daemon=True, name=f"Reminder-{reminder_text[:20]}")
    t.start()
    active_reminders.append(t)



def command_set_alarm(command: str) -> None:
    from core.voice import talk
    m = re.search(r"(\d{1,2}):?(\d{2})?\s*(am|pm|AM|PM)?", command)
    if not m:
        talk("Please specify a time, such as 7 AM or 6:30 PM.")
        return

    hour = int(m.group(1))
    minute = int(m.group(2)) if m.group(2) else 0
    period = (m.group(3) or "").lower()

    if period == "pm" and hour != 12:
        hour += 12
    elif period == "am" and hour == 12:
        hour = 0

    now = datetime.datetime.now()
    alarm_dt = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if alarm_dt <= now:
        alarm_dt += datetime.timedelta(days=1)

    delta = (alarm_dt - now).total_seconds()
    time_str = alarm_dt.strftime("%I:%M %p")
    talk(f"Alarm set for {time_str}.")
    logger.info("Alarm set for %s (%.0f seconds away).", time_str, delta)

    def _alarm():
        time.sleep(delta)
        talk(f"Wake up! Your alarm for {time_str} is ringing!")
        for _ in range(3):
            try:
                import winsound
                winsound.Beep(1000, 600)
                time.sleep(0.4)
            except Exception:
                pass

    t = threading.Thread(target=_alarm, daemon=True, name=f"Alarm-{time_str}")
    t.start()
    active_alarms.append(t)



def command_todo(command: str) -> None:
    from core.voice import talk, accept_command_text
    from core.db import get_todos, add_todo, complete_todo, clear_todos

    try:
        if any(k in command for k in ["add", "new"]):
            task = command
            for kw in ["add to my list", "add to list", "add to do", "add todo",
                        "add task", "new task", "add"]:
                task = task.replace(kw, "")
            task = task.strip()
            if not task:
                talk("What should I add to your list?")
                task = accept_command_text()
                if not task:
                    return
            add_todo(task)
            talk(f"Added '{task}' to your to-do list.")

        elif any(k in command for k in ["clear", "delete all"]):
            clear_todos()
            talk("Your to-do list has been cleared.")

        elif any(k in command for k in ["read", "show", "what", "list"]):
            pending = get_todos(pending_only=True)
            if not pending:
                talk("Your to-do list is empty. Nice work!")
            else:
                talk(f"You have {len(pending)} items on your to-do list.")
                for i, item in enumerate(pending, 1):
                    talk(f"{i}. {item['task']}")

        elif any(k in command for k in ["done", "complete", "finished"]):
            task_frag = command
            for kw in ["mark as done", "mark done", "completed", "complete", "finished", "done"]:
                task_frag = task_frag.replace(kw, "")
            task_frag = task_frag.strip()
            if complete_todo(task_frag):
                talk(f"Marked as done.")
            else:
                talk("I couldn't find that task on your list.")

        else:
            talk("Say 'add to my list', 'read my list', 'mark done', or 'clear list'.")

    except Exception as exc:
        logger.error("Todo command error: %s", exc)
        talk("Sorry, I couldn't access your to-do list right now.")



CURRENCY_MAP = {
    "dollar": "USD", "dollars": "USD", "usd": "USD",
    "rupee": "INR", "rupees": "INR", "inr": "INR",
    "euro": "EUR", "euros": "EUR", "eur": "EUR",
    "pound": "GBP", "pounds": "GBP", "gbp": "GBP",
    "yen": "JPY", "jpy": "JPY",
    "dirham": "AED", "dirhams": "AED", "aed": "AED",
    "franc": "CHF", "francs": "CHF", "chf": "CHF",
}


def command_convert_currency(command: str) -> None:
    from core.voice import talk
    import requests

    amount_m = re.search(r"(\d+\.?\d*)", command)
    if not amount_m:
        talk("Please specify an amount, like convert 100 dollars to rupees.")
        return

    amount = float(amount_m.group(1))
    words = command.lower().split()
    from_curr = to_curr = None
    seen_to = False

    for word in words:
        if word in ("to", "into"):
            seen_to = True
            continue
        if word in CURRENCY_MAP:
            if not seen_to:
                from_curr = CURRENCY_MAP[word]
            else:
                to_curr = CURRENCY_MAP[word]

    from_curr = from_curr or "USD"
    to_curr = to_curr or "INR"

    try:
        # Try cached rate first
        from core.db import cache_get, cache_set
        cache_key = f"fx_{from_curr}_{to_curr}"
        rate = cache_get(cache_key)

        if rate is None:
            data = requests.get(f"https://api.exchangerate-api.com/v4/latest/{from_curr}", timeout=10).json()
            rate = data["rates"].get(to_curr)
            if rate:
                cache_set(cache_key, rate, ttl_seconds=3600)  # cache 1 hour

        if rate:
            result = round(amount * rate, 2)
            talk(f"{amount} {from_curr} equals {result} {to_curr}.")
        else:
            talk(f"Sorry, I couldn't find the exchange rate for {to_curr}.")
    except Exception as exc:
        logger.warning("Currency conversion failed: %s", exc)
        talk("Sorry, I couldn't fetch exchange rates right now.")
