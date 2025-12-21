import cv2
import numpy as np
import tensorflow as tf
import json

# =========================
# 모델 & 클래스 매핑 로드
# =========================
model = tf.keras.models.load_model("digit_model.h5")

with open("class_indices.json", "r", encoding="utf-8") as f:
    class_indices = json.load(f)

idx_to_label = {int(v): k for k, v in class_indices.items()}

# =========================
# 숫자 분리 + 인식
# =========================
def recognize_digits(image_path):
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError("이미지를 불러올 수 없습니다")

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # 1️⃣ 이진화 (숫자 = 흰색)
    _, th = cv2.threshold(
        gray, 0, 255,
        cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU
    )

    # 2️⃣ 윤곽선 검출
    contours, _ = cv2.findContours(
        th, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )

    # 3️⃣ 바운딩 박스 정렬 (좌 → 우)
    boxes = sorted(
        [cv2.boundingRect(c) for c in contours],
        key=lambda x: x[0]
    )

    results = []

    for x, y, w, h in boxes:
        # 노이즈 제거
        if h < 15 or w < 5:
            continue

        # 4️⃣ 숫자 ROI
        roi = gray[y:y+h, x:x+w]

        # 정사각형 패딩 (비율 유지)
        size = max(w, h)
        padded = np.zeros((size, size), dtype=np.uint8)
        padded[
        (size-h)//2:(size-h)//2+h,
        (size-w)//2:(size-w)//2+w
        ] = roi

        # 5️⃣ 학습과 동일한 전처리
        digit_img = cv2.resize(padded, (28, 28))
        digit_img = digit_img / 255.0
        digit_img = digit_img.reshape(1, 28, 28, 1)

        # 6️⃣ 예측
        pred = model.predict(digit_img, verbose=0)
        results.append(idx_to_label[np.argmax(pred)])

    return "".join(results)

# =========================
# 실행
# =========================
result = recognize_digits("test2.png")
print("인식된 숫자:", result)