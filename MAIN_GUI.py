import tkinter as tk
import subprocess
import sys
import os
import atexit
import signal
import keyboard

PYTHON = sys.executable
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

process_map = {}
var_map = {}

def start_script(script):
    if script in process_map:
        return

    p = subprocess.Popen(
        [PYTHON, os.path.join(BASE_DIR, script)],
        creationflags=subprocess.CREATE_NO_WINDOW
    )
    process_map[script] = p
    print(f"START: {script}")

def stop_script(script):
    p = process_map.get(script)
    if not p:
        return

    if p.poll() is None:
        p.terminate()
    process_map.pop(script, None)
    print(f"STOP: {script}")

def toggle(var, script):
    if var.get():
        start_script(script)
    else:
        stop_script(script)

# 🔥 전역 NumPad 토글
def hotkey_toggle(script):
    var = var_map[script]
    var.set(not var.get())
    toggle(var, script)

# 🔥 전체 종료 처리
def kill_all_processes():
    for p in process_map.values():
        if p.poll() is None:
            try:
                p.terminate()
                p.wait(timeout=2)
            except:
                p.kill()
    process_map.clear()

def on_close():
    kill_all_processes()
    root.destroy()

def handle_signal(sig, frame):
    kill_all_processes()
    sys.exit(0)

atexit.register(kill_all_processes)
signal.signal(signal.SIGINT, handle_signal)
signal.signal(signal.SIGTERM, handle_signal)

# =============================
# GUI
# =============================
root = tk.Tk()
root.title("NumPad 전용 PY 실행기")
root.geometry("300x400")
root.resizable(False, False)
root.attributes("-topmost", True)

jobs = [
    ("룬정원꽃 채집", "룬정원꽃채집.py"),
    ("어비스", "어비스.py"),
    ("대장간 미완성", "대장간.py"),
    ("룬던전", "룬던전2.py"),
    ("테시스코어", "테시스코어2.py"),
    ("3번키", "3번키.py"),
    ("F3난사", "F3난사.py"),
    ("sp물약자동", "sp물약자동.py"),
    ("A와 S난사", "A와 S난사.py"),
]

# 체크박스 생성
for text, script in jobs:
    var = tk.BooleanVar()
    var_map[script] = var

    tk.Checkbutton(
        root,
        text=text,
        variable=var,
        command=lambda v=var, s=script: toggle(v, s)
    ).pack(anchor="w", padx=20, pady=6)

# =============================
# 🔥 NumPad 스캔코드 매핑
# (상단 숫자 절대 반응 안함)
# =============================
NUMPAD_SCAN = {
    79: jobs[0][1],  # numpad 1
    80: jobs[1][1],  # numpad 2
    81: jobs[2][1],  # numpad 3
    75: jobs[3][1],  # numpad 4
    76: jobs[4][1],  # numpad 5
    77: jobs[5][1],  # numpad 6
    71: jobs[6][1],  # numpad 7
    72: jobs[7][1],  # numpad 8
    73: jobs[8][1],  # numpad 9
}

for scan_code, script in NUMPAD_SCAN.items():
    keyboard.add_hotkey(scan_code, lambda s=script: hotkey_toggle(s))

print("NumPad 전용 전역 핫키 활성화 완료")

root.protocol("WM_DELETE_WINDOW", on_close)
root.mainloop()