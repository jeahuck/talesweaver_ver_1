import win32gui
import win32con
import win32api
import time

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

def send_background_click(hwnd, client_x, client_y):
    # 클라이언트 좌표를 화면 좌표로 변환
    screen_x, screen_y = win32gui.ClientToScreen(hwnd, (client_x, client_y))

    # 화면 좌표에서 클릭 이벤트 발생 (마우스 이동 없이)
    #lparam = win32api.MAKELONG(client_x, client_y)

    VK_3 = 0x33  # '3' 키
    # PostMessage로 클릭 이벤트 보내기
    #win32gui.PostMessage(hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, lparam)
    win32api.PostMessage(hwnd, win32con.WM_KEYDOWN, VK_3, 0)
    time.sleep(0.05)
    #win32gui.PostMessage(hwnd, win32con.WM_LBUTTONUP, 0, lparam)
    win32api.PostMessage(hwnd, win32con.WM_KEYUP, VK_3, 0)
    print(f"✔ 클릭 완료 at ({client_x}, {client_y})")

def main():
    window_title_keyword = "Talesweaver Client Version 907.2 ,Release ,for Korea (DirectX9)"  # 원하는 창 이름 일부
    click_x, click_y = 356, 597     # 클릭할 좌표 (클라이언트 기준)

    hwnd = get_window_by_title(window_title_keyword)
    if hwnd:
        for i in range(1, 30000):
            time.sleep(0.1)
            send_background_click(hwnd, click_x, click_y)
    else:
        print("❌ 해당 창을 찾을 수 없습니다.")

if __name__ == "__main__":
    main()

# 클릭하고싶어

