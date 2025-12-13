import cv2
import numpy as np
import os

def load_templates(folder="digits"):
    templates = {}
    for filename in os.listdir(folder):
        if filename.endswith(".png"):
            key = filename.split(".")[0]   # 0,1,2,3… 이런 식
            img = cv2.imread(os.path.join(folder, filename), cv2.IMREAD_GRAYSCALE)
            templates[key] = img
    return templates

def extract_number_mask(img):
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    # 흰색 범위 (숫자 UI가 보통 이 영역)
    lower = np.array([0, 0, 180])
    upper = np.array([180, 40, 255])

    mask = cv2.inRange(hsv, lower, upper)

    # 노이즈 제거
    mask = cv2.medianBlur(mask, 5)
    return mask

def detect_number_regions(mask):
    num_regions = []

    # 윤곽 탐지 (connected component 대신 더 안정적)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)

        # 너무 작거나 큰 영역 제외
        if w < 10 or h < 10:
            continue
        if w > 500 or h > 200:
            continue

        num_regions.append((x, y, w, h))

    # 왼쪽 → 오른쪽 정렬
    num_regions.sort(key=lambda t: t[0])

    return num_regions

def recognize_from_regions(img, regions, templates):
    results = []

    for (x, y, w, h) in regions:
        crop = img[y:y+h, x:x+w]
        number = recognize_numbers_from_image(crop, templates)
        results.append((number, (x,y,w,h)))

    return results

def recognize_numbers_from_image(crop_bgr, templates):
    """
    임시/예시 OCR: 그레이스케일 후 이진화 -> 템플릿 매칭 방식으로 가장 높은 점수 텍스트 조합
    (실 사용시 이전에 만든 더 견고한 recognize_numbers_from_image 함수로 교체하세요)
    """
    import cv2
    gray = cv2.cvtColor(crop_bgr, cv2.COLOR_BGR2GRAY)
    _, th = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)  # 글자 흑색(255->배경)로 가정
    # 수직 투영으로 글자 구간 분할
    proj = np.sum(th, axis=0)
    chars = []
    in_char = False
    start = 0
    for x in range(len(proj)):
        if proj[x] > 0 and not in_char:
            in_char = True; start = x
        elif proj[x] == 0 and in_char:
            in_char = False; chars.append((start, x))
    if in_char:
        chars.append((start, th.shape[1]))

    result = ""
    # 간단 매칭: 각 문자에 대해 모든 템플릿과 matchTemplate 비교
    for (s, e) in chars:
        crop_char = th[:, s:e]
        # 상하 트리밍
        rows = np.any(crop_char > 0, axis=1)
        if rows.any():
            crop_char = crop_char[np.where(rows)[0][0]:np.where(rows)[0][-1]+1,:]
        best_k = None; best_score = -1
        for k, tmpl in templates.items():
            if tmpl is None or tmpl.size == 0: continue
            try:
                ct = cv2.resize(crop_char, (tmpl.shape[1], tmpl.shape[0]))
            except Exception:
                continue
            res = cv2.matchTemplate(ct, tmpl, cv2.TM_CCOEFF_NORMED)
            score = res[0][0] if res.size>0 else -1
            if score > best_score:
                best_score = score; best_k = k
        if best_k is None:
            result += "?"
        else:
            result += best_k
    return result


def detect_numbers_in_game_screen(screen_path, templates):
    img = cv2.imread(screen_path)

    # 1) 숫자 색상 기반 마스크 생성
    mask = extract_number_mask(img)

    # 2) 숫자 영역 자동 탐색
    regions = detect_number_regions(mask)

    # 3) 각 영역 숫자 인식
    results = recognize_from_regions(img, regions, templates)

    return results

templates = load_templates("im/digits")
results = detect_numbers_in_game_screen("im/core/testImg.png", templates)
for number, (x,y,w,h) in results:
    print(f"감지된 숫자: {number}  위치: ({x},{y},{w},{h})")