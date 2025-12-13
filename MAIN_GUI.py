import tkinter as tk
import subprocess
import sys
import os

PYTHON = sys.executable
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 실행중인 프로세스 관리
process_map = {}  # {script: Popen}

def start_script(script):
    if script in process_map:
        return  # 이미 실행중

    p = subprocess.Popen(
        [PYTHON, os.path.join(BASE_DIR, script)],
        creationflags=subprocess.CREATE_NO_WINDOW  # 콘솔 숨김 (윈도우)
    )
    process_map[script] = p
    print(f"{script} 시작")

def stop_script(script):
    p = process_map.get(script)
    if not p:
        return

    if p.poll() is None:
        p.terminate()
    process_map.pop(script, None)
    print(f"{script} 종료")

def toggle(var, script):
    if var.get():
        start_script(script)
    else:
        stop_script(script)

# =============================
# GUI
# =============================
root = tk.Tk()
root.title("체크 기반 PY 실행기")
root.geometry("320x200")

jobs = [
    ("룬정원꽃 채집", "룬정원꽃채집.py"),
    ("어비스", "job_b.py"),
    ("림보", "job_c.py"),
    ("대장간 미완성", "job_c.py"),
    ("룬던전", "job_c.py"),
]

vars = {}

for text, script in jobs:
    v = tk.BooleanVar()
    vars[script] = v

    tk.Checkbutton(
        root,
        text=text,
        variable=v,
        command=lambda v=v, s=script: toggle(v, s)
    ).pack(anchor="w", padx=20, pady=5)

root.mainloop()