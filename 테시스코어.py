import cv2
import numpy as np
import mss
import time
import win32gui
import win32con
import win32api
import threading
from concurrent.futures import ThreadPoolExecutor

# 유사도 임계값 (0.8 이상이면 일치로 간주)
THRESHOLD = 0.95
VK_3 = 0x33  # '3' 키
VK_RETURN = 0x0D # 엔터
SKIP_CHK = False
lock = threading.Lock()

# 1️⃣ 화면 캡처 함수 (빠르고 안정적)
def capture_screen():
    with mss.mss() as sct:
        monitor = sct.monitors[1]  # 첫 번째 모니터
        screenshot = sct.grab(monitor)
        img = np.array(screenshot)
        img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
        return img

# 2️⃣ 이미지 찾기 함수
def find_image_on_screen(template_path, threshold=0.8):
    screen = capture_screen()
    template = cv2.imread(template_path, cv2.IMREAD_COLOR)

    result = cv2.matchTemplate(screen, template, cv2.TM_CCOEFF_NORMED)
    loc = np.where(result >= threshold)

    points = list(zip(*loc[::-1]))  # (x, y) 좌표 리스트
    return points, screen, template

# 3️⃣ 클릭 함수
def click_center(client_x, client_y, hwnd):
    lparam = win32api.MAKELONG(client_x, client_y)
    win32gui.PostMessage(hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, lparam)
    time.sleep(0.05)
    win32gui.PostMessage(hwnd, win32con.WM_LBUTTONUP, 0, lparam)

#부분 창 제목으로 창 핸들 찾기
def get_window_by_title(partial_title):
    """부분 창 제목으로 창 핸들 찾기"""
    def callback(hwnd, result):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)

            if partial_title.lower() in title.lower():
                result.append(hwnd)
    result = []
    win32gui.EnumWindows(callback, result)
    return result[0] if result else None

def send_background_click(hwnd, vk_key):
    # 클라이언트 좌표를 화면 좌표로 변환
    #screen_x, screen_y = win32gui.ClientToScreen(hwnd, (client_x, client_y))
    # 화면 좌표에서 클릭 이벤트 발생 (마우스 이동 없이)
    #lparam = win32api.MAKELONG(client_x, client_y)
    win32api.PostMessage(hwnd, win32con.WM_KEYDOWN, vk_key, 0)
    time.sleep(0.05)
    win32api.PostMessage(hwnd, win32con.WM_KEYUP, vk_key, 0)

# 1️⃣ 창의 위치와 크기 가져오기
def win_send_xy(hwnd):
    return win32gui.GetWindowRect(hwnd)

#이미지 서치
def select_img(TARGET_IMAGE, hwnd, win_left, win_top):
    # global SKIP_CHK
    # with lock: SKIP_CHK = True  # 안전하게 전역 변수 수정

    returnChk = False
    points, screen, template = find_image_on_screen(TARGET_IMAGE, THRESHOLD)
    if points:
        print(f"{len(points)}개의 일치 항목 발견")
        for pt in points:
            h, w = template.shape[:2]
            screen_x = pt[0] + w // 2
            screen_y = pt[1] + h // 2
            inner_x = screen_x - win_left
            inner_y = screen_y - win_top - 45
            # print(f"screen_y 좌표: ({screen_x}, {screen_y})")
            # print(f"wind 좌표: ({win_left}, {win_top})")
            # print(f"창 내부 좌표: ({inner_x}, {inner_y})")

            # 매칭된 영역 표시
            cv2.rectangle(screen, pt, (pt[0] + template.shape[1], pt[1] + template.shape[0]), (0, 255, 0), 2)
            click_center(inner_x, inner_y, hwnd)
            time.sleep(0.5)
            send_background_click(hwnd, VK_3)
            break
        returnChk = True

    # if returnChk:
    #     lock.acquire()
    #     try:
    #         global SKIP_CHK
    #         SKIP_CHK = False
    #
    #         time.sleep(1)
    #     finally:
    #         lock.release()
    return returnChk


def worker_1(test):
    print(test)
    window_title_keyword = "Talesweaver Client Version 907.2 ,Release ,for Korea (DirectX9)"  # 원하는 창 이름 일부
    hwnd = get_window_by_title(window_title_keyword)
    if hwnd:
        for i in range(1, 30000000):
            global SKIP_CHK
            print(SKIP_CHK)
            if SKIP_CHK :
                time.sleep(0.1)
                send_background_click(hwnd, VK_3)
            else :
                time.sleep(0.1)

    else:
        print("❌ 해당 창을 찾을 수 없습니다.")

def worker_2(name):
    print(name)
    window_title_keyword = "Talesweaver Client Version 907.2 ,Release ,for Korea (DirectX9)"  # 원하는 창 이름 일부
    #time.sleep(0.3)
    hwnd = get_window_by_title(window_title_keyword)
    if hwnd:
        for i in range(1, 30000000):

            win_left, win_top, win_right, win_bottom  = win_send_xy(hwnd)
            select_img('im/core/skii1.png', hwnd, win_left, win_top)
            select_img('im/core/skii2.png', hwnd, win_left, win_top)
            select_img('im/core/skii3.png', hwnd, win_left, win_top)
            select_img('im/core/skii4.png', hwnd, win_left, win_top)
            select_img('im/core/skii5.png', hwnd, win_left, win_top)


    else:
        print("❌ 해당 창을 찾을 수 없습니다.")

#t1 = threading.Thread(target=worker_1,  args=("쓰레드1",))
t2 = threading.Thread(target=worker_2,  args=("쓰레드2",))
def main():
    #t1.start()
    t2.start()





if __name__ == "__main__":
    main()