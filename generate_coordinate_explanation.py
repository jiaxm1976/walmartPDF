#!/usr/bin/env python3
# ============================================================# 文件: generate_coordinate_explanation.py
# 功能: 生成带坐标系解释的测试文件
# 作者: 开发团队
# 创建时间: 2025-12-25
# ============================================================

import os
import sys
import logging
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

# 添加项目根目录和backend目录到Python路径
sys.path.append(str(Path(__file__).parent))
sys.path.append(str(Path(__file__).parent / "backend"))

# 导入OCR引擎
from backend.app.services.ocr_engine import OCREngine

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('generate_coordinate_explanation.log')
    ]
)
logger = logging.getLogger(__name__)

def draw_coordinate_system(image_array, output_path):
    """在图片上绘制坐标系示意图"""
    # 转换为PIL图片
    img = Image.fromarray(image_array)
    draw = ImageDraw.Draw(img)
    
    # 绘制坐标轴
    width, height = img.size
    axis_length = 100
    arrow_size = 15
    
    # X轴（红色）
    draw.line([(50, height-50), (50+axis_length, height-50)], fill="red", width=2)
    # X轴箭头
    draw.polygon([(50+axis_length, height-50), (50+axis_length-arrow_size, height-50-arrow_size/2), 
                  (50+axis_length-arrow_size, height-50+arrow_size/2)], fill="red")
    
    # Y轴（绿色）
    draw.line([(50, height-50), (50, height-50-axis_length)], fill="green", width=2)
    # Y轴箭头
    draw.polygon([(50, height-50-axis_length), (50-arrow_size/2, height-50-axis_length+arrow_size), 
                  (50+arrow_size/2, height-50-axis_length+arrow_size)], fill="green")
    
    # 绘制原点
    draw.ellipse([(45, height-55), (55, height-45)], fill="blue")
    
    # 添加文字说明
    try:
        draw.text((50+axis_length+10, height-55), "X轴", fill="red", font=ImageFont.load_default())
        draw.text((40, height-50-axis_length-15), "Y轴", fill="green", font=ImageFont.load_default())
        draw.text((20, height-30), "原点 (0,0)", fill="blue", font=ImageFont.load_default())
    except:
        # 如果无法加载字体，不添加文字
        pass
    
    # 保存图片
    img.save(output_path)
    logger.info(f"✓ 坐标系示意图已保存: {output_path}")

def format_box(box):
    """格式化坐标框输出"""
    if not box:
        return "[]"
    return f"[{box[0][0]},{box[0][1]}] [{box[1][0]},{box[1][1]}] [{box[2][0]},{box[2][1]}] [{box[3][0]},{box[3][1]}]"

