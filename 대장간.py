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

# DPI 인식 설정
ctypes.windll.user32.SetProcessDPIAware()

# ==============================
# 설정
# ==============================
THRESHOLD = 0.95   # 템플릿 매칭 유사도 기준
VK_3 = 0x33         # '3' 키
VK_2 = 0x32         # '2' 키
VK_V = 0x56         # v
VK_RETURN = 0x0D    # 엔터 키
VK_MENU = 0x12     #Alt
VK_LBUTTONDOWN = 0x01 #마우스 오른쪽
VK_LEFT = 0x25 # 왼쪽키
SKIP_CHK = False
lock = threading.Lock()

# 마지막 클릭 기록 (중복 클릭 방지)
_last_click = {"pos": None, "time": 0.0}
CLICK_COOLDOWN = 0.5  # 초


VK_F1 = 0x70
VK_F2 = 0x71
VK_F3 = 0x72
VK_F4 = 0x73
VK_F5 = 0x74
VK_F6 = 0x75
# ==============================
# 유틸: DPI / 모니터
# ==============================
def get_dpi_scale():
    hdc = win32gui.GetDC(0)
    dpi = win32print.GetDeviceCaps(hdc, 88)  # LOGPIXELSX
    win32gui.ReleaseDC(0, hdc)
    return dpi / 96.0


def get_monitors():
    monitors = win32api.EnumDisplayMonitors()
    info = []
    for m in monitors:
        mi = win32api.GetMonitorInfo(m[0])
        info.append(mi["Monitor"])  # (left, top, right, bottom)
    return info


# ==============================
# 화면 캡처 (모니터 영역)
# ==============================
def capture_monitor(monitor_rect):
    left, top, right, bottom = map(int, monitor_rect)
    width, height = right - left, bottom - top
    if width <= 0 or height <= 0:
        raise ValueError(f"Invalid monitor rect: {monitor_rect}")
    with mss.mss() as sct:
        sct_img = sct.grab({"left": left, "top": top, "width": width, "height": height})
        img = np.array(sct_img)
        if img.ndim == 3 and img.shape[2] == 4:
            img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
    return img


# ==============================
# 템플릿 매칭 작업 (작업 단위: 이미 캡처된 screen + template + mon_rect + template_path_json)
# ==============================
def match_task(task):
    """
    task = {
        'screen': <ndarray BGR>,
        'template': <ndarray BGR>,
        'mon': (left, top, right, bottom),
        'template_path_json': {...}
    }
    """
    screen = task['screen']
    template = task['template']
    mon = task['mon']
    tpl_info = task['template_path_json']

    # 안전 체크
    if screen is None or template is None:
        return None

    # 그레이 변환
    gray_screen = cv2.cvtColor(screen, cv2.COLOR_BGR2GRAY)
    gray_template = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)

    # 템플릿이 더 크면 실패
    if gray_template.shape[0] > gray_screen.shape[0] or gray_template.shape[1] > gray_screen.shape[1]:
        return None

    res = cv2.matchTemplate(gray_screen, gray_template, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(res)

    if max_val >= THRESHOLD:
        return {
            "mon": mon,
            "max_loc": max_loc,
            "template": template,
            "callBackKey": tpl_info.get('callBackKey', ''),
            "score": max_val
        }
    return None


# ==============================
# 클릭 & 키 이벤트
# ==============================
def click_client_coords(cx, cy, hwnd):
    lparam = win32api.MAKELONG(int(cx), int(cy))
    win32api.PostMessage(hwnd, win32con.WM_MOUSEMOVE, 0, lparam)
    time.sleep(0.02)
    win32gui.PostMessage(hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, lparam)
    time.sleep(0.02)  # 최소 50~100ms 권장
    win32gui.PostMessage(hwnd, win32con.WM_LBUTTONUP, 0, lparam)


def send_background_click(hwnd, vk_key):
    win32api.PostMessage(hwnd, win32con.WM_KEYDOWN, vk_key, 0)
    time.sleep(0.02)
    win32api.PostMessage(hwnd, win32con.WM_KEYUP, vk_key, 0)




# ==============================
# 창 찾기 유틸
# ==============================
def get_window_by_title(partial_title):
    def cb(hwnd, result):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd) or ""
            if partial_title.lower() in title.lower():
                result.append(hwnd)

    result = []
    win32gui.EnumWindows(cb, result)
    return result[0] if result else None


