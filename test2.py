import win32gui
import win32con
import win32api
import time


def get_window_by_title(partial_title):
    def cb(hwnd, result):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd) or ""
            if partial_title.lower() in title.lower():
                result.append(hwnd)
                win32gui.SetWindowText(hwnd, 'Talesweaver Client Version 907.3 ,Release ,for Korea (DirectX9)')
                print('?')
    result = []
    win32gui.EnumWindows(cb, result)


if __name__ == "__main__":
    get_window_by_title('123')