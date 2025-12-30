#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OCR文本行可视化分析脚本.

功能：
1. 对板块图片进行OCR识别
2. 在图片上绘制每行文本的Y坐标线（中心点和右上角）
3. 标注Y坐标值
4. 统计文本行数和Y坐标范围

使用方法：
    python scripts/visualize_ocr_lines.py test_output_grayscale/step4/MP_01142025_statement_summary_sales.png
"""

import sys
import logging
from pathlib import Path
import cv2
import numpy as np

# 添加backend目录到Python路径
backend_dir = Path(__file__).parent.parent / 'backend'
sys.path.insert(0, str(backend_dir))

from app.services.ocr_engine import OCREngine

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def merge_text_blocks_into_lines(ocr_results, y_threshold=30):
    """将OCR识别的文本块按Y坐标合并成文本行.

    Args:
        ocr_results: OCR识别结果列表
            [
                [[x1,y1], [x2,y2], [x3,y3], [x4,y4]],  # 坐标
                ('文本', 置信度)
            ]
        y_threshold: Y坐标阈值（像素），小于此值的块认为是同一行

    Returns:
        List[Dict]: 文本行列表
            [
                {
                    'text': '完整文本行',
                    'y_center': 中心Y坐标,
                    'y_top': 顶部Y坐标,
                    'y_bottom': 底部Y坐标,
                    'x_left': 左侧X坐标,
                    'x_right': 右侧X坐标,
                    'blocks': [原始文本块列表]
                }
            ]
    """
    if not ocr_results:
        return []

    # 提取所有文本块信息
    blocks = []
    for item in ocr_results:
        if len(item) >= 2:
            coords = item[0]  # [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
            text_info = item[1]  # ('文本', 置信度)

            if isinstance(text_info, tuple) and len(text_info) >= 1:
                text = text_info[0]
                confidence = text_info[1] if len(text_info) > 1 else 0.0

                # 计算边界框
                xs = [pt[0] for pt in coords]
                ys = [pt[1] for pt in coords]
                x_min, x_max = min(xs), max(xs)
                y_min, y_max = min(ys), max(ys)
                y_center = (y_min + y_max) / 2

                blocks.append({
                    'text': text,
                    'confidence': confidence,
                    'y_center': y_center,
                    'y_top': y_min,
                    'y_bottom': y_max,
                    'x_left': x_min,
                    'x_right': x_max,
                    'coords': coords
                })

    if not blocks:
        return []

    # 按Y坐标排序
    blocks.sort(key=lambda b: b['y_center'])

    # 合并相近Y坐标的块
    lines = []
    current_line_blocks = [blocks[0]]
    current_y = blocks[0]['y_center']

    for block in blocks[1:]:
        y_diff = abs(block['y_center'] - current_y)

        if y_diff <= y_threshold:
            # 同一行
            current_line_blocks.append(block)
        else:
            # 新行，保存当前行
            lines.append(create_line_from_blocks(current_line_blocks))
            current_line_blocks = [block]
            current_y = block['y_center']

    # 保存最后一行
    if current_line_blocks:
        lines.append(create_line_from_blocks(current_line_blocks))

    return lines


def create_line_from_blocks(blocks):
    """从文本块列表创建文本行.

    Args:
        blocks: 文本块列表

    Returns:
        Dict: 文本行信息
    """
    # 按X坐标排序（从左到右）
    blocks.sort(key=lambda b: b['x_left'])

    # 合并文本（用空格连接）
    text = ' '.join(b['text'] for b in blocks)

    # 计算行的边界
    y_centers = [b['y_center'] for b in blocks]
    y_tops = [b['y_top'] for b in blocks]
    y_bottoms = [b['y_bottom'] for b in blocks]
    x_lefts = [b['x_left'] for b in blocks]
    x_rights = [b['x_right'] for b in blocks]

    return {
        'text': text,
        'y_center': sum(y_centers) / len(y_centers),
        'y_top': min(y_tops),
        'y_bottom': max(y_bottoms),
        'x_left': min(x_lefts),
        'x_right': max(x_rights),
        'blocks': blocks
    }


def visualize_ocr_lines(image_path: str, output_dir: str = None):
    """可视化OCR文本行识别结果.

    Args:
        image_path: 输入图片路径
        output_dir: 输出目录（可选，默认与输入同目录）
    """
    logger.info("=" * 80)
    logger.info("OCR文本行可视化分析")
    logger.info("=" * 80)

    # 读取图片
    image_path_obj = Path(image_path)
    if not image_path_obj.exists():
        logger.error(f"文件不存在: {image_path}")
        return

    logger.info(f"输入图片: {image_path_obj.name}")

    image = cv2.imread(str(image_path_obj))
    if image is None:
        logger.error("无法读取图片")
        return

    height, width = image.shape[:2]
    logger.info(f"图片尺寸: {width}x{height}px")

    # OCR识别
    logger.info("\n执行OCR识别...")
    ocr_engine = OCREngine()
    ocr_results = ocr_engine.recognize_image(image)

    if not ocr_results:
        logger.warning("OCR未识别到文本")
        return

    logger.info(f"识别到 {len(ocr_results)} 个文本块")

    # 合并成文本行
    logger.info("\n合并文本块为文本行...")
    lines = merge_text_blocks_into_lines(ocr_results, y_threshold=30)
    logger.info(f"合并为 {len(lines)} 个文本行")

    # 创建可视化图片（在原图上绘制）
    vis_image = image.copy()

    # 绘制设置
    COLOR_CENTER = (0, 255, 0)      # 绿色：中心线
    COLOR_TOP_RIGHT = (255, 0, 0)   # 蓝色：右上角线
    COLOR_TEXT = (0, 0, 255)        # 红色：文字标注
    LINE_THICKNESS = 2
    FONT = cv2.FONT_HERSHEY_SIMPLEX
    FONT_SCALE = 0.5
    FONT_THICKNESS = 1

    logger.info("\n绘制可视化标注...")
    logger.info("-" * 80)
    logger.info(f"{'行号':<6} {'Y中心':<8} {'Y顶部':<8} {'Y底部':<8} {'文本内容'}")
    logger.info("-" * 80)

    # 统计信息
    y_centers = []
    y_tops = []
    y_bottoms = []

    for i, line in enumerate(lines, 1):
        y_center = int(line['y_center'])
        y_top = int(line['y_top'])
        y_bottom = int(line['y_bottom'])
        x_left = int(line['x_left'])
        x_right = int(line['x_right'])
        text = line['text']

        # 记录坐标
        y_centers.append(y_center)
        y_tops.append(y_top)
        y_bottoms.append(y_bottom)

        # 绘制中心线（绿色，横跨整个图片宽度）
        cv2.line(vis_image, (0, y_center), (width, y_center), COLOR_CENTER, LINE_THICKNESS)

        # 绘制右上角线（蓝色，从右上角向左延伸）
        cv2.line(vis_image, (x_right, y_top), (width, y_top), COLOR_TOP_RIGHT, LINE_THICKNESS)

        # 标注Y坐标（在图片右侧）
        label_x = width - 100
        label_center = f"C:{y_center}"
        label_top = f"T:{y_top}"

        # 绘制中心Y坐标标注
        cv2.putText(vis_image, label_center, (label_x, y_center - 5),
                    FONT, FONT_SCALE, COLOR_CENTER, FONT_THICKNESS)

        # 绘制顶部Y坐标标注
        cv2.putText(vis_image, label_top, (label_x, y_top - 5),
                    FONT, FONT_SCALE, COLOR_TOP_RIGHT, FONT_THICKNESS)

        # 在文本左侧标注行号
        line_num_label = f"#{i}"
        cv2.putText(vis_image, line_num_label, (5, y_center),
                    FONT, FONT_SCALE, COLOR_TEXT, FONT_THICKNESS)

        # 打印统计信息
        logger.info(f"#{i:<5} {y_center:<8} {y_top:<8} {y_bottom:<8} {text}")

    # 统计汇总
    logger.info("-" * 80)
    logger.info(f"\n统计汇总:")
    logger.info(f"  文本行总数: {len(lines)}")
    logger.info(f"  Y坐标范围（中心点）: {min(y_centers)} ~ {max(y_centers)}")
    logger.info(f"  Y坐标范围（顶部）: {min(y_tops)} ~ {max(y_tops)}")
    logger.info(f"  Y坐标范围（底部）: {min(y_bottoms)} ~ {max(y_bottoms)}")
    logger.info(f"  图片总高度: {height}px")

    # 保存可视化图片
    if output_dir is None:
        output_dir = image_path_obj.parent
    else:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

    output_filename = f"{image_path_obj.stem}_ocr_lines_vis.png"
    output_path = output_dir / output_filename

    cv2.imwrite(str(output_path), vis_image)
    logger.info(f"\n可视化图片已保存: {output_path}")

    # 创建图例说明
    legend_height = 150
    legend_image = np.ones((legend_height, width, 3), dtype=np.uint8) * 255

    legend_text = [
        "图例说明:",
        "  绿色横线 = 文本行中心Y坐标",
        "  蓝色横线 = 文本行顶部Y坐标（从右上角开始）",
        "  C:xxx = 中心Y坐标",
        "  T:xxx = 顶部Y坐标",
        "  #n = 行号"
    ]

    for i, text in enumerate(legend_text):
        y_pos = 30 + i * 20
        cv2.putText(legend_image, text, (10, y_pos),
                    FONT, FONT_SCALE, (0, 0, 0), FONT_THICKNESS)

    # 保存图例
    legend_path = output_dir / f"{image_path_obj.stem}_legend.png"
    cv2.imwrite(str(legend_path), legend_image)
    logger.info(f"图例说明已保存: {legend_path}")

    logger.info("\n" + "=" * 80)
    logger.info("分析完成")
    logger.info("=" * 80)


def main():
    """主函数."""
    if len(sys.argv) < 2:
        print("用法: python scripts/visualize_ocr_lines.py <图片文件路径> [输出目录]")
        print("示例: python scripts/visualize_ocr_lines.py test_output_grayscale/step4/MP_01142025_statement_summary_sales.png")
        sys.exit(1)

    image_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else None

    visualize_ocr_lines(image_path, output_dir)


if __name__ == "__main__":
    main()
