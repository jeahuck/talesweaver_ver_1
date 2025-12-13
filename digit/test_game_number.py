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

def cnn_predict_digit(img):
    if len(img.shape) == 3:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    img = cv2.resize(img, (28, 28))
    img = img.astype(np.float32) / 255.0
    img = 1.0 - img  # 흰/밝은 숫자 기준

    tensor = torch.from_numpy(img).unsqueeze(0).unsqueeze(0)

    with torch.no_grad():
        out = model(tensor)
        prob = torch.softmax(out, dim=1)
        conf, pred = torch.max(prob, 1)

    return int(pred.item()), float(conf.item())


# ==============================
# 숫자 색상 마스크 (청록/하늘색 대응)
# ==============================
def extract_number_mask(img):
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    # 하늘색~청록색 숫자 범위
    lower = np.array([70, 40, 120])
    upper = np.array([130, 255, 255])

    mask = cv2.inRange(hsv, lower, upper)
    mask = cv2.medianBlur(mask, 5)
    return mask


# ==============================
# 숫자 인식
# ==============================
def recognize_numbers(img):
    mask = extract_number_mask(img)

    contours, _ = cv2.findContours(
        mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )

    digits = []

    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)

        if h < 15 or w < 5:
            continue

        aspect = w / float(h)
        if aspect < 0.2 or aspect > 1.2:
            continue

        digit_img = img[y:y+h, x:x+w]
        digit, conf = cnn_predict_digit(digit_img)

        if conf > 0.6:
            digits.append((x, digit, conf, (x, y, w, h)))

    # 왼쪽 → 오른쪽 정렬
    digits.sort(key=lambda x: x[0])

    number_str = "".join(str(d[1]) for d in digits)
    return number_str, digits


# ==============================
# 실행
# ==============================
if __name__ == "__main__":
    img = cv2.imread("../im/core/testImg.png") # ← 너가 올린 이미지 파일명
    number, digits = recognize_numbers(img)

    print("인식된 숫자:", number)

    for _, d, conf, (x, y, w, h) in digits:
        cv2.rectangle(img, (x, y), (x+w, y+h), (0, 255, 0), 1)
        cv2.putText(
            img,
            f"{d} {conf:.2f}",
            (x, y - 5),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (0, 255, 0),
            1
        )

    cv2.imwrite("result", img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
