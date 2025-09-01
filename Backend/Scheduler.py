import json
import os
import threading
import time
from datetime import datetime
import dateparser
import re
import playsound
from TextToSpeech import TextToSpeech as speak

TASKS_FILE = "tasks.json"

def parse_tasks_from_input(user_input):
    tasks = []
    pattern = rf"(?P<task>.+?)\s+(at|by|on|around)\s+(?P<time>[\w\s:]+)"
    matches = re.finditer(pattern, user_input, re.IGNORECASE)

    for match in matches:
        task = match.group("task").strip().capitalize()
        time_text = match.group("time").strip()
        time_obj = dateparser.parse(time_text)
        if time_obj:
            tasks.append({"task": task, "time": time_obj.strftime("%H:%M")})
    return tasks

def save_tasks(tasks):
    if os.path.exists(TASKS_FILE):
        with open(TASKS_FILE, "r") as f:
            existing = json.load(f)
    else:
        existing = []

    existing.extend(tasks)
    with open(TASKS_FILE, "w") as f:
        json.dump(existing, f, indent=4)

def set_reminder(task, time_str):
    def wait_and_alert():
        task_time = datetime.strptime(time_str, "%H:%M").time()
        while True:
            now = datetime.now().time()
            if now.hour == task_time.hour and now.minute == task_time.minute:
                speak(f"Reminder! It's time for: {task}")
                try:
                    alarm_path = os.path.join(os.getcwd(), "alarm.mp3")
                    playsound.playsound(alarm_path)
                except Exception as e:
                    print(f"[ERROR] Alarm sound failed: {e}")
                    speak("Alarm sound failed to play.")
                break
            time.sleep(10)  # Check every 10 seconds

    t = threading.Thread(target=wait_and_alert)
    t.daemon = True
    t.start()

def schedule_tasks(user_input):
    speak("Scheduling your tasks for today.")
    tasks = parse_tasks_from_input(user_input)

    if not tasks:
        speak("Sorry, I couldn't understand the task timings.")
        return

    save_tasks(tasks)

    for t in tasks:
        set_reminder(t["task"], t["time"])

    speak("Tasks scheduled with reminders.")
    for t in tasks:
        speak(f"{t['task']} at {t['time']}")
