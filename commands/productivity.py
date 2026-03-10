import re
import math
import time
import datetime
import threading
import json
import requests
from core.voice import talk, accept_command_text

active_timers = []
active_reminders = []
active_alarms = []

TODO_FILE = "data/todo_list.json"

def command_calculate(command):
    expr = command
    for keyword in ["calculate", "what is", "what's", "compute", "solve", "how much is"]:
        expr = expr.replace(keyword, "")

    replacements = {
        "plus": "+", "add": "+", "added to": "+",
        "minus": "-", "subtract": "-", "subtracted from": "-",
        "times": "*", "multiplied by": "*", "into": "*", "x": "*",
        "divided by": "/", "over": "/",
        "power": "**", "to the power of": "**", "raised to": "**",
        "modulo": "%", "mod": "%",
        "percent": "/100",
    }
    for spoken, symbol in replacements.items():
        expr = expr.replace(spoken, symbol)

    expr = re.sub(r'square root of\s*(\d+\.?\d*)', r'math.sqrt(\1)', expr)
    expr = expr.strip()
    
    safe_chars = set("0123456789+-*/().% ")
    if not all(c in safe_chars or c in "mathsqrt.," for c in expr):
        talk("Sorry, I couldn't parse that math expression.")
        return

    try:
        result = eval(expr, {"__builtins__": {}, "math": math})
        if isinstance(result, float):
            result = round(result, 4)
        talk(f"The answer is {result}")
    except Exception:
        talk("Sorry, I couldn't calculate that. Please try again.")

def command_set_timer(command):
    minutes = 0
    seconds = 0
    min_match = re.search(r'(\d+)\s*minute', command)
    sec_match = re.search(r'(\d+)\s*second', command)

    if min_match: minutes = int(min_match.group(1))
    if sec_match: seconds = int(sec_match.group(1))

    total_seconds = minutes * 60 + seconds
    if total_seconds <= 0:
        talk("Please specify a time, like 5 minutes or 30 seconds.")
        return

    label = f"{minutes} minutes" if minutes else ""
    if seconds:
        label += f" {seconds} seconds" if label else f"{seconds} seconds"

    talk(f"Timer set for {label}.")

    def timer_callback():
        time.sleep(total_seconds)
        talk(f"Time's up! Your {label} timer has finished.")

    t = threading.Thread(target=timer_callback, daemon=True)
    t.start()
    active_timers.append(t)

def command_set_reminder(command):
    minutes = 0
    min_match = re.search(r'(\d+)\s*minute', command)
    hour_match = re.search(r'(\d+)\s*hour', command)

    if min_match: minutes += int(min_match.group(1))
    if hour_match: minutes += int(hour_match.group(1)) * 60

    reminder_text = command
    for keyword in ["remind me to", "remind me", "reminder to", "reminder", "set a reminder to", "set reminder to", "after", "in"]:
        reminder_text = reminder_text.replace(keyword, "")
    reminder_text = re.sub(r'\d+\s*(minute|hour|second)s?', '', reminder_text).strip()

    if minutes <= 0:
        talk("In how many minutes should I remind you?")
        time_cmd = accept_command_text()
        if time_cmd:
            m = re.search(r'(\d+)', time_cmd)
            if m: minutes = int(m.group(1))
        if minutes <= 0:
            talk("Sorry, I couldn't set the reminder.")
            return

    if not reminder_text:
        reminder_text = "your reminder"

    talk(f"I'll remind you in {minutes} minutes to {reminder_text}.")

    def reminder_callback():
        time.sleep(minutes * 60)
        talk(f"Reminder: It's time to {reminder_text}!")

    t = threading.Thread(target=reminder_callback, daemon=True)
    t.start()
    active_reminders.append(t)

