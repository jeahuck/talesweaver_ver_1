import tkinter as tk
import subprocess
import sys
import os
import atexit
import signal

PYTHON = sys.executable
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

process_map = {}

def start_script(script):
    if script in process_map:
        return

    p = subprocess.Popen(
        [PYTHON, os.path.join(BASE_DIR, script)],
        creationflags=subprocess.CREATE_NO_WINDOW
    )
    process_map[script] = p

def stop_script(script):
    p = process_map.get(script)
    if not p:
        return

    if p.poll() is None:
        p.terminate()
    process_map.pop(script, None)

def toggle(var, script):
    if var.get():
        start_script(script)
    else:
        stop_script(script)

# 🔥 모든 종료 경로에서 호출
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
# GUI33
# =============================
root = tk.Tk()
root.title("체크 기반 PY 실행기")
root.geometry("300x300")
root.resizable(False, False)
root.attributes("-topmost", True)

jobs = [
    ("룬정원꽃 채집", "룬정원꽃채집.py"),
    ("어비스", "어비스.py"),
    ("림보", "림보.py"),
    ("대장간 미완성", "대장간.py"),
    ("룬던전", "룬던전2.py"),
    ("테시스코어", "테시스코어2.py"),
    ("필멸의땅", "필멸의땅.py"),
    ("3번키", "3번키.py"),
]

for text, script in jobs:
    var = tk.BooleanVar()
    tk.Checkbutton(
        root,
        text=text,
        variable=var,
        command=lambda v=var, s=script: toggle(v, s)
    ).pack(anchor="w", padx=20, pady=6)

root.protocol("WM_DELETE_WINDOW", on_close)
root.mainloop()