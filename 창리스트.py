import win32gui

def enum_windows():
    windows = []

    def callback(hwnd, _):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            if title:  # 제목이 있는 창만 필터링
                windows.append((hwnd, title))

    win32gui.EnumWindows(callback, None)
    return windows

# 테스트: 창 목록 출력
for hwnd, title in enum_windows():
    print(f"HWND: {hwnd}, TITLE: {title}")