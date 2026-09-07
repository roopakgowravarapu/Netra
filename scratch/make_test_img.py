import cv2
import numpy as np
from pathlib import Path

out_path = Path(r"c:\Users\roopa\Downloads\Netra\scratch\test_fundus.jpg")
out_path.parent.mkdir(parents=True, exist_ok=True)

img = np.zeros((300, 300, 3), dtype=np.uint8)
cv2.circle(img, (150, 150), 120, (30, 70, 200), -1)
cv2.circle(img, (150, 150), 90, (15, 45, 140), 2)
cv2.circle(img, (150, 150), 60, (10, 30, 110), 2)
cv2.line(img, (50, 150), (250, 150), (10, 200, 220), 2)
cv2.line(img, (150, 50), (150, 250), (10, 180, 200), 2)

cv2.imwrite(str(out_path), img)
print("Test fundus image created at", out_path)
