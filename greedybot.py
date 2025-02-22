import random
import time
import tkinter as tk
from utils.getkeys import key_check
import pydirectinput
import keyboard
import time
import cv2
from utils.grabscreen import grab_screen, screen_mask
from utils.pixel_filter import pixel_filter

import os
import cv2
import numpy as np
import time

class ActionDeterminer:
    def __init__(self):
        self.offset = 25
        self.halfside = 17
        self.linewidth1 = 50
        self.linewidth2 = 60
        self.masks_computed = False
        self.masks = {}
        self.counter = 0
        self.green_value = 150  # 绿色道具的像素值
        self.red_value = 50    # 红色减速的像素值
        self.black_value = 253  # 黑色障碍的像素值
        self.white_value = 251  # 监测点的像素值

    def _compute_masks(self, image):
        height, width = image.shape
        # 需要确定角色方框中心坐标
        center_x = 1009 # 为 width // 2
        center_y = 22 
        
        # 定义mask参数
        # right 和 left 的移动高宽比为 1.7
        # rightright 和 leftleft 的移动高宽比为 0.9
        length1 = int((height - center_y) // 1.7)
        length2 = int((height - center_y) // 0.9)
        # import ipdb; ipdb.set_trace()
        masks_params = [
            ('mask1', (center_x - self.offset, center_y), (center_x + self.offset, height), self.linewidth1),
            ('mask2', (center_x, center_y), (center_x + length1, height), self.linewidth1),  # right
            ('mask3', (center_x, center_y), (center_x - length1, height), self.linewidth1),   # left
            ('mask4', (center_x, center_y), (center_x + length2, height), self.linewidth2),  # rightright
            ('mask5', (center_x, center_y), (center_x - length2, height), self.linewidth2),   # leftleft
        ]
        
        # 创建并存储mask
        for name, start, end, thickness in masks_params:
            mask = np.zeros((height, width), dtype=np.uint8)
            if name == 'mask1':
                mask[start[1]:end[1], start[0]:end[0]] = 255
            else:
                cv2.line(mask, start, end, 255, thickness=thickness)
            self.masks[name] = mask
            
        self.masks_computed = True

    def _calculate_path(self, image, green_flag):
        path_lengths = []
        
        for mask_name in ['mask1', 'mask2', 'mask3', 'mask4', 'mask5']:
            # 获取当前路径的mask区域
            masked_image = cv2.bitwise_and(self.masks[mask_name], image)
            
            # 计算路径长度（无障碍距离）
            if (green_flag):
                green_counts = np.sum(masked_image == self.green_value, axis=1)
                green_index = np.argmax(green_counts >= 8)

                if green_counts[green_index] < 8:
                    green_index = 0
                    
                path_length = np.argmax((masked_image == 253).any(axis=1))
                if ((green_index != 0 and path_length != 0 and green_index + 10 < path_length) or (path_length == 0 and green_index != 0)):
                    path_length = 1600 -  green_index
                        
            else:
                path_length = np.argmax(masked_image.any(axis=1))
            
            if path_length == 0:
                path_length = 700  # 如果路径完全畅通
                
            path_lengths.append(path_length)
            
        return path_lengths

    def determine_action(self, image, prev_action, green_flag, vis=False):
        if not self.masks_computed:
            self._compute_masks(image)
     
        image[:50, :] = 0  # 去掉人物区域
        
        # 计算每条路径
        path_lengths = self._calculate_path(image, green_flag)
        
        # 选择最佳路径
        action = np.argmax(path_lengths)

        # 如果当前路径仍然安全，保持原动作
        if ((path_lengths[prev_action] + 30 > path_lengths[action]) and (path_lengths[prev_action] > 650)) or (path_lengths[prev_action] > 700) or \
            ((path_lengths[prev_action] > 500) and (path_lengths[action] > 700) and (path_lengths[action] < 1300) ):
            action = prev_action

        if ((path_lengths[0] >= 700) and (path_lengths[0] >= path_lengths[action])):
            action = 0
        
        return action, path_lengths
    
    def check_status(self, image):
        status = 6
        height = 42
        if (image[height, 1012] == self.white_value and image[height, 1006] == self.white_value):
            status = 0
        elif (image[height-7, 1027] == self.white_value and image[height-6, 1027] == self.white_value):
            status = 1
        elif (image[height-7, 991] == self.white_value and image[height-6, 991] == self.white_value):
            status = 2
        elif (image[height, 1026] == self.white_value and image[height-6, 1033] == self.white_value):
            status = 3
        elif (image[height, 992] == self.white_value and image[height-6, 985] == self.white_value):
            status = 4

        return status

    def _visualize_masks(self, image, longest_way):
        # 创建一个白色图像
        white_image = np.ones_like(image) * 255

        # 合并所有的 mask
        combined_mask = self.masks['mask1'] | self.masks['mask2'] | self.masks['mask3'] | self.masks['mask4'] | \
                        self.masks['mask5']

        # 将合并后的 mask 应用到白色图像上
        masked_white = cv2.bitwise_and(white_image, white_image, mask=combined_mask)
        # 将合并后的 mask 应用到原始图像上
        masked_original = cv2.bitwise_and(image, image, mask=cv2.bitwise_not(combined_mask))
        # 将两部分合并
        result_image = cv2.add(masked_original, masked_white)
        height, width = result_image.shape
        disp_img = cv2.resize(result_image, (width//3, height//3))

        cv2.imshow("Processed Image", disp_img)
        cv2.waitKey(1)
        cv2.moveWindow("Processed Image", 100, 100)
        # 设置窗口置顶
        cv2.setWindowProperty('Processed Image', cv2.WND_PROP_TOPMOST, 1)

        text_image = np.zeros((200, 600, 3), dtype=np.uint8)
        text = "Distance:{} ".format(longest_way)
        # 设置字体参数
        font = cv2.FONT_HERSHEY_SIMPLEX  # 字体
        font_scale = 0.7  # 字体大小
        font_color = (255, 255, 255)  # 字体颜色 (绿色)
        font_thickness = 1  # 字体粗细
        # 获取文本的宽度和高度
        text_size, _ = cv2.getTextSize(text, font, font_scale, font_thickness)
        # 计算文本的中心位置
        text_x = (text_image.shape[1] - text_size[0]) // 2
        text_y = (text_image.shape[0] + text_size[1]) // 2
        cv2.putText(text_image, text, (text_x, text_y), font, font_scale, font_color, font_thickness)
        cv2.imshow("Text", text_image)
        cv2.waitKey(1)
        cv2.moveWindow("Text", 1250, 100)
        cv2.setWindowProperty("Text", cv2.WND_PROP_TOPMOST, 1)


# Tkinter 窗口设置
class PredictionWindow:
    def __init__(self):
        self.root = tk.Tk()
        self.root.attributes("-topmost", True)  # 设置窗口置顶
        self.root.overrideredirect(True)
        self.root.geometry("400x100+820+150")

        self.label = tk.Label(self.root, text="...", font=("Helvetica", 10))
        self.label.pack(expand=True)

        self.start_x = 0
        self.start_y = 0

    def start_drag(self, event):
        self.start_x = event.x
        self.start_y = event.y

    def do_drag(self, event):
        x = self.root.winfo_x() + event.x - self.start_x
        y = self.root.winfo_y() + event.y - self.start_y
        self.root.geometry(f"+{x}+{y}")

    def resize_window(self, event):
        new_width = self.root.winfo_width() + event.x
        new_height = self.root.winfo_height() + event.y
        self.root.geometry(f"{new_width}x{new_height}")

    def update_label(self, text):
        self.label.config(text=text)
        self.root.update()

# 创建窗口
prediction_window = PredictionWindow()

sleepy = 0.1

# 开始
print("Waiting For M to Start")
keyboard.wait('m')
action_determiner = ActionDeterminer()

prev_action = 0
prev_flash_num = 0
visual = True
image_count = 0
paused = False 

while True:
    # 暂停
    if keyboard.is_pressed('t'):
        if not paused:
            print("Algorithm Paused")
            paused = True
        keyboard.block_key('t') 

    # 继续
    if paused:
        if keyboard.is_pressed('c'):
            print("Algorithm Resumed")
            paused = False
            keyboard.block_key('c')
        time.sleep(0.1)
        continue

    # 截图
    image = grab_screen(region=(270, 600, 2287, 1299))
    image, green_flag = pixel_filter(image)
    image_prediction = image.copy()
    
    action, longest_way = action_determiner.determine_action(image_prediction, prev_action, green_flag,  vis = visual)
 
    status = action_determiner.check_status(image)
    flash_image = grab_screen(region=(1375, 115, 1466, 144))
    
    if np.array_equal(flash_image[12, 71], [75, 210, 146]):
        flash_num = 3
    elif np.array_equal(flash_image[12, 38], [75, 210, 146]):
        flash_num = 2
    elif np.array_equal(flash_image[12, 5], [75, 210, 146]):
        flash_num = 1
    else:
        flash_num = 0
    
    # 更新窗口显示预测结果
    prediction_window.update_label(f"Action: {action} Previous Action: {prev_action} Status: {status} Flash : {flash_num}")
    prev_action = action
    
    if flash_num < prev_flash_num:
        keyboard.press("w")
        keyboard.release("w")
    prev_flash_num = flash_num    

    if (action != status):
        if action == 0:
            keyboard.press("s")
            keyboard.release("s")


        elif action == 1: # right
            if (status == 3):
                keyboard.press("s")
                keyboard.release("s")
                keyboard.press("d")
                keyboard.release("d")
            else:
                keyboard.press("d")
                keyboard.release("d")

        elif action == 2:  # left
            if (status == 4):
                keyboard.press("s")
                keyboard.release("s")
                keyboard.press("a")
                keyboard.release("a")
            else:
                keyboard.press("a")
                keyboard.release("a")

        elif action == 3: # right right
            if (status == 1):
                keyboard.press("d")
                keyboard.release("d")
            else:
                keyboard.press("d")
                keyboard.release("d")
                keyboard.press("d")
                keyboard.release("d")

        elif action == 4: # left left
            if (status == 2):
                keyboard.press("a")
                keyboard.release("a")
            else:
                keyboard.press("a")
                keyboard.release("a")
                keyboard.press("a")
                keyboard.release("a")

    keys = key_check()
    if keys == "H":
        break

    action_determiner._visualize_masks(image_prediction, longest_way)

print("Algorithm Stop")
