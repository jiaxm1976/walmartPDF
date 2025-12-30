#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ============================================================
# 文件: scripts/test_step3_keywords.py
# 功能: 测试Step 3关键词识别功能
# 作者: 开发团队
# 创建时间: 2025-12-16
# 说明: 验证关键词Y坐标识别的准确性
# ============================================================

"""
Step 3 关键词识别测试脚本.

测试内容：
1. PDF转图片（Step 1）
2. 横向63%分割（Step 2）
3. 提取关键词Y坐标（Step 3）
4. 保存JSON文件
5. 生成可视化图片（在左侧图片上画Y坐标线）

使用方法：
    python scripts/test_step3_keywords.py PdfData/MP_01142025_statement_summary.pdf
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
from app.utils.image_utils import pdf_to_images

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_step3_keywords(pdf_path: str, output_dir: str = 'test_output/step3'):
    """测试Step 3关键词识别完整流程.

    Args:
        pdf_path: PDF文件路径
        output_dir: 输出目录
    """
    logger.info("=" * 60)
    logger.info("Step 3 关键词识别测试")
    logger.info("=" * 60)

    # 创建输出目录
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # 提取PDF文件名
    pdf_name = Path(pdf_path).stem

    # ========== Step 1: PDF转图片 ==========
    logger.info("\n[Step 1] PDF转图片...")
    images = pdf_to_images(
        pdf_path,
        dpi=300,  # 使用300 DPI
        save_images=False
    )

    if not images:
        logger.error("PDF转换失败，没有生成图片")
        return

    logger.info(f"  成功转换 {len(images)} 页")

    # 只处理第一页（转换为numpy数组）
    import numpy as np
    first_page = np.array(images[0])
    logger.info(f"  第一页尺寸: {first_page.shape}")

    # ========== Step 2: 横向分割 ==========
    logger.info("\n[Step 2] 横向63%分割...")
    ocr_engine = OCREngine()
    splitter = ImageSplitter(ocr_engine)

    left_image, right_image = splitter.split_horizontal(first_page)

    logger.info(f"  左侧图片: {left_image.shape}")
    logger.info(f"  右侧图片: {right_image.shape}")

    # 保存左右图片
    import cv2
    left_path = output_path / f"{pdf_name}_left.png"
    right_path = output_path / f"{pdf_name}_right.png"
    cv2.imwrite(str(left_path), left_image)
    cv2.imwrite(str(right_path), right_image)
    logger.info(f"  已保存: {left_path}")
    logger.info(f"  已保存: {right_path}")

    # ========== Step 3: 提取关键词Y坐标 ==========
    logger.info("\n[Step 3] 提取关键词Y坐标...")
    keyword_map, ocr_results = splitter.extract_keywords_positions(left_image)

    # 打印识别结果
    logger.info("\n识别到的关键词：")
    for section, keywords in keyword_map.items():
        if keywords:
            for keyword, y_coord in keywords.items():
                logger.info(f"  [{section}] {keyword}: Y={y_coord}")
        else:
            logger.warning(f"  [{section}] 未找到关键词")

    # ========== 输出JSON ==========
    logger.info("\n[输出JSON] 保存关键词坐标...")

    # 构建元数据
    metadata = {
        'pdf_name': pdf_name,
        'pdf_path': pdf_path,
        'image_size': {
            'width': int(left_image.shape[1]),
            'height': int(left_image.shape[0])
        },
        'dpi': 300,
        'split_ratio': 0.63
    }

    json_path = output_path / f"{pdf_name}_keywords.json"
    splitter.save_keywords_to_json(
        keyword_map,
        str(json_path),
        metadata=metadata
    )

    logger.info(f"  JSON已保存: {json_path}")

    # ========== 生成可视化图片 ==========
    logger.info("\n[可视化] 在左侧图片上绘制Y坐标线...")

    vis_path = output_path / f"{pdf_name}_keywords_visualization.png"
    splitter.visualize_keywords(
        left_image,
        keyword_map,
        str(vis_path)
    )

    logger.info(f"  可视化图片已保存: {vis_path}")

    # ========== 统计信息 ==========
    logger.info("\n" + "=" * 60)
    logger.info("测试完成")
    logger.info("=" * 60)
    logger.info(f"输出目录: {output_path}")
    logger.info(f"生成文件：")
    logger.info(f"  1. {left_path.name} - 左侧图片")
    logger.info(f"  2. {right_path.name} - 右侧图片")
    logger.info(f"  3. {json_path.name} - 关键词坐标JSON")
    logger.info(f"  4. {vis_path.name} - 可视化图片")
    logger.info("")
    logger.info(f"请检查可视化图片，确认红线是否准确标注在关键词位置")
    logger.info("=" * 60)


def main():
    """主函数."""
    if len(sys.argv) < 2:
        print("用法: python scripts/test_step3_keywords.py <PDF文件路径>")
        print("示例: python scripts/test_step3_keywords.py PdfData/MP_01142025_statement_summary.pdf")
        sys.exit(1)

    pdf_path = sys.argv[1]

    # 检查文件是否存在
    if not os.path.exists(pdf_path):
        print(f"错误: 文件不存在: {pdf_path}")
        sys.exit(1)

    # 运行测试
    test_step3_keywords(pdf_path)


if __name__ == "__main__":
    main()
