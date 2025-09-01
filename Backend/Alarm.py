import datetime
import time
import threading
import pygame
import os
from Backend.TextToSpeech import TextToSpeech

# Initialize pygame at module level
try:
    pygame.init()
    pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
    print("[INFO] Pygame mixer initialized successfully")
except Exception as e:
    print(f"[ERROR] Failed to initialize pygame mixer: {e}")

alarms = []

def parse_alarm_time(text):
    import re
    from datetime import datetime as dt
    import datetime

    # First try to match time with AM/PM format
    am_pm_pattern = re.search(r'(\d{1,2})(?::(\d{2}))?\s*(a\.?m\.?|p\.?m\.?)', text, re.IGNORECASE)
    if am_pm_pattern:
        hour = int(am_pm_pattern.group(1))
        minute = int(am_pm_pattern.group(2)) if am_pm_pattern.group(2) else 0
        period = am_pm_pattern.group(3).lower().replace('.', '')  # normalize to am or pm

        if period.startswith('p') and hour != 12:
            hour += 12
        if period.startswith('a') and hour == 12:
            hour = 0

        now = dt.now()
        alarm_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)

        if alarm_time <= now:
            alarm_time += datetime.timedelta(days=1)

        print(f"[DEBUG] Parsed alarm time (AM/PM format): {alarm_time}")
        return alarm_time

    # Try to match 24-hour format (e.g., "14:30" or "14 30")
    hour24_pattern = re.search(r'(\d{1,2})(?::|\s)(\d{2})', text)
    if hour24_pattern:
        hour = int(hour24_pattern.group(1))
        minute = int(hour24_pattern.group(2))

        if 0 <= hour < 24 and 0 <= minute < 60:
            now = dt.now()
            alarm_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)

            if alarm_time <= now:
                alarm_time += datetime.timedelta(days=1)

            print(f"[DEBUG] Parsed alarm time (24-hour format): {alarm_time}")
            return alarm_time

    # Try to match just an hour (e.g., "at 7" or "at seven")
    hour_words = {
        'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5, 'six': 6, 'seven': 7, 
        'eight': 8, 'nine': 9, 'ten': 10, 'eleven': 11, 'twelve': 12
    }
    
    # Try numeric hour
    hour_pattern = re.search(r'\b(\d{1,2})\s*(?:o\'clock)?\b', text)
    if hour_pattern:
        hour = int(hour_pattern.group(1))
        
        # Determine if it's AM or PM based on context
        is_pm = False
        if 'evening' in text.lower() or 'night' in text.lower() or 'afternoon' in text.lower():
            is_pm = True
        elif 'morning' in text.lower():
            is_pm = False
        else:
            # If not specified, assume PM for hours 1-11, and AM for 12
            current_hour = dt.now().hour
            if 1 <= hour <= 11 and current_hour >= 12:
                is_pm = True
        
        if is_pm and hour != 12:
            hour += 12
        if not is_pm and hour == 12:
            hour = 0
            
        now = dt.now()
        alarm_time = now.replace(hour=hour, minute=0, second=0, microsecond=0)
        
        if alarm_time <= now:
            alarm_time += datetime.timedelta(days=1)

        print(f"[DEBUG] Parsed alarm time (24-hour format): {alarm_time}")
        return alarm_time

    print("[DEBUG] Could not parse any time format from the text.")
    return None

# Initialize pygame mixer
try:
    pygame.init()
    pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
    print("[INFO] Pygame mixer initialized successfully")
except Exception as e:
    print(f"[ERROR] Failed to initialize pygame mixer: {e}")

def alarm_checker():
    # Define the alarm sound path
    alarm_sound_path = os.path.join(os.path.dirname(__file__), "..", "alarm.mp3")
    
    # Check if alarm sound exists
    if not os.path.exists(alarm_sound_path):
        print(f"[WARNING] Alarm sound file not found at: {alarm_sound_path}")
    else:
        print(f"[INFO] Alarm sound file found at: {alarm_sound_path}")
    
    while True:
        now = datetime.datetime.now()
        for alarm in alarms[:]:  # safe copy of list
            print(f"[DEBUG] Now: {now}, Checking alarm: {alarm}")
            if now >= alarm:
                print("[DEBUG] Alarm triggered!")
                
                # Play alarm sound
                try:
                    if os.path.exists(alarm_sound_path):
                        print(f"[INFO] Playing alarm sound: {alarm_sound_path}")
                        # Reinitialize mixer to ensure it's ready
                        pygame.mixer.quit()
                        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
                        pygame.mixer.music.load(alarm_sound_path)
                        pygame.mixer.music.set_volume(1.0)  # Full volume
                        pygame.mixer.music.play(loops=5)  # Play 5 times
                        
                        # Play the alarm for 7-8 seconds
                        alarm_start_time = time.time()
                        while pygame.mixer.music.get_busy() and (time.time() - alarm_start_time) < 7.5:
                            time.sleep(0.1)  # Small sleep to prevent CPU hogging
                        pygame.mixer.music.stop()  # Ensure music stops after 7.5 seconds
                    else:
                        print(f"[WARNING] Alarm sound file not found at: {alarm_sound_path}")
                except Exception as e:
                    print(f"[ERROR] Failed to play alarm sound: {e}")
                
                # Remove the alarm from the list after it's triggered
                alarms.remove(alarm)
                
        time.sleep(5)  # Check every 5 seconds

def SetAlarm(text):
    try:
        alarm_time = parse_alarm_time(text)
        if alarm_time:
            alarms.append(alarm_time)
            print(f"[DEBUG] Alarm set for: {alarm_time}")
            print(f"Alarm set for {alarm_time.strftime('%I:%M %p')}, sir.")
            return True
        else:
            print("[ERROR] Could not parse alarm time from text")
            print("Sorry sir, I couldn't understand the alarm time.")
            return False
    except Exception as e:
        print(f"[ERROR] Error setting alarm: {e}")
        print("Sorry sir, there was an error setting the alarm.")
        return False

# Start the alarm checker in a separate thread
alarm_thread = threading.Thread(target=alarm_checker, daemon=True)
alarm_thread.start()
