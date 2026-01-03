import win32gui
import win32con
import win32api
import time
from common.config import WINDOW_TITLE_KEYWORD

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

def screen_to_client(hwnd, x, y):
    """화면 좌표를 클라이언트 좌표로 변환"""
    return win32gui.ScreenToClient(hwnd, (x, y))

def get_mouse_position():
    """현재 마우스 위치 (스크린 좌표)"""
    return win32api.GetCursorPos()

def main():
    window_title = WINDOW_TITLE_KEYWORD  # 원하는 창 이름 일부
    hwnd = get_window_by_title(window_title)

    if not hwnd:
        print("❌ 창을 찾을 수 없습니다.")
        return

    print("🖱 마우스를 원하는 위치에 두세요. 3초 후 좌표를 측정합니다...")
    time.sleep(3)

    x, y = get_mouse_position()
    client_x, client_y = screen_to_client(hwnd, x, y)

    print(f"📌 마우스 위치 (화면 기준): ({x}, {y})")
    print(f"📌 마우스 위치 (창 클라이언트 기준): ({client_x}, {client_y})")

if __name__ == "__main__":
    main()