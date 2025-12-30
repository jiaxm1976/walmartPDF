#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ============================================================
# 文件: scripts/test_direct_extraction.py
# 功能: 测试直接关键词定位提取策略并生成可视化标注
# 作者: 开发团队
# 创建时间: 2025-12-18
# ============================================================

"""
测试直接关键词定位提取策略并生成可视化标注.

功能：
1. 读取PDF并转为图片
2. 横向分割左右两侧
3. 使用新的DirectKeywordExtractor提取数据
4. 在左侧图片上绘制关键词位置和板块范围边界
5. 保存可视化结果和JSON数据
"""

import sys
import logging
from pathlib import Path
import json

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

import cv2
import numpy as np
from pdf2image import convert_from_path

from backend.app.services.ocr_engine import OCREngine
from backend.app.services.direct_keyword_extractor import DirectKeywordExtractor

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def pdf_to_image(pdf_path: str, dpi: int = 300) -> np.ndarray:
    """将PDF第一页转为图片.

    Args:
        pdf_path: PDF文件路径
        dpi: 分辨率

    Returns:
        np.ndarray: 图片数组（BGR格式）
    """
    logger.info(f"转换PDF为图片: {pdf_path} (DPI={dpi})")
    images = convert_from_path(pdf_path, dpi=dpi, first_page=1, last_page=1)

    # 转换为numpy数组
    image = np.array(images[0])
    # RGB -> BGR (OpenCV格式)
    image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

    logger.info(f"图片尺寸: {image.shape[1]}x{image.shape[0]}")
    return image


def split_horizontal(image: np.ndarray, split_ratio: float = 0.63) -> tuple:
    """横向分割图片.

    Args:
        image: 输入图片
        split_ratio: 分割比例

    Returns:
        (left_image, right_image)
    """
    height, width = image.shape[:2]
    split_x = int(width * split_ratio)

    left_image = image[0:height, 0:split_x]
    right_image = image[0:height, split_x:width]

    logger.info(f"横向分割完成 - 左侧: {left_image.shape}, 右侧: {right_image.shape}")
    return left_image, right_image


def visualize_annotations(
    left_image: np.ndarray,
    keyword_positions: dict,
    section_ranges: dict,
    text_blocks: list,
    output_path: str
) -> str:
    """在左侧图片上绘制关键词位置、板块范围和文本框.

    Args:
        left_image: 左侧图片
        keyword_positions: 关键词Y坐标字典
        section_ranges: 板块范围字典
        text_blocks: OCR识别的所有文本块列表
        output_path: 输出路径

    Returns:
        str: 输出文件路径
    """
    logger.info("生成可视化标注图片")

    # 复制图片（避免修改原图）
    vis_image = left_image.copy()
    height, width = vis_image.shape[:2]

    # 定义颜色和样式
    KEYWORD_COLOR = (0, 0, 255)      # 红色 - 关键词位置
    RANGE_COLOR = (0, 255, 0)        # 绿色 - 板块范围边界
    BOX_COLOR = (255, 0, 0)          # 蓝色 - 文本框
    KEYWORD_THICKNESS = 3
    RANGE_THICKNESS = 2
    BOX_THICKNESS = 2
    FONT = cv2.FONT_HERSHEY_SIMPLEX
    FONT_SCALE = 0.5
    FONT_THICKNESS = 1

    # 板块中文名称映射
    section_names_cn = {
        'header': '回款等待',
        'sales': '销售',
        'refund': '退款',
        'adjustment': '调整',
        'wfs': 'WFS',
        'other': '其他活动',
        'footer': '向您支付的金额'
    }

    # 1. 绘制所有文本框和坐标标注（底层）
    logger.info("  绘制文本框和坐标标注")
    for block in text_blocks:
        # 提取四角坐标
        box = block['box']
        x1, y1 = int(box[0][0]), int(box[0][1])
        x2, y2 = int(box[1][0]), int(box[1][1])
        x3, y3 = int(box[2][0]), int(box[2][1])
        x4, y4 = int(box[3][0]), int(box[3][1])

        # 绘制蓝色矩形框
        pts = np.array([[x1, y1], [x2, y2], [x3, y3], [x4, y4]], np.int32)
        pts = pts.reshape((-1, 1, 2))
        cv2.polylines(vis_image, [pts], True, BOX_COLOR, BOX_THICKNESS)

        # 在文本框左侧标注左上角坐标 (x1, y1)
        coord_label = f"({x1},{y1})"
        # 文字位置：左上角左侧
        text_x = max(5, x1 - 80)  # 确保不超出图片边界
        text_y = y1

        # 绘制白色背景（提高可读性）
        text_size = cv2.getTextSize(coord_label, FONT, FONT_SCALE, FONT_THICKNESS)[0]
        cv2.rectangle(vis_image,
                     (text_x - 2, text_y - text_size[1] - 2),
                     (text_x + text_size[0] + 2, text_y + 2),
                     (255, 255, 255), -1)

        # 绘制坐标文字
        cv2.putText(vis_image, coord_label, (text_x, text_y),
                   FONT, FONT_SCALE, BOX_COLOR, FONT_THICKNESS)

    # 2. 绘制板块范围边界（绿色横线，中层）
    logger.info("  绘制板块范围边界")
    for section_name, (start_y, end_y) in section_ranges.items():
        # 绘制起始边界（绿色虚线）
        for x in range(0, width, 20):  # 虚线效果
            cv2.line(vis_image, (x, start_y), (min(x + 10, width), start_y),
                    RANGE_COLOR, RANGE_THICKNESS)

        # 绘制结束边界（绿色虚线）
        for x in range(0, width, 20):
            cv2.line(vis_image, (x, end_y), (min(x + 10, width), end_y),
                    RANGE_COLOR, RANGE_THICKNESS)

        # 添加范围标注（右侧）
        cn_name = section_names_cn.get(section_name, section_name)
        range_label = f"[{cn_name}] {start_y}-{end_y} ({end_y-start_y}px)"

        # 文字位置：板块中间靠右侧
        text_x = width - 350
        text_y = int((start_y + end_y) / 2)

        # 绘制背景矩形（提高可读性）
        text_size = cv2.getTextSize(range_label, FONT, 0.7, 2)[0]
        cv2.rectangle(vis_image,
                     (text_x - 5, text_y - text_size[1] - 5),
                     (text_x + text_size[0] + 5, text_y + 5),
                     (255, 255, 255), -1)

        # 绘制文字
        cv2.putText(vis_image, range_label, (text_x, text_y),
                   FONT, 0.7, RANGE_COLOR, 2)

    # 3. 绘制关键词位置（红色横线，顶层）
    logger.info("  绘制关键词位置线")
    for section_name, y_coord in keyword_positions.items():
        # 绘制红色横线
        cv2.line(vis_image, (0, y_coord), (width, y_coord), KEYWORD_COLOR, KEYWORD_THICKNESS)

        # 添加文字标注（左侧）
        cn_name = section_names_cn.get(section_name, section_name)
        label_text = f"{cn_name}: Y={y_coord}"

        # 文字位置：左侧
        text_x = 20
        text_y = y_coord - 15

        # 绘制背景矩形
        text_size = cv2.getTextSize(label_text, FONT, 0.7, 2)[0]
        cv2.rectangle(vis_image,
                     (text_x - 5, text_y - text_size[1] - 5),
                     (text_x + text_size[0] + 5, text_y + 5),
                     (255, 255, 255), -1)

        # 绘制文字（红色）
        cv2.putText(vis_image, label_text, (text_x, text_y),
                   FONT, 0.7, KEYWORD_COLOR, 2)

    # 4. 保存图片
    cv2.imwrite(output_path, vis_image)
    logger.info(f"可视化图片已保存: {output_path}")

    return output_path


