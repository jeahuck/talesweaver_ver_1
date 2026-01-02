from pynput import keyboard, mouse
import json
import time
import os

# =========================
# 설정
# =========================
LOG_FILE = "events.json"
MAX_HISTORY = 10  # events1 ~ events10 까지 유지

# =========================
# 파일 적재(로테이션)
# =========================
def rotate_event_files(base="events.json", max_files=10):
    for i in range(max_files, 0, -1):
        src = base if i == 1 else f"events{i-1}.json"
        dst = f"events{i}.json"
        if os.path.exists(src):
            os.replace(src, dst)

# 🔥 녹화 시작 전 파일 적재
rotate_event_files(LOG_FILE, MAX_HISTORY)

# =========================
# 전역 상태
# =========================
events = []
recording = False
started = False
start_time = None

ms = mouse.Controller()

def now():
    return round(time.time() - start_time, 4)

# =========================
# 키보드 이벤트
# =========================
def on_press(key):
    global recording, started, start_time

    # ▶ 시작 키 '='
    if hasattr(key, "char") and key.char == "=" and not started:
        started = True
        print("⏳ 3초 후 녹화 시작")
        for i in range(3, 0, -1):
            print(f"  {i}...")
            time.sleep(1)

        start_time = time.time()
        recording = True
        print("🔴 녹화 시작")
        return

    # ■ 종료 키 ESC
    if key == keyboard.Key.esc and recording:
        print("🛑 녹화 종료")
        recording = False
        return False

    if not recording:
        return

    # 🔥 v 키 → 좌표 스냅샷 + 키 기록
    if hasattr(key, "char") and key.char == "v":
        x, y = ms.position
        t = now()

        events.append({
            "t": t,
            "type": "mouse_snap",
            "x": x,
            "y": y
        })

        events.append({
            "t": t,
            "type": "key_down",
            "key": str(key)
        })

        print(f"📍 v 눌림 → 좌표 저장 ({x}, {y})")
        return

    # 일반 키 기록
    events.append({
        "t": now(),
        "type": "key_down",
        "key": str(key)
    })

def on_release(key):
    if not recording:
        return

    events.append({
        "t": now(),
        "type": "key_up",
        "key": str(key)
    })

# =========================
# 실행
# =========================
print("🟡 대기중 : '=' → 녹화 시작 / v → 좌표 저장 / ESC 종료")

with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
    listener.join()

# =========================
# 저장
# =========================
with open(LOG_FILE, "w", encoding="utf-8") as f:
    json.dump(events, f, indent=2)

print(f"✅ 저장 완료 : {LOG_FILE}")
print(f"📦 총 이벤트 수 : {len(events)}")