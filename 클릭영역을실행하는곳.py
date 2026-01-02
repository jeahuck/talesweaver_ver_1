from pynput import keyboard, mouse
import json
import time
import os
import threading

LOG_FILE = "events.json"
SPEED = 1

if not os.path.exists(LOG_FILE):
    print("❌ events.json 없음")
    exit(1)

with open(LOG_FILE, "r", encoding="utf-8") as f:
    events = json.load(f)

kb = keyboard.Controller()
ms = mouse.Controller()

playing = False
stop_flag = False

def parse_key(key_str):
    if key_str.startswith("Key."):
        return getattr(keyboard.Key, key_str.split(".")[1])
    else:
        return keyboard.KeyCode.from_char(key_str.strip("'"))

def play_events():
    global stop_flag

    print("▶ 3초 후 재생 시작")
    for i in range(3, 0, -1):
        time.sleep(1)

    last_t = 0

    for e in events:
        if stop_flag:
            return

        delay = (e["t"] - last_t) * SPEED
        if delay > 0:
            time.sleep(delay)
        last_t = e["t"]

        t = e["type"]

        if t == "mouse_snap":
            ms.position = (e["x"], e["y"])

        elif t == "key_down":
            kb.press(parse_key(e["key"]))

        elif t == "key_up":
            kb.release(parse_key(e["key"]))

    print("✅ 재생 완료")

def on_press(key):
    global playing, stop_flag

    if hasattr(key, "char") and key.char == "=" and not playing:
        playing = True
        stop_flag = False
        threading.Thread(target=play_events, daemon=True).start()

    if key == keyboard.Key.esc and playing:
        stop_flag = True
        return False

print("🟡 대기중 : '=' → 재생 / ESC 중단")

with keyboard.Listener(on_press=on_press) as listener:
    listener.join()