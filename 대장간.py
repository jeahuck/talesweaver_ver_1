import cv2
import numpy as np
import mss
import time
import win32gui
import win32con
import win32api
import threading
from concurrent.futures import ThreadPoolExecutor
import ctypes
import win32print
from common.config import WINDOW_TITLE_KEYWORD
import json

# ==============================
# DPI 인식 설정
# ==============================
ctypes.windll.user32.SetProcessDPIAware()

# ==============================
# 설정
# ==============================
THRESHOLD = 0.95
VK_3 = 0x33
VK_2 = 0x32
VK_V = 0x56
VK_RETURN = 0x0D
VK_MENU = 0x12
VK_LEFT = 0x25
VK_F1 = 0x71
VK_F2 = 0x72
VK_F3 = 0x73
VK_F4 = 0x74
VK_F5 = 0x75

SKIP_CHK = False
lock = threading.Lock()

_last_click = {"pos": None, "time": 0.0}
CLICK_COOLDOWN = 0.5

LOG_FILE = "리체_대장간_이속99.json"
SPEED = 1

# ==============================
# DPI / 모니터
# ==============================
def get_dpi_scale():
    hdc = win32gui.GetDC(0)
    dpi = win32print.GetDeviceCaps(hdc, 88)
    win32gui.ReleaseDC(0, hdc)
    return dpi / 96.0


def get_monitors():
    monitors = win32api.EnumDisplayMonitors()
    info = []
    for m in monitors:
        mi = win32api.GetMonitorInfo(m[0])
        info.append(mi["Monitor"])
    return info


# ==============================
# 화면 캡처
# ==============================
def capture_monitor(monitor_rect):
    left, top, right, bottom = map(int, monitor_rect)
    width, height = right - left, bottom - top

    with mss.mss() as sct:
        img = np.array(
            sct.grab({"left": left, "top": top, "width": width, "height": height})
        )
        if img.shape[2] == 4:
            img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
    return img


# ==============================
# 템플릿 매칭
# ==============================
def match_task(task):
    screen = task["screen"]
    template = task["template"]
    mon = task["mon"]
    tpl_info = task["template_path_json"]

    gray_screen = cv2.cvtColor(screen, cv2.COLOR_BGR2GRAY)
    gray_template = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)

    if gray_template.shape[0] > gray_screen.shape[0]:
        return None

    res = cv2.matchTemplate(gray_screen, gray_template, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(res)

    if max_val >= THRESHOLD:
        return {
            "mon": mon,
            "max_loc": max_loc,
            "template": template,
            "callBackKey": tpl_info.get("callBackKey", ""),
            "score": max_val
        }
    return None


# ==============================
# 클릭 & 키
# ==============================
def click_client_coords(cx, cy, hwnd):
    lparam = win32api.MAKELONG(int(cx), int(cy))
    win32api.PostMessage(hwnd, win32con.WM_MOUSEMOVE, 0, lparam)
    time.sleep(0.02)
    win32gui.PostMessage(hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, lparam)
    time.sleep(0.05)
    win32gui.PostMessage(hwnd, win32con.WM_LBUTTONUP, 0, lparam)


def send_background_click(hwnd, vk_key):
    win32api.PostMessage(hwnd, win32con.WM_KEYDOWN, vk_key, 0)
    time.sleep(0.02)
    win32api.PostMessage(hwnd, win32con.WM_KEYUP, vk_key, 0)


# ==============================
# 윈도우 유틸
# ==============================
def get_window_by_title(partial_title):
    result = []

    def cb(hwnd, _):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            if partial_title.lower() in title.lower():
                result.append(hwnd)

    win32gui.EnumWindows(cb, None)
    return result[0] if result else None


def get_window_client_offset(hwnd):
    win_left, win_top, _, _ = win32gui.GetWindowRect(hwnd)
    client_left_top = win32gui.ClientToScreen(hwnd, (0, 0))

    offset_x = client_left_top[0] - win_left
    offset_y = client_left_top[1] - win_top
    return offset_x, offset_y


# ==============================
# worker_2
# ==============================
def worker_2():
    hwnd = get_window_by_title(WINDOW_TITLE_KEYWORD)
    if not hwnd:
        print("❌ 창을 찾을 수 없습니다.")
        return

    offset_x, offset_y = get_window_client_offset(hwnd)
    print(f"[OFFSET] x={offset_x}, y={offset_y}")

    with open(LOG_FILE, "r", encoding="utf-8") as f:
        events = json.load(f)

    while True:
        last_t = 0

        for e in events:
            delay = (e["t"] - last_t) * SPEED
            if delay > 0:
                time.sleep(delay)
            last_t = e["t"]

            t = e["type"]
            key = e.get("key", "")

            paramKey = 0
            if key == "'v'": paramKey = VK_V
            if key == "'3'": paramKey = VK_3

            if t == "mouse_snap":
                client_x, client_y = win32gui.ScreenToClient(
                    hwnd, (int(e["x"]), int(e["y"]))
                )

                client_x -= offset_x
                client_y -= offset_y

                lparam = win32api.MAKELONG(client_x, client_y)
                win32api.PostMessage(hwnd, win32con.WM_MOUSEMOVE, 0, lparam)

            elif t == "key_down":
                win32api.PostMessage(hwnd, win32con.WM_KEYDOWN, paramKey, 0)

            elif t == "key_up":
                win32api.PostMessage(hwnd, win32con.WM_KEYUP, paramKey, 0)

        # ===== 반복 후 =====
        click_client_coords(41, 900, hwnd)
        time.sleep(7)

        send_background_click(hwnd, VK_F1)
        time.sleep(0.1)
        send_background_click(hwnd, VK_F2)
        time.sleep(0.1)
        send_background_click(hwnd, VK_F3)
        time.sleep(0.1)
        send_background_click(hwnd, VK_F4)
        time.sleep(0.1)
        send_background_click(hwnd, VK_F5)
        time.sleep(0.1)

        click_client_coords(614, 310, hwnd)
        time.sleep(1)
        click_client_coords(996, 593, hwnd)
        time.sleep(8)


# ==============================
# main
# ==============================
def main():
    worker_2()


if __name__ == "__main__":
    main()