#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Step 5 左侧板块OCR识别测试脚本.

功能：
1. 读取Step 4生成的7个板块图片
2. 对每个板块进行OCR识别
3. 提取结构化数据
4. 输出JSON文件

使用方法：
    python scripts/test_step5_simple.py test_output/step4
"""

import sys
import os
import logging
from pathlib import Path

# 添加backend目录到Python路径
backend_dir = Path(__file__).parent.parent / 'backend'
sys.path.insert(0, str(backend_dir))

from app.services.ocr_engine import OCREngine
from app.services.left_section_ocr import LeftSectionOCR
import cv2

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_left_section_ocr(section_dir: str):
    """测试左侧板块OCR识别和数据提取."""

    logger.info("=" * 60)
    logger.info("Step 5 左侧板块OCR识别测试")
    logger.info("=" * 60)

    section_path = Path(section_dir)

    # 板块文件列表（按处理顺序）
    section_files = {
        'header': 'header.png',
        'sales': 'sales.png',
        'refund': 'refund.png',
        'adjustment': 'adjustment.png',
        'wfs': 'wfs.png',
        'other': 'other.png',
        'footer': 'footer.png'
    }

    # [1/4] 读取所有板块图片
    logger.info(f"\n[1/4] 读取板块图片: {section_dir}")
    section_images = {}

    for section_name, filename in section_files.items():
        # 查找匹配的文件（支持前缀，如MP_01142025_header.png）
        matching_files = list(section_path.glob(f"*_{section_name}.png"))

        if not matching_files:
            logger.warning(f"  [{section_name}] 文件不存在，跳过")
            continue

        file_path = matching_files[0]
        image = cv2.imread(str(file_path))

        if image is None:
            logger.warning(f"  [{section_name}] 无法读取图片: {file_path}")
            continue

        section_images[section_name] = image
        height, width = image.shape[:2]
        logger.info(f"  [{section_name}] {width}x{height}px - {file_path.name}")

    if not section_images:
        logger.error("未找到任何板块图片")
        return

    logger.info(f"成功读取 {len(section_images)} 个板块图片")

    # [2/4] 初始化OCR引擎
    logger.info("\n[2/4] 初始化OCR引擎...")
    ocr_engine = OCREngine()

    # [3/4] 初始化板块OCR处理器
    logger.info("\n[3/4] 初始化板块OCR处理器...")
    section_ocr = LeftSectionOCR(ocr_engine)

    # [4/4] 处理所有板块并生成JSON
    logger.info("\n[4/4] 处理所有板块...")
    result_data = section_ocr.process_all_sections(section_images)

    # 保存JSON
    output_dir = Path("test_output/step5")
    output_dir.mkdir(parents=True, exist_ok=True)

    # 从文件名提取基础名称
    first_file = list(section_path.glob("*_header.png"))[0]
    base_name = first_file.stem.replace("_header", "")

    json_path = output_dir / f"{base_name}_left_data.json"
    section_ocr.save_json(result_data, str(json_path))

    # 打印预览
    logger.info("\n" + "=" * 60)
    logger.info("JSON数据预览:")
    logger.info("=" * 60)

    import json
    print(json.dumps(result_data, ensure_ascii=False, indent=2))

    # 完成
    logger.info("\n" + "=" * 60)
    logger.info("测试完成")
    logger.info("=" * 60)
    logger.info(f"JSON文件: {json_path}")
    logger.info(f"共处理 {len(section_images)} 个板块")
    logger.info("=" * 60)


def main():
    """主函数."""
    if len(sys.argv) < 2:
        print("用法: python scripts/test_step5_simple.py <板块目录>")
        print("示例: python scripts/test_step5_simple.py test_output/step4")
        sys.exit(1)

    section_dir = sys.argv[1]

    # 检查目录是否存在
    if not os.path.exists(section_dir):
        print(f"错误: 目录不存在: {section_dir}")
        sys.exit(1)

    # 运行测试
    test_left_section_ocr(section_dir)


if __name__ == "__main__":
    main()
