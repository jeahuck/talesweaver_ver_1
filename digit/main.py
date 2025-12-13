import cv2
import numpy as np
import torch
from digit_cnn import DigitCNN


# ==============================
# CNN 모델 로드
# ==============================
model = DigitCNN()
model.load_state_dict(torch.load("digit_cnn.pth", map_location="cpu"))
model.eval()

# ==============================
# CNN 숫자 예측
# ==============================
def cnn_predict_digit(img):
    if len(img.shape) == 3:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)


    img = cv2.resize(img, (28, 28))
    img = img.astype(np.float32) / 255.0
    img = 1.0 - img # 흰 숫자 기준


    tensor = torch.from_numpy(img).unsqueeze(0).unsqueeze(0)


    with torch.no_grad():
        logits = model(tensor)
    prob = torch.softmax(logits, dim=1)
    conf, pred = torch.max(prob, 1)


    return int(pred.item()), float(conf.item())


# ==============================
# 숫자 색상 마스크
# ==============================
def extract_number_mask(img):
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    lower = np.array([0, 0, 180])
    upper = np.array([180, 40, 255])
    mask = cv2.inRange(hsv, lower, upper)
    mask = cv2.medianBlur(mask, 5)
    return mask

# ==============================
# 숫자 영역 탐지
# ==============================
def detect_number_regions(mask):
    regions = []
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)


    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        if w < 10 or h < 15:
            continue
        aspect = w / float(h)
        if aspect < 0.2 or aspect > 5:
            continue
        regions.append((x, y, w, h))


    regions.sort(key=lambda r: r[0])
    return regions

# ==============================
# 숫자 문자열 인식
# ==============================
def recognize_number_string(img, rect):
    x, y, w, h = rect
    crop = img[y:y+h, x:x+w]


    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    th = cv2.adaptiveThreshold(
        gray, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV,
        11, 2
    )


    proj = np.sum(th, axis=0)
    chars = []
    in_char = False
    start = 0


    for i, v in enumerate(proj):
        if v > 0 and not in_char:
            in_char = True
            start = i
        elif v == 0 and in_char:
            in_char = False
            chars.append((start, i))


    if in_char:
        chars.append((start, th.shape[1]))


    result = ""
    for s, e in chars:
        ch = th[:, s:e]
        rows = np.any(ch > 0, axis=1)
        if not rows.any():
            continue
    ch = ch[np.where(rows)[0][0]:np.where(rows)[0][-1] + 1]


    digit, conf = cnn_predict_digit(ch)
    result += str(digit) if conf > 0.7 else "?"


    return result


# ==============================
# 메인 실행
# ==============================
def detect_numbers_in_image(path):
    img = cv2.imread(path)
    mask = extract_number_mask(img)
    regions = detect_number_regions(mask)


    for rect in regions:
        num = recognize_number_string(img, rect)
        x, y, w, h = rect
        print(f"감지 숫자: {num} 위치=({x},{y},{w},{h})")


        cv2.rectangle(img, (x, y), (x+w, y+h), (0,255,0), 2)
        cv2.putText(img, num, (x, y-5), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,0), 2)


        cv2.imshow("result", img)
        cv2.waitKey(0)




if __name__ == '__main__':
    detect_numbers_in_image("../im/core/testImg.png")