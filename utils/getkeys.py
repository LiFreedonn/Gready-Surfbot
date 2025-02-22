import win32api as wapi
import time

keyList = ["\b"]
for char in "ABCDEFGHIJKLMNOPQRSTUVWXYZ 123456789,.'APS$/\\":
    keyList.append(char)

# 添加方向键的虚拟键码
keyList.extend([0x25, 0x26, 0x27, 0x28])  # 0x25: Left, 0x26: Up, 0x27: Right, 0x28: Down

def key_check():
    keys = []
    for key in keyList:
        # if wapi.GetAsyncKeyState(ord(key)):
        if wapi.GetAsyncKeyState(ord(key) if isinstance(key, str) else key): # key是虚拟键码时，不能用ord。
            keys.append(key)



    if 'H' in keys: # 优先级最高
        return 'H'
    elif ' ' in keys:  # Space key
        return ' '
    elif 0x26 in keys:  # Up arrow key
        return 'Up'
    elif 0x28 in keys:  # Down arrow key
        return 'Down'
    elif 0x25 in keys:  # Left arrow key
        return 'Left'
    elif 0x27 in keys:  # Right arrow key
        return 'Right'
    elif 'A' in keys:
        return 'A'
    elif 'D' in keys:
        return 'D'
    elif 'S' in keys:
        return 'S'
    elif 'B' in keys:
        return 'B'
    else:
        return 'Q'
