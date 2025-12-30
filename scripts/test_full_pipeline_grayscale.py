#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整流水线测试脚本（灰度版本）.

从PDF开始，执行完整的7步流程：
Step 1: PDF转灰度图片（提高OCR准确率）
Step 2: 横向63%分割
Step 3: 提取关键词Y坐标
Step 4: 左侧图片板块切分
Step 5: OCR识别各板块并输出JSON

使用方法：
    python scripts/test_full_pipeline_grayscale.py PdfData/MP_01142025_statement_summary.pdf
"""

import sys
import os
import logging
from pathlib import Path

# 添加backend目录到Python路径
backend_dir = Path(__file__).parent.parent / 'backend'
sys.path.insert(0, str(backend_dir))

from app.utils.image_utils import pdf_to_images
from app.services.image_splitter import ImageSplitter
from app.services.ocr_engine import OCREngine
from app.services.left_section_cutter import LeftSectionCutter
from app.services.left_section_ocr import LeftSectionOCR
import cv2

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_full_pipeline(pdf_path: str):
    """测试完整流水线（灰度版本）."""

    logger.info("=" * 80)
    logger.info("完整流水线测试 - 灰度优化版")
    logger.info("=" * 80)

    pdf_name = Path(pdf_path).stem
    output_base = Path("test_output_grayscale")

    # ============================================================
    # Step 1: PDF转灰度图片
    # ============================================================
    logger.info("\n【Step 1】PDF转灰度图片")
    logger.info("-" * 60)

    step1_output = output_base / "step1"
    images = pdf_to_images(
        pdf_path,
        dpi=300,  # 使用300 DPI平衡质量和性能
        output_dir=str(step1_output),
        save_images=True,
        grayscale=True  # 关键：转换为灰度图
    )

    if not images:
        logger.error("PDF转换失败")
        return

    logger.info(f"✓ 成功转换 {len(images)} 页（灰度模式）")

    # 转换PIL Image为OpenCV格式
    import numpy as np
    image_array = np.array(images[0])

    # 如果是灰度图，需要转换为BGR（OpenCV默认格式）
    if len(image_array.shape) == 2:
        # 灰度图转BGR
        image_array = cv2.cvtColor(image_array, cv2.COLOR_GRAY2BGR)

    # ============================================================
    # Step 2: 横向63%分割
    # ============================================================
    logger.info("\n【Step 2】横向63%分割")
    logger.info("-" * 60)

    step2_output = output_base / "step2"
    step2_output.mkdir(parents=True, exist_ok=True)

    ocr_engine = OCREngine()
    splitter = ImageSplitter(ocr_engine)

    left_image, right_image = splitter.split_horizontal(image_array)

    # 保存分割后的图片
    left_path = step2_output / f"{pdf_name}_left.png"
    right_path = step2_output / f"{pdf_name}_right.png"
    cv2.imwrite(str(left_path), left_image)
    cv2.imwrite(str(right_path), right_image)

    logger.info(f"✓ 左侧图片: {left_image.shape[1]}x{left_image.shape[0]}px")
    logger.info(f"✓ 右侧图片: {right_image.shape[1]}x{right_image.shape[0]}px")

    # ============================================================
    # Step 3: 提取关键词Y坐标
    # ============================================================
    logger.info("\n【Step 3】提取关键词Y坐标")
    logger.info("-" * 60)

    keyword_map, ocr_results = splitter.extract_keywords_positions(left_image)

    logger.info(f"✓ 识别到 {sum(len(v) for v in keyword_map.values())} 个关键词")
    for section, keywords in keyword_map.items():
        for keyword, y_coord in keywords.items():
            logger.info(f"  [{section}] {keyword}: Y={y_coord}")

    # ============================================================
    # Step 4: 左侧图片板块切分
    # ============================================================
    logger.info("\n【Step 4】左侧图片板块切分")
    logger.info("-" * 60)

    step4_output = output_base / "step4"
    cutter = LeftSectionCutter()

    height = left_image.shape[0]
    section_ranges = cutter.calculate_section_ranges(keyword_map, height)

    saved_files = cutter.cut_sections(
        left_image,
        section_ranges,
        str(step4_output),
        pdf_name
    )

    logger.info(f"✓ 切分完成，共 {len(saved_files)} 个板块")

    # ============================================================
    # Step 5: OCR识别各板块并输出JSON
    # ============================================================
    logger.info("\n【Step 5】OCR识别各板块")
    logger.info("-" * 60)

    # 读取所有板块图片
    section_images = {}
    for section_name, file_path in saved_files.items():
        img = cv2.imread(file_path)
        if img is not None:
            section_images[section_name] = img

    # OCR识别
    section_ocr = LeftSectionOCR(ocr_engine)
    result_data = section_ocr.process_all_sections(section_images)

    # 保存JSON
    step5_output = output_base / "step5"
    step5_output.mkdir(parents=True, exist_ok=True)
    json_path = step5_output / f"{pdf_name}_left_data.json"
    section_ocr.save_json(result_data, str(json_path))

    logger.info(f"✓ JSON已保存: {json_path}")

    # ============================================================
    # 完成
    # ============================================================
    logger.info("\n" + "=" * 80)
    logger.info("流水线测试完成")
    logger.info("=" * 80)
    logger.info(f"输出目录: {output_base}")
    logger.info(f"JSON文件: {json_path}")
    logger.info("\n运行验证脚本查看结果：")
    logger.info(f"  python scripts/verify_json_output.py {json_path}")
    logger.info("=" * 80)


def main():
    """主函数."""
    if len(sys.argv) < 2:
        print("用法: python scripts/test_full_pipeline_grayscale.py <PDF文件路径>")
        print("示例: python scripts/test_full_pipeline_grayscale.py PdfData/MP_01142025_statement_summary.pdf")
        sys.exit(1)

    pdf_path = sys.argv[1]

    if not os.path.exists(pdf_path):
        print(f"错误: 文件不存在: {pdf_path}")
        sys.exit(1)

    test_full_pipeline(pdf_path)


if __name__ == "__main__":
    main()