def main():
    """主函数."""
    if len(sys.argv) < 2:
        print("用法: python test_direct_extraction.py <PDF文件路径>")
        sys.exit(1)

    pdf_path = sys.argv[1]

    # 检查文件是否存在
    if not Path(pdf_path).exists():
        logger.error(f"文件不存在: {pdf_path}")
        sys.exit(1)

    # 创建输出目录
    output_dir = Path(__file__).parent / "test" / "test-output"
    output_dir.mkdir(parents=True, exist_ok=True)

    # 获取文件名（不含扩展名）
    pdf_name = Path(pdf_path).stem

    logger.info("=" * 80)
    logger.info("开始测试直接关键词定位提取策略")
    logger.info("=" * 80)

    # Step 1: PDF转图片
    image = pdf_to_image(pdf_path, dpi=300)

    # Step 2: 横向分割
    left_image, right_image = split_horizontal(image, split_ratio=0.63)

    # Step 3: 初始化提取器
    ocr_engine = OCREngine()
    extractor = DirectKeywordExtractor(ocr_engine)

    # Step 4: 提取数据
    result_data, keyword_positions, section_ranges, text_blocks = extractor.process_all_sections(left_image)

    # Step 5: 生成可视化标注
    vis_output_path = output_dir / f"{pdf_name}_direct_extraction_annotated.png"
    visualize_annotations(left_image, keyword_positions, section_ranges, text_blocks, str(vis_output_path))

    # Step 6: 保存JSON数据
    json_output_path = output_dir / f"{pdf_name}_direct_extraction.json"
    with open(json_output_path, 'w', encoding='utf-8') as f:
        json.dump(result_data, f, ensure_ascii=False, indent=2)
    logger.info(f"JSON数据已保存: {json_output_path}")

    # Step 7: 输出结果摘要
    logger.info("=" * 80)
    logger.info("提取结果摘要:")
    logger.info("=" * 80)
    for section_name, section_data in result_data.items():
        logger.info(f"  [{section_name}] 字段数量: {len(section_data)}")
        if section_data:
            # 显示前3个字段
            items = list(section_data.items())[:3]
            for key, value in items:
                logger.info(f"    - {key}: {value}")
            if len(section_data) > 3:
                logger.info(f"    ... 共{len(section_data)}个字段")

    logger.info("=" * 80)
    logger.info("测试完成")
    logger.info(f"可视化图片: {vis_output_path}")
    logger.info(f"JSON数据: {json_output_path}")
    logger.info("=" * 80)

    print(f"\n✅ 测试完成！\n")
    print(f"📊 可视化图片: {vis_output_path}")
    print(f"📄 JSON数据: {json_output_path}")


if __name__ == "__main__":
    main()


# ============================================================
# END OF test_direct_extraction.py
# ============================================================
