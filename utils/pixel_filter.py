import numpy as np
import cv2

def pixel_filter(image):
    """image is a numpy array"""
    
    
    # 创建红色和绿色的掩码
    red_mask = (image[..., 0] == 0) & (image[..., 1] == 0) & (image[..., 2] == 255)
    green_mask = ((image[..., 0] == 0) & (image[..., 1] == 255) & (image[..., 2] == 0))
    
    image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    new_pixels = np.zeros(image.shape, dtype=np.uint8)

    new_pixels[(image == 0)] = 253 # 黑色点
    new_pixels[(image == 242)] = 251 # status 监测点
    new_pixels[green_mask] = 150
    green_flag = np.any(image == 150)
    
    return new_pixels, green_flag