# ==============================
# 핵심: 한 번 캡처하고 모든 템플릿 검사 (모니터별)
# ==============================
def select_img(fileList, hwnd, win_left, win_top):
    """
    - fileList: [{'imgName':..., 'callBackKey': ...}, ...]
    - hwnd: target window handle
    - win_left, win_top: window rect's left/top (screen coords, 논리 좌표)
    """
    global _last_click
    scale = get_dpi_scale()
    monitors = get_monitors()
    tasks = []

    # --- 1) 각 모니터를 한 번만 캡처하고, 그 스크린으로 모든 템플릿 태스크 생성
    for mon in monitors:
        try:
            screen = capture_monitor(mon)
        except Exception as e:
            print(f"[WARN] capture monitor {mon} failed:", e)
            continue

        for tpl in fileList:
            template = cv2.imread(tpl['imgName'], cv2.IMREAD_COLOR)
            if template is None:
                print(f"[WARN] template load fail: {tpl['imgName']}")
                continue
            tasks.append({
                "screen": screen,
                "template": template,
                "mon": mon,
                "template_path_json": tpl
            })

    if not tasks:
        return False

    # --- 2) 병렬로 매칭 수행 (캡처는 이미 끝난 상태)
    results = []
    # max_workers = min(1, len(tasks))
    max_workers = 12
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futures = [ex.submit(match_task, t) for t in tasks]
        for fut in futures:
            r = fut.result()
            if r:
                results.append(r)

    if not results:
        return False

    # --- 3) 결과 중 가장 높은 score 우선 처리
    results.sort(key=lambda x: x['score'], reverse=True)
    best = results[0]

    mon = best['mon']
    max_loc = best['max_loc']
    template = best['template']
    callBackKey = best['callBackKey']
    h, w = template.shape[:2]
    x, y = max_loc

    # 화면(스크린 전체) 좌표(픽셀)
    screen_x = mon[0] + x + w // 2
    screen_y = mon[1] + y + h // 2

    # 스케일 보정된 윈도우 내부 좌표로 변환: ScreenToClient 사용 (더 정확)
    client_point = win32gui.ScreenToClient(hwnd, (int(screen_x), int(screen_y)))
    client_x, client_y = client_point[0], client_point[1]

    # 중복 클릭/쿨다운 검사
    now = time.time()
    pos = (int(client_x), int(client_y))
    if _last_click["pos"] == pos and (now - _last_click["time"]) < CLICK_COOLDOWN:
        # 이미 최근에 클릭한 위치이면 무시
        return False

    # 클릭
    print(f"Found match score={best['score']:.3f} screen=({screen_x},{screen_y}) client=({client_x},{client_y})")
    click_client_coords(client_x, client_y, hwnd)
    _last_click["pos"] = pos
    _last_click["time"] = now

    # 콜백키가 있으면 전송
    if callBackKey:
        time.sleep(0.5)
        send_background_click(hwnd, callBackKey)

    # 클릭 후 짧은 여유
    time.sleep(0.2)
    return True


# ==============================
# 스레드들
# ==============================
def worker_1():
    window_title_keyword = WINDOW_TITLE_KEYWORD
    hwnd = get_window_by_title(window_title_keyword)
    if not hwnd:
        print("❌ 해당 창을 찾을 수 없습니다.")
        return

    while True:
        # global SKIP_CHK
        # if SKIP_CHK:
        #     send_background_click(hwnd, VK_3)
        #     time.sleep(0.2)
        # else:
        #     time.sleep(0.5)
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
        send_background_click(hwnd, VK_F6)
        time.sleep(0.1)

        time.sleep(5)


LOG_FILE = "리체_대장간_이속99.json"
SPEED = 1

def worker_2():
    window_title_keyword = WINDOW_TITLE_KEYWORD
    hwnd = get_window_by_title(window_title_keyword)
    if not hwnd:
        print("❌ 해당 창을 찾을 수 없습니다.")
        return

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

            paramKey = ""
            key = e.get("key")
            if key is None: key = ""

            if key == "'v'" : paramKey = VK_V
            if key == "'3'" : paramKey = VK_3
            # if t == "mouse_snap":
            #     clinet_x_my = 0
            #     clinet_y_my = 0
            #
            #     # 스케일 보정된 윈도우 내부 좌표로 변환: ScreenToClient 사용 (더 정확)
            #     client_point = win32gui.ScreenToClient(hwnd, (int(e["x"],), int(e["y"])))
            #
            #     if client_point[0] == int(e["x"]): clinet_x_my = 320
            #     if client_point[1] == int(e["y"]): clinet_y_my = 167
            #
            #     client_x, client_y = client_point[0] - clinet_x_my, client_point[1] - clinet_y_my
            #     lparam = win32api.MAKELONG(int(client_x), int(client_y))
            #
            #     win32api.PostMessage(hwnd, win32con.WM_MOUSEMOVE, 0, lparam)
            #     #print(client_x, client_y)

            if t == "key_down":
                win32api.PostMessage(hwnd, win32con.WM_KEYDOWN, paramKey, 0)

            elif t == "key_up":
                win32api.PostMessage(hwnd, win32con.WM_KEYUP, paramKey, 0)
            elif t == "mouse_click":
                 # Screen → Client 좌표 변환
                client_point = win32gui.ScreenToClient(hwnd, (int(e["x"]), int(e["y"])))

                clinet_x_my = 0
                clinet_y_my = 0

                # 기존 보정 로직 유지
                if client_point[0] == int(e["x"]): clinet_x_my = 320
                if client_point[1] == int(e["y"]): clinet_y_my = 167

                client_x = client_point[0] - clinet_x_my
                client_y = client_point[1] - clinet_y_my

                if e["pressed"]:
                    click_client_coords(client_x, client_y, hwnd)
                else:
                    click_client_coords(client_x, client_y, hwnd)
        #대장간 끝나고 나서 다시 실행
        click_client_coords(41, 900, hwnd)
        time.sleep(9)
        click_client_coords(614, 310, hwnd)
        time.sleep(1)
        click_client_coords(996, 593, hwnd)
        time.sleep(8)



# ==============================
# 메인
# ==============================
def main():
    t1 = threading.Thread(target=worker_1, daemon=True)
    t1.start()
    worker_2()  # 메인 스레드에서 실행

if __name__ == "__main__":
    main()