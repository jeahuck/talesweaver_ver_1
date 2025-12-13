import os
import cv2
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
import numpy as np
import random

# ==============================
# Dataset
# ==============================
class DigitDataset(Dataset):
    def __init__(self, root):
        self.samples = []
        for label in range(10):
            folder = os.path.join(root, str(label))
            for f in os.listdir(folder):
                self.samples.append((os.path.join(folder, f), label))

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        path, label = self.samples[idx]
        img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
        img = cv2.resize(img, (28, 28))
        img = img.astype(np.float32) / 255.0
        img = 1.0 - img  # 흰 숫자 기준
        img = torch.tensor(img).unsqueeze(0)
        return img, label

# ==============================
# Model
# ==============================
class DigitCNN(nn.Module):
    def __init__(self):
        super().__init__()
        self.net = nn.Sequential(
            nn.Conv2d(1, 32, 3, 1, 1),
            nn.ReLU(),
            nn.MaxPool2d(2),

            nn.Conv2d(32, 64, 3, 1, 1),
            nn.ReLU(),
            nn.MaxPool2d(2),

            nn.Flatten(),
            nn.Linear(64 * 7 * 7, 128),
            nn.ReLU(),
            nn.Linear(128, 10)
        )

    def forward(self, x):
        return self.net(x)

# ==============================
# Train
# ==============================
device = "cuda" if torch.cuda.is_available() else "cpu"

model = DigitCNN().to(device)
criterion = nn.CrossEntropyLoss()
optimizer = torch.optim.Adam(model.parameters(), lr=0.001)

dataset = DigitDataset("../dataset")
loader = DataLoader(dataset, batch_size=64, shuffle=True)

for epoch in range(10):
    total = 0
    correct = 0
    loss_sum = 0

    for imgs, labels in loader:
        imgs = imgs.to(device)
        labels = labels.to(device)

        optimizer.zero_grad()
        out = model(imgs)
        loss = criterion(out, labels)
        loss.backward()
        optimizer.step()

        loss_sum += loss.item()
        _, pred = torch.max(out, 1)
        correct += (pred == labels).sum().item()
        total += labels.size(0)

    acc = correct / total * 100
    #print(f\"Epoch {epoch+1} | Loss {loss_sum:.4f} | Acc {acc:.2f}%\")
    print(f"Epoch {epoch+1} | Loss {loss_sum:.4f} | Acc {acc:.2f}%")
    # ==============================
    # Save
    # ==============================
    torch.save(model.state_dict(), "digit_cnn.pth")
    print("digit_cnn.pth 저장 완료")