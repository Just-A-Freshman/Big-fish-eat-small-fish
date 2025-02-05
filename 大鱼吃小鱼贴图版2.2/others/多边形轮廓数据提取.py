from PIL import Image
import cv2
import numpy as np
import matplotlib.pyplot as plt
import time
import os
import json


def create_closed_smooth_mask(image_path):
    image = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
    if image.shape[2] == 4:
        alpha_channel = image[:, :, 3]
        mask = alpha_channel > 0
        mask_proportion = np.count_nonzero(mask) / mask.size
        binary = np.zeros_like(alpha_channel)
        binary[mask] = 255
    else:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    kernel = np.ones((3, 3), np.uint8)
    opening = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel, iterations=2)
    contours, _ = cv2.findContours(opening, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    closed_mask = np.zeros((image.shape[0], image.shape[1], 4), dtype=np.uint8)
    closed_mask[:, :, 3] = 0
    contour_points = []
    for contour in contours:
        if len(contour) > 10:  # 确保轮廓至少有10个点
            epsilon = 0.003 * cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, epsilon, True)
            contour_points.append(approx.reshape(-1, 2).tolist())
            cv2.fillPoly(closed_mask, [approx], (0, 0, 0, 255))

    return closed_mask, contour_points, mask_proportion


def plot_polygon_and_point(polyX: list, polyY: list, x: int, y: int):
    polyX.append(polyX[0])
    polyY.append(polyY[0])
    plt.fill(polyX, polyY, 'r', alpha=0.5)
    plt.plot(polyX, polyY, 'r-')  # 绘制多边形边界
    plt.scatter(x, y, color='blue', s=10, label='Test Point')
    plt.title('Polygon and Test Point')
    plt.xlabel('X-axis')
    plt.ylabel('Y-axis')
    plt.legend()
    plt.axis('equal')
    plt.show()


def point_in_polygon(x, y, polyX, polyY):
    start = time.perf_counter()
    if x < min(polyX) or x > max(polyX) or y < min(polyY) or y > max(polyY):
        return False
    polySides = len(polyX)
    oddNodes = False
    
    for i in range(polySides):
        j = (i + 1) % polySides
        if ((polyY[i] < y and polyY[j] >= y) or (polyY[j] < y and polyY[i] >= y)) and \
           (polyX[i] + (y - polyY[i]) * (polyX[j] - polyX[i]) / (polyY[j] - polyY[i]) < x):
            oddNodes = not oddNodes
    return oddNodes


if __name__ == "__main__":
    root = r"D:\Users\pbl\Desktop\test"
    save_path = r"collision_basic.json"
    dir_path = ["SmallFish", "MediumFish", "HugeFish"]
    final_result = dict()

    for dir in dir_path:
        path = os.path.join(root, dir)
        for file in os.scandir(path):
            mask, points, area_propotion = create_closed_smooth_mask(file.path)
            X = [item[0] for item in points[0]]
            X.reverse()
            Y = [item[1] for item in points[0]]
            Y.reverse()
            with Image.open(file.path) as img:
                width, height = img.size
            final_result[file.name] = {
                "Size": [width, height],
                "Life_val": round(area_propotion, 2),
                "PolyX": X,
                "PolyY": Y
            }

    # 玩家的数据需要单独获取处理。这里是直接显示的将获取到的数据写在这里了。
    final_result["Player"] = {
        "Size": [480, 240],
        "Life_val": 0.45,
        "PolyX": [286, 272, 290, 256, 453, 228, 192, 155, 116, 312, 81, 343, 45, 439, 375, 10, 409, 31, 439, 370, 60, 345, 84, 314, 283, 257, 113, 230, 203, 462, 180, 138, 150],
        "PolyY": [25, 38, 59, 63, 67, 74, 75, 77, 83, 90, 92, 101, 105, 106, 115, 128, 134, 149, 151, 161, 168, 182, 183, 186, 189, 191, 192, 193, 195, 196, 201, 202, 222]
    }

    with open(save_path, "w") as f:
        json.dump(final_result, f)