def generate_coordinate_explanation():
    """生成带坐标系解释的测试文件"""
    logger.info("=" * 80)
    logger.info("开始生成带坐标系解释的测试文件")
    logger.info("=" * 80)
    
    try:
        # 初始化OCR引擎（使用Apple Vision OCR）
        ocr_engine = OCREngine(engine_type="vision")
        logger.info("✓ OCR引擎初始化成功")
        
        # 选择一个测试PDF文件
        pdf_path = "/Users/jiaxinming/JxmWork/walmart-a/PdfData/MP_01142025_statement_summary.pdf"
        if not os.path.exists(pdf_path):
            logger.error(f"✗ PDF文件不存在: {pdf_path}")
            return False
        
        # 导入pdf_to_images函数
        from backend.app.utils.image_utils import pdf_to_images
        
        # 将PDF转换为图片
        logger.info(f"正在处理PDF文件: {pdf_path}")
        images = pdf_to_images(pdf_path, dpi=300, grayscale=True)
        if not images:
            logger.error("✗ PDF转图片失败")
            return False
        
        # 使用第一页图片进行测试
        first_page = images[0]
        logger.info(f"✓ PDF转图片成功，共 {len(images)} 页，使用第1页进行测试")
        
        # 确保图片是灰度的
        if first_page.mode != 'L':
            first_page = first_page.convert('L')
        
        # 转换为numpy数组
        image_array = np.array(first_page)
        image_height, image_width = image_array.shape
        
        # 使用recognize_image方法获取带坐标的文本块
        logger.info("\n正在调用recognize_image方法...")
        ocr_results = ocr_engine.recognize_image(image_array)
        
        # 输出坐标系解释
        logger.info("\n" + "=" * 80)
        logger.info("OCR坐标系详细解释")
        logger.info("=" * 80)
        
        coordinate_explanation = """
OCR坐标系解释：

1. 坐标原点：图片左上角 (0, 0)
2. X轴方向：从左到右，值逐渐增加
3. Y轴方向：从上到下，值逐渐增加
4. 坐标单位：像素 (pixel)

坐标框格式：
[ [x1,y1], [x2,y2], [x3,y3], [x4,y4] ]
其中：
- (x1,y1) = 左上角坐标
- (x2,y2) = 右上角坐标
- (x3,y3) = 右下角坐标
- (x4,y4) = 左下角坐标

坐标框示例：
[ [100,200], [200,200], [200,250], [100,250] ]
表示一个宽100像素、高50像素的矩形，左上角在(100,200)位置。

图片信息：
- 宽度：{} 像素
- 高度：{} 像素
- 分辨率：300 DPI
        """
        
        logger.info(coordinate_explanation.format(image_width, image_height))
        
        # 输出前10个文本块的详细信息
        logger.info("\n" + "=" * 80)
        logger.info("前10个文本块的坐标信息")
        logger.info("=" * 80)
        
        sample_results = ocr_results[:10]  # 只显示前10个结果
        for i, (box, (text, confidence)) in enumerate(sample_results):
            logger.info(f"\n  {i+1:2d}. 文本: {text}")
            logger.info(f"     置信度: {confidence:.2f}")
            logger.info(f"     坐标框: {format_box(box)}")
            
            # 计算文本块的位置信息
            left = box[0][0]
            top = box[0][1]
            right = box[2][0]
            bottom = box[2][1]
            width = right - left
            height = bottom - top
            center_x = int((left + right) / 2)
            center_y = int((top + bottom) / 2)
            
            logger.info(f"     位置信息:")
            logger.info(f"       - 左上角: [{left}, {top}]")
            logger.info(f"       - 右下角: [{right}, {bottom}]")
            logger.info(f"       - 宽度: {width} 像素")
            logger.info(f"       - 高度: {height} 像素")
            logger.info(f"       - 中心点: [{center_x}, {center_y}]")
        
        # 输出到文本文件
        output_file = "coordinate_system_explanation.txt"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("OCR坐标系详细解释\n")
            f.write("=" * 70 + "\n")
            f.write(coordinate_explanation.format(image_width, image_height))
            
            f.write("\n" + "=" * 70 + "\n")
            f.write(f"所有文本块信息（共 {len(ocr_results)} 个）\n")
            f.write("=" * 70 + "\n")
            
            for i, (box, (text, confidence)) in enumerate(ocr_results):
                f.write(f"\n{i+1:2d}. 文本: {text}\n")
                f.write(f"   置信度: {confidence:.2f}\n")
                f.write(f"   坐标框: {format_box(box)}\n")
                
                # 计算文本块的位置信息
                left = box[0][0]
                top = box[0][1]
                right = box[2][0]
                bottom = box[2][1]
                width = right - left
                height = bottom - top
                center_x = int((left + right) / 2)
                center_y = int((top + bottom) / 2)
                
                f.write(f"   位置信息: 左上角[{left}, {top}], 右下角[{right}, {bottom}], ")
                f.write(f"宽度{width}px, 高度{height}px, 中心点[{center_x}, {center_y}]")
        
        logger.info(f"\n✓ 坐标系解释和文本块信息已保存: {output_file}")
        
        # 绘制坐标系示意图
        try:
            coordinate_image_path = "coordinate_system_diagram.png"
            draw_coordinate_system(image_array, coordinate_image_path)
        except Exception as e:
            logger.warning(f"绘制坐标系示意图失败: {e}")
        
        logger.info("\n" + "=" * 80)
        logger.info("带坐标系解释的测试文件生成完成")
        logger.info("=" * 80)
        
        return True
        
    except Exception as e:
        logger.error(f"✗ 生成失败: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    generate_coordinate_explanation()