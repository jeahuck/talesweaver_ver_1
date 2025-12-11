import asyncio
import base64
import json
import aiohttp
import pyautogui
import time
from mss import mss
from PIL import Image

# ----------------------------
# OCR 서버 호출 함수
# ----------------------------
async def run_powershell_ocr_from_image(image_path):
    """
    PowerToys OCR API에 이미지 전송 후 텍스트 반환
    """
    with open(image_path, "rb") as f:
        img_bytes = f.read()
    img_b64 = base64.b64encode(img_bytes).decode("utf-8")

    url = "http://localhost:5000/api/ocr"  # 서버 이미 켜진 상태 가정
    headers = {"Content-Type": "application/json"}
    data = {"base64Image": img_b64, "language": "ko"}

    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, data=json.dumps(data)) as resp:
            result = await resp.json()
            text = result.get("text", "")
            return text.strip()

# ----------------------------
# OCR 결과 기반 자동 클릭/처리
# ----------------------------
def handle_ocr_text(text):
    """
    OCR 결과를 기반으로 클릭/작업 처리
    """
    if "시작" in text:
        print("→ 시작 버튼 클릭")
        pyautogui.click(x=500, y=300)
    elif "종료" in text:
        print("→ 종료 버튼 클릭")
        pyautogui.click(x=600, y=400)
    else:
        print("→ 클릭 조건 없음")

# ----------------------------
# 화면 캡처 + OCR 반복
# ----------------------------
async def monitor_screen(region=None, interval=1.0):
    """
    region: {"top": int, "left": int, "width": int, "height": int}
    interval: OCR 반복 간격 (초)
    """
    with mss() as sct:
        while True:
            # 화면 캡처
            monitor = region if region else sct.monitors[1]  # 1번 모니터 전체
            sct_img = sct.grab(monitor)
            img = Image.frombytes("RGB", sct_img.size, sct_img.rgb)

            # 임시 파일로 저장
            tmp_path = "tmp_screen.png"
            img.save(tmp_path)

            # OCR 실행
            text = await run_powershell_ocr_from_image(tmp_path)
            print("🟢 OCR 결과:", text)

            # 결과 기반 처리
            handle_ocr_text(text)

            time.sleep(interval)

# ----------------------------
# 메인 실행
# ----------------------------
if __name__ == "__main__":
    # 원하는 화면 영역 지정 (예: 게임 UI 일부)
    region = {"top": 100, "left": 100, "width": 500, "height": 300}

    # 반복 OCR + 자동 처리 실행
    asyncio.run(monitor_screen(region=region, interval=1.0))