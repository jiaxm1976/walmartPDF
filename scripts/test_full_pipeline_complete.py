#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整流水线测试 (Steps 1-6)
包括左侧和右侧的完整识别流程
"""

import sys
import os
import logging
from pathlib import Path
import cv2
import json

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "backend"))

from app.utils.image_utils import pdf_to_images
from app.services.ocr_engine import OCREngine
from app.services.image_splitter import ImageSplitter
from app.services.left_section_cutter import LeftSectionCutter
from app.services.left_section_ocr import LeftSectionOCR
from app.services.right_section_ocr import RightSectionOCR

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_full_pipeline(pdf_path: str, output_base_dir: str = "test_output_complete"):
    """完整流水线测试 (Steps 1-6).

    Args:
        pdf_path: PDF文件路径
        output_base_dir: 输出根目录
    """
    logger.info("=" * 80)
    logger.info("完整流水线测试 (Steps 1-6) - 左侧+右侧完整识别")
    logger.info("=" * 80)

    pdf_name = Path(pdf_path).stem

    # ============================================================
    # Step 1: PDF转灰度图片
    # ============================================================
    logger.info("\n【Step 1】PDF转灰度图片")
    logger.info("-" * 60)

    output_step1 = os.path.join(output_base_dir, "step1")
    os.makedirs(output_step1, exist_ok=True)

    pil_images = pdf_to_images(pdf_path, dpi=300, output_dir=output_step1, save_images=True, grayscale=True)
    logger.info(f"✓ 成功转换 {len(pil_images)} 页（灰度模式）")

    # 只处理第一页（PDF对账单的核心数据都在第1页）
    page1_filename = f"{pdf_name}_page_1.png"
    page1_path = os.path.join(output_step1, page1_filename)
    page1_image = cv2.imread(page1_path)

    # ============================================================
    # Step 2: 横向63%分割
    # ============================================================
    logger.info("\n【Step 2】横向63%分割")
    logger.info("-" * 60)

    ocr_engine = OCREngine()
    splitter = ImageSplitter(ocr_engine)

    output_step2 = os.path.join(output_base_dir, "step2")
    os.makedirs(output_step2, exist_ok=True)

    left_image, right_image = splitter.split_horizontal(page1_image)

    # 保存左右侧图片
    left_path = os.path.join(output_step2, f"{pdf_name}_left.png")
    right_path = os.path.join(output_step2, f"{pdf_name}_right.png")
    cv2.imwrite(left_path, left_image)
    cv2.imwrite(right_path, right_image)

    logger.info(f"✓ 左侧图片: {left_image.shape[1]}x{left_image.shape[0]}px")
    logger.info(f"✓ 右侧图片: {right_image.shape[1]}x{right_image.shape[0]}px")

    # ============================================================
    # Step 3: 提取关键词Y坐标
    # ============================================================
    logger.info("\n【Step 3】提取关键词Y坐标")
    logger.info("-" * 60)

    keyword_map, ocr_results = splitter.extract_keywords_positions(left_image)

    # 转换为list格式用于LeftSectionCutter
    keywords = []
    for section_type, kw_dict in keyword_map.items():
        for kw_text, y_coord in kw_dict.items():
            keywords.append((section_type, kw_text, y_coord))

    logger.info(f"✓ 识别到 {len(keywords)} 个关键词")
    for kw_type, kw_text, y_coord in keywords:
        logger.info(f"  [{kw_type}] {kw_text}: Y={y_coord}")

    # ============================================================
    # Step 4: 左侧图片板块切分
    # ============================================================
    logger.info("\n【Step 4】左侧图片板块切分")
    logger.info("-" * 60)

    output_step4 = os.path.join(output_base_dir, "step4")
    os.makedirs(output_step4, exist_ok=True)

    left_cutter = LeftSectionCutter()
    # 先计算板块范围
    section_ranges = left_cutter.calculate_section_ranges(keyword_map, left_image.shape[0])
    # 切分并保存板块，同时读取为numpy数组
    section_paths = left_cutter.cut_sections(left_image, section_ranges, output_step4, pdf_name)

    # 读取所有板块图片为numpy数组
    section_images = {}
    for section_name, section_path in section_paths.items():
        section_images[section_name] = cv2.imread(section_path)

    logger.info(f"✓ 切分完成，共 {len(section_images)} 个板块")

    # ============================================================
    # Step 5: 左侧OCR识别各板块
    # ============================================================
    logger.info("\n【Step 5】左侧OCR识别各板块")
    logger.info("-" * 60)

    left_ocr = LeftSectionOCR(ocr_engine)
    left_data = left_ocr.process_all_sections(section_images)

    # ============================================================
    # Step 6: 右侧付款详情OCR识别
    # ============================================================
    logger.info("\n【Step 6】右侧付款详情OCR识别")
    logger.info("-" * 60)

    right_ocr = RightSectionOCR(ocr_engine)
    right_data = right_ocr.process_right_image(right_image)

    # ============================================================
    # Step 7: 整合左右侧数据
    # ============================================================
    logger.info("\n【Step 7】整合左右侧数据")
    logger.info("-" * 60)

    # 构建完整的JSON数据结构
    complete_data = {
        "pdf_filename": pdf_name,
        "left_section": left_data,
        "right_section": right_data
    }

    # 保存完整JSON
    output_step7 = os.path.join(output_base_dir, "step7_final")
    os.makedirs(output_step7, exist_ok=True)

    complete_json_path = os.path.join(output_step7, f"{pdf_name}_complete_data.json")
    with open(complete_json_path, 'w', encoding='utf-8') as f:
        json.dump(complete_data, f, ensure_ascii=False, indent=2)

    logger.info(f"✓ 完整JSON已保存: {complete_json_path}")

    # ============================================================
    # 流程完成
    # ============================================================
    logger.info("\n" + "=" * 80)
    logger.info("流水线测试完成 (Steps 1-6)")
    logger.info("=" * 80)
    logger.info(f"输出目录: {output_base_dir}")
    logger.info(f"完整JSON: {complete_json_path}")
    logger.info("\n运行验证脚本查看结果：")
    logger.info(f"  cat {complete_json_path}")
    logger.info("=" * 80)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python scripts/test_full_pipeline_complete.py <PDF文件路径>")
        print("示例: python scripts/test_full_pipeline_complete.py PdfData/MP_01142025_statement_summary.pdf")
        sys.exit(1)

    pdf_path = sys.argv[1]
    test_full_pipeline(pdf_path)
