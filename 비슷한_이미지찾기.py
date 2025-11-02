import cv2
import numpy as np
import pyautogui
import mss
import time

# 찾을 이미지 파일 경로
TARGET_IMAGE = "im/Abyss/btn1.png"

# 유사도 임계값 (0.8 이상이면 일치로 간주)
THRESHOLD = 0.8

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
def click_center(x, y, template):
    h, w = template.shape[:2]
    center_x = x + w // 2
    center_y = y + h // 2
    pyautogui.moveTo(center_x, center_y, duration=0.2)
    pyautogui.click()
    print(f"클릭 완료: ({center_x}, {center_y})")

# 4️⃣ 실행
if __name__ == "__main__":
    print("1초 후 화면 캡처 시작...")
    time.sleep(1)

    points, screen, template = find_image_on_screen(TARGET_IMAGE, THRESHOLD)

    if points:
        print(f"{len(points)}개의 일치 항목 발견")
        for pt in points:
            # 매칭된 영역 표시
            cv2.rectangle(screen, pt, (pt[0] + template.shape[1], pt[1] + template.shape[0]), (0, 255, 0), 2)
            click_center(pt[0], pt[1], template)
    else:
        print("일치하는 이미지가 없습니다.")

    cv2.imshow("Result", screen)
    cv2.waitKey(0)
    cv2.destroyAllWindows()