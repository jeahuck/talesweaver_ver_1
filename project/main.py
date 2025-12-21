import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Conv2D, MaxPooling2D, Flatten, Dense
from tensorflow.keras.preprocessing.image import ImageDataGenerator
import json
# =========================
# 설정
# =========================
IMG_SIZE = (28, 28)
BATCH_SIZE = 8
EPOCHS = 10
DATA_DIR = "dataset/train"

# =========================
# 데이터 제너레이터 (자동 분할)
# =========================
datagen = ImageDataGenerator(
    rescale=1.0 / 255,
    validation_split=0.2   # ⭐ 80% train / 20% val
)

train_gen = datagen.flow_from_directory(
    DATA_DIR,
    target_size=IMG_SIZE,
    color_mode="grayscale",
    batch_size=BATCH_SIZE,
    class_mode="categorical",
    subset="training",
    shuffle=True
)

val_gen = datagen.flow_from_directory(
    DATA_DIR,
    target_size=IMG_SIZE,
    color_mode="grayscale",
    batch_size=BATCH_SIZE,
    class_mode="categorical",
    subset="validation",
    shuffle=False
)

print("클래스 매핑:", train_gen.class_indices)
print("Train samples:", train_gen.samples)
print("Val samples:", val_gen.samples)

# =========================
# 모델 정의
# =========================
model = Sequential([
    Conv2D(16, (3,3), activation="relu", input_shape=(28,28,1)),
    MaxPooling2D(2,2),
    Conv2D(32, (3,3), activation="relu"),
    MaxPooling2D(2,2),
    Flatten(),
    Dense(64, activation="relu"),
    Dense(train_gen.num_classes, activation="softmax")
])

model.compile(
    optimizer="adam",
    loss="categorical_crossentropy",
    metrics=["accuracy"]
)

# =========================
# 학습
# =========================
model.fit(
    train_gen,
    validation_data=val_gen,
    epochs=EPOCHS
)

# =========================
# 모델 저장
# =========================
model.save("digit_model.h5")
print("✅ 모델 저장 완료")

with open("class_indices.json", "w", encoding="utf-8") as f:
    json.dump(train_gen.class_indices, f)