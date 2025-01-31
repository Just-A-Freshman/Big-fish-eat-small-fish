from PIL import Image
import os

def is_image_background_transparent(image_path):
    # 打开图片
    with Image.open(image_path) as img:
        # 确保图片是RGBA模式
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
        
        # 获取图片的宽度和高度
        width, height = img.size
        
        # 遍历图片的每个像素
        for x in range(width):
            for y in range(height):
                # 获取像素的RGBA值
                r, g, b, a = img.getpixel((x, y))
                # 如果透明度不为0，返回False
                if a == 255:
                    continue
                if a != 0:
                    
                    return False
        # 如果所有像素的透明度都为0，返回True
        return True
    
def make_transparent_points_white(image_path, output_path):
    # 打开图片
    with Image.open(image_path) as img:
        # 确保图片是RGBA模式
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
        
        # 获取图片的宽度和高度
        width, height = img.size
        
        # 遍历图片的每个像素
        for x in range(width):
            for y in range(height):
                # 获取像素的RGBA值
                r, g, b, a = img.getpixel((x, y))
                # 如果透明度不为0，将像素颜色设置为纯白色
                if a == 255:
                    continue
                if a != 0:
                    img.putpixel((x, y), (r, g, b, 255))
        
        # 保存处理后的图片
        img.save(output_path)
    

if __name__ == '__main__':
    input_path = r"D:\Users\pbl\Desktop\源代码\resources\MediumFish\1.8.png"
    output_path = r"D:\Users\pbl\Desktop\test\result.png"
    make_transparent_points_white(input_path, output_path)
    