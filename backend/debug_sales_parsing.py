#!/usr/bin/env python3
"""
调试销售模块解析过程
"""

import logging
import sys
import os
import cv2
import numpy as np

# 设置日志级别为DEBUG
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.ocr_engine import OCREngine
from app.services.left_section_ocr import LeftSectionOCR
# 移除预处理函数导入

class DebugOCREngine:
    """调试用的OCR引擎，返回模拟数据"""
    
    def recognize_image(self, image):
        """返回模拟的OCR结果"""
        # 模拟销售板块的OCR结果
        return [
            ([[(0, 0), (100, 0), (100, 30), (0, 30)]], ("销售 1161.46美元", 0.99)),
            ([[(0, 40), (100, 40), (100, 70), (0, 70)]], ("产品价格", 0.99)),
            ([[(150, 40), (250, 40), (250, 70), (150, 70)]], ("1,355.89美元", 0.99)),
            ([[(0, 80), (100, 80), (100, 110), (0, 110)]], ("运输", 0.99)),
            ([[(150, 80), (250, 80), (250, 110), (150, 110)]], ("13.98美元", 0.99)),
            ([[(0, 120), (150, 120), (150, 150), (0, 150)]], ("WFS 运输税退款", 0.99)),
            ([[(200, 120), (300, 120), (300, 150), (200, 150)]], ("-1.01美元", 0.99)),
            ([[(0, 160), (100, 160), (100, 190), (0, 190)]], ("总计:", 0.99)),
            ([[(150, 160), (250, 160), (250, 190), (150, 190)]], ("-13.98美元", 0.99)),
        ]

def main():
    """主函数"""
    logger.info("开始调试销售模块解析")
    
    # 创建模拟图片
    image = np.zeros((200, 400, 3), dtype=np.uint8)
    
    # 初始化OCR引擎和解析器
    ocr_engine = DebugOCREngine()
    left_section_ocr = LeftSectionOCR(ocr_engine)
    
    # 提取文本行
    logger.info("\n1. 提取文本行:")
    text_lines = left_section_ocr.extract_text_lines(image)
    for i, (text, y_coord) in enumerate(text_lines):
        logger.info(f"   行{i}: {text} (Y={y_coord})")
        logger.info(f"   原始文本: {text}")
    
    # 提取键值对
    logger.info("\n2. 提取键值对:")
    data = left_section_ocr.extract_key_value_pairs(text_lines, extract_total_from_title=True)
    logger.info(f"   提取的数据: {data}")
    
    # 后处理
    logger.info("\n3. 后处理:")
    data = left_section_ocr.post_process_total(data, text_lines, section_name="sales")
    logger.info(f"   后处理后的数据: {data}")
    
    logger.info("\n调试结束")

if __name__ == "__main__":
    main()
