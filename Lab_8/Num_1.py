import cv2
import numpy as np


img = cv2.imread('variant-5.jpg')

def noise(img, n=0.5):
    backup = img.copy()
    h, w = backup.shape[:2]
    noise_pixels = int(h * w * n)
    
    for _ in range(noise_pixels):
        y = np.random.randint(0, h)
        x = np.random.randint(0, w)
        if np.random.random() < 0.5:
            backup[y, x] = 0 
        else:
            backup[y, x] = 255  
    
    return backup

img_noise = noise(img)
cv2.imshow("image", img_noise)


cv2.waitKey(0)
cv2.destroyAllWindows()