def command_set_alarm(command):
    time_match = re.search(r'(\d{1,2}):?(\d{2})?\s*(am|pm|AM|PM)?', command)
    if not time_match:
        talk("Please specify a time, like 7 AM or 6:30 PM.")
        return

    hour = int(time_match.group(1))
    minute = int(time_match.group(2)) if time_match.group(2) else 0
    period = time_match.group(3)

    if period and period.lower() == "pm" and hour != 12: hour += 12
    elif period and period.lower() == "am" and hour == 12: hour = 0

    now = datetime.datetime.now()
    alarm_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if alarm_time <= now:
        alarm_time += datetime.timedelta(days=1)

    delta = (alarm_time - now).total_seconds()
    time_str = alarm_time.strftime("%I:%M %p")
    talk(f"Alarm set for {time_str}.")

    def alarm_callback():
        time.sleep(delta)
        talk(f"Wake up! Your alarm for {time_str} is ringing!")
        for _ in range(3):
            try:
                import winsound
                winsound.Beep(1000, 500)
            except:
                pass

    t = threading.Thread(target=alarm_callback, daemon=True)
    t.start()
    active_alarms.append(t)

def load_todos():
    try:
        with open(TODO_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_todos(todos):
    with open(TODO_FILE, "w") as f:
        json.dump(todos, f, indent=2)

def command_todo(command):
    todos = load_todos()
    
    if "add" in command or "new" in command:
        task = command
        for keyword in ["add to my list", "add to list", "add to do", "add todo", "add task", "new task", "add"]:
            task = task.replace(keyword, "")
        task = task.strip()
        if not task:
            talk("What should I add to your list?")
            task = accept_command_text()
            if not task:
                return
        todos.append({"task": task, "done": False, "added": datetime.datetime.now().isoformat()})
        save_todos(todos)
        talk(f"Added '{task}' to your to-do list.")
    
    elif "read" in command or "show" in command or "what" in command or "list" in command:
        pending = [t for t in todos if not t["done"]]
        if not pending:
            talk("Your to-do list is empty. Nice work!")
        else:
            talk(f"You have {len(pending)} items on your to-do list:")
            for i, item in enumerate(pending, 1):
                talk(f"{i}. {item['task']}")
    
    elif "clear" in command or "delete all" in command:
        save_todos([])
        talk("Your to-do list has been cleared.")
    
    elif "done" in command or "complete" in command or "finished" in command:
        task_name = command
        for keyword in ["mark as done", "mark done", "completed", "complete", "finished", "done"]:
            task_name = task_name.replace(keyword, "")
        task_name = task_name.strip().lower()
        found = False
        for t in todos:
            if task_name in t["task"].lower() and not t["done"]:
                t["done"] = True
                found = True
                save_todos(todos)
                talk(f"Marked '{t['task']}' as done.")
                break
        if not found:
            talk("I couldn't find that task on your list.")
    else:
        talk("Say 'add to my list', 'read my list', 'mark done', or 'clear list'.")

def command_convert_currency(command):
    currency_names = {
        'dollar': 'USD', 'dollars': 'USD', 'usd': 'USD',
        'rupee': 'INR', 'rupees': 'INR', 'inr': 'INR',
        'euro': 'EUR', 'euros': 'EUR', 'eur': 'EUR',
        'pound': 'GBP', 'pounds': 'GBP', 'gbp': 'GBP',
        'yen': 'JPY', 'jpy': 'JPY',
        'dirham': 'AED', 'dirhams': 'AED', 'aed': 'AED',
    }
    
    amount_match = re.search(r'(\d+\.?\d*)', command)
    if not amount_match:
        talk("Please specify an amount, like convert 100 dollars to rupees.")
        return
    
    amount = float(amount_match.group(1))
    words = command.lower().split()
    from_curr = to_curr = None
    
    found_to = False
    for word in words:
        if word in ["to", "into"]:
            found_to = True
            continue
        if word in currency_names:
            if not found_to: from_curr = currency_names[word]
            else: to_curr = currency_names[word]
    
    if not from_curr: from_curr = "USD"
    if not to_curr: to_curr = "INR"
    
    try:
        url = f"https://api.exchangerate-api.com/v4/latest/{from_curr}"
        data = requests.get(url, timeout=10).json()
        rate = data["rates"].get(to_curr)
        if rate:
            result = round(amount * rate, 2)
            talk(f"{amount} {from_curr} is {result} {to_curr}.")
        else:
            talk(f"Sorry, I couldn't find the exchange rate for {to_curr}.")
    except Exception as e:
        talk("Sorry, I couldn't fetch exchange rates right now.")
