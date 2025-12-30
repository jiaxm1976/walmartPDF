#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试Step 6: 右侧付款详情OCR识别
"""

import sys
import os
import logging
from pathlib import Path
import cv2

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "backend"))

from app.services.ocr_engine import OCREngine
from app.services.right_section_ocr import RightSectionOCR

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_right_ocr(right_image_path: str, output_dir: str = "test_output_grayscale/step6"):
    """测试右侧付款详情OCR识别.

    Args:
        right_image_path: 右侧图片路径
        output_dir: 输出目录
    """
    logger.info("=" * 80)
    logger.info("测试Step 6: 右侧付款详情OCR识别")
    logger.info("=" * 80)

    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)

    # 1. 初始化OCR引擎
    logger.info("\n【初始化OCR引擎】")
    logger.info("-" * 60)
    ocr_engine = OCREngine()

    # 2. 初始化右侧OCR识别器
    logger.info("\n【初始化右侧OCR识别器】")
    logger.info("-" * 60)
    right_ocr = RightSectionOCR(ocr_engine)

    # 3. 读取右侧图片
    logger.info("\n【读取右侧图片】")
    logger.info("-" * 60)
    logger.info(f"图片路径: {right_image_path}")
    right_image = cv2.imread(right_image_path)
    if right_image is None:
        logger.error(f"无法读取图片: {right_image_path}")
        return
    logger.info(f"✓ 图片尺寸: {right_image.shape[1]}x{right_image.shape[0]}")

    # 4. OCR识别
    logger.info("\n【OCR识别】")
    logger.info("-" * 60)
    result = right_ocr.process_right_image(right_image)

    # 5. 保存JSON
    logger.info("\n【保存JSON】")
    logger.info("-" * 60)
    pdf_basename = Path(right_image_path).stem.replace("_right", "")
    output_json = os.path.join(output_dir, f"{pdf_basename}_right_data.json")
    right_ocr.save_json(result, output_json)
    logger.info(f"✓ JSON已保存: {output_json}")

    # 6. 显示结果
    logger.info("\n【识别结果】")
    logger.info("-" * 60)
    payment_details = result.get('payment_details', {})
    for key, value in payment_details.items():
        logger.info(f"  {key}: {value}")

    logger.info("\n" + "=" * 80)
    logger.info("测试完成")
    logger.info("=" * 80)
    logger.info(f"\n运行验证脚本查看结果：")
    logger.info(f"  cat {output_json}")
    logger.info("=" * 80)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python scripts/test_step6_right_ocr.py <右侧图片路径>")
        print("示例: python scripts/test_step6_right_ocr.py test_output_grayscale/step2/MP_01142025_statement_summary_right.png")
        sys.exit(1)

    right_image_path = sys.argv[1]
    test_right_ocr(right_image_path)
