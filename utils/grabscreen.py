import cv2
import numpy as np
import win32gui, win32ui, win32con, win32api


def grab_screen(region=None):

    hwin = win32gui.GetDesktopWindow()

    if region:
            left, top, x2, y2 = region
            width = x2 - left + 1
            height = y2 - top + 1
    else:
        width = win32api.GetSystemMetrics(win32con.SM_CXVIRTUALSCREEN)
        height = win32api.GetSystemMetrics(win32con.SM_CYVIRTUALSCREEN)
        left = win32api.GetSystemMetrics(win32con.SM_XVIRTUALSCREEN)
        top = win32api.GetSystemMetrics(win32con.SM_YVIRTUALSCREEN)

    hwindc = win32gui.GetWindowDC(hwin)
    srcdc = win32ui.CreateDCFromHandle(hwindc)
    memdc = srcdc.CreateCompatibleDC()
    bmp = win32ui.CreateBitmap()
    bmp.CreateCompatibleBitmap(srcdc, width, height)
    memdc.SelectObject(bmp)
    memdc.BitBlt((0, 0), (width, height), srcdc, (left, top), win32con.SRCCOPY)
    
    signedIntsArray = bmp.GetBitmapBits(True)
    img = np.fromstring(signedIntsArray, dtype='uint8')
    img.shape = (height, width, 4)

    #cv2.imwrite("imageFULL.png", img) 
    srcdc.DeleteDC()
    memdc.DeleteDC()
    win32gui.ReleaseDC(hwin, hwindc)
    win32gui.DeleteObject(bmp.GetHandle())

    return cv2.cvtColor(img, cv2.COLOR_BGRA2RGB)

# 上边中点与下边左顶点和右顶点以外的区域截掉
def grab_screen_custom(region=None):
    hwin = win32gui.GetDesktopWindow()

    if region:
        left, top, x2, y2 = region
        width = x2 - left + 1
        height = y2 - top + 1
    else:
        width = win32api.GetSystemMetrics(win32con.SM_CXVIRTUALSCREEN)
        height = win32api.GetSystemMetrics(win32con.SM_CYVIRTUALSCREEN)
        left = win32api.GetSystemMetrics(win32con.SM_XVIRTUALSCREEN)
        top = win32api.GetSystemMetrics(win32con.SM_YVIRTUALSCREEN)

    hwindc = win32gui.GetWindowDC(hwin)
    srcdc = win32ui.CreateDCFromHandle(hwindc)
    memdc = srcdc.CreateCompatibleDC()
    bmp = win32ui.CreateBitmap()
    bmp.CreateCompatibleBitmap(srcdc, width, height)
    memdc.SelectObject(bmp)
    memdc.BitBlt((0, 0), (width, height), srcdc, (left, top), win32con.SRCCOPY)
    
    signedIntsArray = bmp.GetBitmapBits(True)
    img = np.frombuffer(signedIntsArray, dtype='uint8')
    img.shape = (height, width, 4)

    # Release resources
    srcdc.DeleteDC()
    memdc.DeleteDC()
    win32gui.ReleaseDC(hwin, hwindc)
    win32gui.DeleteObject(bmp.GetHandle())

    # Convert to RGB
    img = cv2.cvtColor(img, cv2.COLOR_BGRA2RGB)

    # Get dimensions
    img_height, img_width, _ = img.shape

    # 计算关键点
    top_mid = (img_width // 2, 0)  # 上边中点
    bottom_left = (0, img_height)  # 下边左顶点
    bottom_right = (img_width, img_height)  # 下边右顶点

    # 创建一个遮罩
    mask = np.zeros_like(img, dtype='uint8')
    pts = np.array([top_mid, bottom_left, bottom_right], dtype=np.int32)
    cv2.fillPoly(mask, [pts], (255, 255, 255))

    # 使用遮罩
    img = cv2.bitwise_and(img, mask)
    
    return img

# 上边中点与下边左顶点和右顶点以外的区域截掉
def screen_mask(image, region=None):
    img = image.copy()

    # Get dimensions
    img_height, img_width  = img.shape

    # 计算关键点
    top_mid = (img_width // 2, 0)  # 上边中点
    bottom_left = (0, img_height)  # 下边左顶点
    bottom_right = (img_width, img_height)  # 下边右顶点

    # 创建一个遮罩
    mask = np.zeros_like(img, dtype='uint8')
    pts = np.array([top_mid, bottom_left, bottom_right], dtype=np.int32)
    cv2.fillPoly(mask, [pts], (255, 255, 255))

    # 使用遮罩
    img = cv2.bitwise_and(img, mask)
    
    return img