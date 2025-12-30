#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Step 3 关键词识别简化测试脚本.

只做最核心的功能：
1. 读取已有的左侧图片
2. OCR识别提取关键词Y坐标
3. 生成可视化图片

使用方法：
    python scripts/test_step3_simple.py test_output/step3/MP_01142025_statement_summary_left.png
"""

import sys
import os
import logging
from pathlib import Path

# 添加backend目录到Python路径
backend_dir = Path(__file__).parent.parent / 'backend'
sys.path.insert(0, str(backend_dir))

from app.services.image_splitter import ImageSplitter
from app.services.ocr_engine import OCREngine
import cv2

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_keywords_simple(left_image_path: str):
    """简化测试：只识别关键词并可视化."""

    logger.info("=" * 60)
    logger.info("Step 3 关键词识别简化测试")
    logger.info("=" * 60)

    # 读取左侧图片
    logger.info(f"\n[1/3] 读取左侧图片: {left_image_path}")
    left_image = cv2.imread(left_image_path)

    if left_image is None:
        logger.error(f"无法读取图片: {left_image_path}")
        return

    logger.info(f"  原始尺寸: {left_image.shape}")

    # 不再缩放图片，Vision框架性能足够好

    # 初始化OCR引擎
    logger.info("\n[2/3] 初始化OCR引擎...")
    ocr_engine = OCREngine()
    splitter = ImageSplitter(ocr_engine)

    # 提取关键词Y坐标
    logger.info("\n[3/3] 提取关键词Y坐标...")
    keyword_map, ocr_results = splitter.extract_keywords_positions(left_image)

    # 打印识别结果
    logger.info("\n识别到的关键词：")
    for section, keywords in keyword_map.items():
        if keywords:
            for keyword, y_coord in keywords.items():
                logger.info(f"  [{section}] {keyword}: Y={y_coord}")
        else:
            logger.warning(f"  [{section}] 未找到关键词")

    # 生成可视化图片
    logger.info("\n[4/3] 生成可视化图片...")
    output_path = Path(left_image_path).parent
    vis_filename = Path(left_image_path).stem + "_visualization.png"
    vis_path = output_path / vis_filename

    splitter.visualize_keywords(
        left_image,
        keyword_map,
        str(vis_path)
    )

    logger.info(f"  可视化图片: {vis_path}")

    # 完成
    logger.info("\n" + "=" * 60)
    logger.info("测试完成")
    logger.info("=" * 60)
    logger.info(f"输出文件: {vis_path}")
    logger.info("请打开图片检查红线是否准确标注在关键词位置")
    logger.info("=" * 60)


def main():
    """主函数."""
    if len(sys.argv) < 2:
        print("用法: python scripts/test_step3_simple.py <左侧图片路径>")
        print("示例: python scripts/test_step3_simple.py test_output/step3/MP_01142025_statement_summary_left.png")
        sys.exit(1)

    image_path = sys.argv[1]

    # 检查文件是否存在
    if not os.path.exists(image_path):
        print(f"错误: 文件不存在: {image_path}")
        sys.exit(1)

    # 运行测试
    test_keywords_simple(image_path)


if __name__ == "__main__":
    main()
