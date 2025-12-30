#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Step 4 左侧图片板块切分测试脚本.

功能：
1. 读取左侧图片
2. 使用OCR提取关键词Y坐标
3. 根据坐标切分成7个板块
4. 保存到输出目录

使用方法：
    python scripts/test_step4_simple.py test_output/step3/MP_01142025_statement_summary_left.png
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
from app.services.left_section_cutter import LeftSectionCutter
import cv2

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_section_cutting(left_image_path: str):
    """测试左侧图片板块切分."""

    logger.info("=" * 60)
    logger.info("Step 4 左侧图片板块切分测试")
    logger.info("=" * 60)

    # [1/4] 读取左侧图片
    logger.info(f"\n[1/4] 读取左侧图片: {left_image_path}")
    left_image = cv2.imread(left_image_path)

    if left_image is None:
        logger.error(f"无法读取图片: {left_image_path}")
        return

    height, width = left_image.shape[:2]
    logger.info(f"  图片尺寸: {width}x{height}px")

    # [2/4] 初始化OCR引擎并提取关键词坐标
    logger.info("\n[2/4] 初始化OCR引擎...")
    ocr_engine = OCREngine()
    splitter = ImageSplitter(ocr_engine)

    logger.info("提取关键词Y坐标...")
    keyword_map, ocr_results = splitter.extract_keywords_positions(left_image)

    # 打印关键词坐标
    logger.info("\n识别到的关键词坐标：")
    for section, keywords in keyword_map.items():
        if keywords:
            for keyword, y_coord in keywords.items():
                logger.info(f"  [{section}] {keyword}: Y={y_coord}")

    # [3/4] 初始化切分器并计算板块范围
    logger.info("\n[3/4] 初始化左侧板块切分器...")
    cutter = LeftSectionCutter()

    logger.info("计算板块Y坐标范围...")
    section_ranges = cutter.calculate_section_ranges(keyword_map, height)

    # [4/4] 切分图片并保存
    logger.info("\n[4/4] 切分图片并保存...")

    # 输出目录
    output_dir = "test_output/step4"

    # 基础文件名（从输入文件名提取）
    # 例如: MP_01142025_statement_summary_left.png -> MP_01142025
    input_filename = Path(left_image_path).stem
    # 移除"_statement_summary_left"后缀
    if "_statement_summary_left" in input_filename:
        base_filename = input_filename.replace("_statement_summary_left", "")
    else:
        # 如果没有标准后缀，使用整个文件名
        base_filename = input_filename

    logger.info(f"基础文件名: {base_filename}")

    # 执行切分
    saved_files = cutter.cut_sections(
        left_image,
        section_ranges,
        output_dir,
        base_filename
    )

    # 完成
    logger.info("\n" + "=" * 60)
    logger.info("测试完成")
    logger.info("=" * 60)
    logger.info(f"输出目录: {output_dir}")
    logger.info(f"共生成 {len(saved_files)} 个板块图片：")
    for section_name, file_path in saved_files.items():
        logger.info(f"  [{section_name}] {file_path}")
    logger.info("=" * 60)


def main():
    """主函数."""
    if len(sys.argv) < 2:
        print("用法: python scripts/test_step4_simple.py <左侧图片路径>")
        print("示例: python scripts/test_step4_simple.py test_output/step3/MP_01142025_statement_summary_left.png")
        sys.exit(1)

    image_path = sys.argv[1]

    # 检查文件是否存在
    if not os.path.exists(image_path):
        print(f"错误: 文件不存在: {image_path}")
        sys.exit(1)

    # 运行测试
    test_section_cutting(image_path)


if __name__ == "__main__":
    main()
