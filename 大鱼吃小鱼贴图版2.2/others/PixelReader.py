"""
基于图像像素进行碰撞检测
这可能遇到诸多问题，实际测试时总是会碰到如大幅度颜色变化；

"""
import ctypes
from ctypes import wintypes
from typing import Sequence, Generator


user32 = ctypes.windll.user32
gdi32 = ctypes.windll.gdi32

# 定义类型
HWND = wintypes.HWND
HDC = wintypes.HDC
HBITMAP = wintypes.HBITMAP


class BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [
        ("biSize", wintypes.DWORD),
        ("biWidth", wintypes.LONG),
        ("biHeight", wintypes.LONG),
        ("biPlanes", wintypes.WORD),
        ("biBitCount", wintypes.WORD),
        ("biCompression", wintypes.DWORD),
        ("biSizeImage", wintypes.DWORD),
        ("biXPelsPerMeter", wintypes.LONG),
        ("biYPelsPerMeter", wintypes.LONG),
        ("biClrUsed", wintypes.DWORD),
        ("biClrImportant", wintypes.DWORD)
    ]

class BITMAPINFO(ctypes.Structure):
    _fields_ = [
        ("bmiHeader", BITMAPINFOHEADER),
        ("bmiColors", wintypes.DWORD * 3)
    ]


def get_pixel_color(coords: Sequence[tuple[int, int]], hwnd: HWND) -> Generator[tuple[int, int, int], None, None]:
    rect = wintypes.RECT()
    user32.GetClientRect(hwnd, ctypes.byref(rect))
    width = rect.right - rect.left
    height = rect.bottom - rect.top

    hdc_src = user32.GetDC(hwnd)
    hdc_dst = gdi32.CreateCompatibleDC(hdc_src)
    bmp = gdi32.CreateCompatibleBitmap(hdc_src, width, height)
    gdi32.SelectObject(hdc_dst, bmp)
 
    gdi32.BitBlt(hdc_dst, 0, 0, width, height, hdc_src, 0, 0, 0x00CC0020)  # SRCCOPY
 
    bmi = BITMAPINFO()
    bmi.bmiHeader.biSize = ctypes.sizeof(BITMAPINFOHEADER)
    bmi.bmiHeader.biWidth = width
    bmi.bmiHeader.biHeight = -height  # 负值表示自底向上
    bmi.bmiHeader.biPlanes = 1
    bmi.bmiHeader.biBitCount = 32
    bmi.bmiHeader.biCompression = 0
 
    buffer = ctypes.create_string_buffer(width * height * 4)
    gdi32.GetDIBits(hdc_dst, bmp, 0, height, buffer, ctypes.byref(bmi), 0)

    gdi32.DeleteObject(bmp)
    gdi32.DeleteDC(hdc_dst)
    user32.ReleaseDC(hwnd, hdc_src)
 
    for x, y in coords:
        if 0 <= x < width and 0 <= y < height:
            offset = (y * width + x) * 4
            color = buffer[offset:offset + 4]
            yield color[2], color[1], color[0]  # BGR -> RGB
        else:
            yield (0, 0, 0)

    

def find_window(class_name: str = None, window_name: str = None) -> HWND:
    return user32.FindWindowW(class_name, window_name)
