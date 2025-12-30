#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ============================================================
# 文件: scripts/batch_test_direct_extraction.py
# 功能: 批量测试直接关键词定位提取策略
# 作者: 开发团队
# 创建时间: 2025-12-18
# ============================================================

"""
批量测试直接关键词定位提取策略.

功能：
1. 自动扫描PdfData目录下的所有PDF文件
2. 对每个PDF执行直接关键词定位提取
3. 生成可视化标注图片
4. 保存JSON数据
5. 输出测试报告
"""

import sys
import logging
from pathlib import Path
import json
from datetime import datetime

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
    """将PDF第一页转为图片."""
    logger.info(f"转换PDF为图片: {pdf_path} (DPI={dpi})")
    images = convert_from_path(pdf_path, dpi=dpi, first_page=1, last_page=1)

    # 转换为numpy数组
    image = np.array(images[0])
    # RGB -> BGR (OpenCV格式)
    image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

    logger.info(f"图片尺寸: {image.shape[1]}x{image.shape[0]}")
    return image


def split_horizontal(image: np.ndarray, split_ratio: float = 0.63) -> tuple:
    """横向分割图片."""
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
    """在左侧图片上绘制关键词位置、板块范围和文本框."""
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
    BOX_THICKNESS = 1
    FONT = cv2.FONT_HERSHEY_SIMPLEX
    FONT_SCALE = 0.4
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
        text_x = max(5, x1 - 70)  # 确保不超出图片边界
        text_y = y1 + 10

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
        text_x = width - 320
        text_y = int((start_y + end_y) / 2)

        # 绘制背景矩形（提高可读性）
        text_size = cv2.getTextSize(range_label, FONT, 0.6, 2)[0]
        cv2.rectangle(vis_image,
                     (text_x - 5, text_y - text_size[1] - 5),
                     (text_x + text_size[0] + 5, text_y + 5),
                     (255, 255, 255), -1)

        # 绘制文字
        cv2.putText(vis_image, range_label, (text_x, text_y),
                   FONT, 0.6, RANGE_COLOR, 2)

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
        text_y = y_coord - 10

        # 绘制背景矩形
        text_size = cv2.getTextSize(label_text, FONT, 0.6, 2)[0]
        cv2.rectangle(vis_image,
                     (text_x - 5, text_y - text_size[1] - 5),
                     (text_x + text_size[0] + 5, text_y + 5),
                     (255, 255, 255), -1)

        # 绘制文字（红色）
        cv2.putText(vis_image, label_text, (text_x, text_y),
                   FONT, 0.6, KEYWORD_COLOR, 2)

    # 4. 保存图片
    cv2.imwrite(output_path, vis_image)
    logger.info(f"可视化图片已保存: {output_path}")

    return output_path


def process_single_pdf(pdf_path: Path, output_dir: Path, extractor: DirectKeywordExtractor) -> dict:
    """处理单个PDF文件.

    Returns:
        dict: 处理结果
            {
                'success': bool,
                'pdf_name': str,
                'sections_found': int,
                'total_fields': int,
                'error': str (if failed)
            }
    """
    pdf_name = pdf_path.stem
    logger.info("=" * 80)
    logger.info(f"处理PDF: {pdf_name}")
    logger.info("=" * 80)

    result = {
        'success': False,
        'pdf_name': pdf_name,
        'sections_found': 0,
        'total_fields': 0
    }

    try:
        # Step 1: PDF转图片
        image = pdf_to_image(str(pdf_path), dpi=300)

        # Step 2: 横向分割
        left_image, right_image = split_horizontal(image, split_ratio=0.63)

        # Step 3: 提取数据
        result_data, keyword_positions, section_ranges, text_blocks = extractor.process_all_sections(left_image)

        # Step 4: 生成可视化标注
        vis_output_path = output_dir / f"{pdf_name}_annotated.png"
        visualize_annotations(left_image, keyword_positions, section_ranges, text_blocks, str(vis_output_path))

        # Step 5: 保存JSON数据
        json_output_path = output_dir / f"{pdf_name}_data.json"
        with open(json_output_path, 'w', encoding='utf-8') as f:
            json.dump(result_data, f, ensure_ascii=False, indent=2)
        logger.info(f"JSON数据已保存: {json_output_path}")

        # 统计结果
        result['success'] = True
        result['sections_found'] = len(result_data)
        result['total_fields'] = sum(len(section_data) for section_data in result_data.values())
        result['vis_path'] = str(vis_output_path)
        result['json_path'] = str(json_output_path)

        logger.info(f"✅ {pdf_name} 处理成功")

    except Exception as e:
        logger.error(f"❌ {pdf_name} 处理失败: {e}", exc_info=True)
        result['error'] = str(e)

    return result


def main():
    """主函数."""
    # 获取PDF目录
    pdf_dir = Path(__file__).parent.parent / "PdfData"

    if not pdf_dir.exists():
        logger.error(f"PDF目录不存在: {pdf_dir}")
        sys.exit(1)

    # 查找所有PDF文件
    pdf_files = list(pdf_dir.glob("*.pdf"))

    if not pdf_files:
        logger.error(f"未找到PDF文件: {pdf_dir}")
        sys.exit(1)

    logger.info(f"找到 {len(pdf_files)} 个PDF文件")

    # 创建输出目录
    output_dir = Path(__file__).parent / "test" / "test-output"
    output_dir.mkdir(parents=True, exist_ok=True)

    # 初始化提取器（提取器会自动创建低置信度阈值的OCR引擎）
    logger.info("=" * 80)
    logger.info("初始化直接关键词提取器")
    logger.info("=" * 80)
    # ⭐ 传入None，让DirectKeywordExtractor自己创建confidence_threshold=0.3的OCR引擎
    # 这样可以识别到置信度较低的"期末余额"金额（confidence=0.3）
    extractor = DirectKeywordExtractor(ocr_engine=None)

    # 批量处理
    logger.info("=" * 80)
    logger.info("开始批量处理")
    logger.info("=" * 80)

    results = []
    start_time = datetime.now()

    for pdf_file in pdf_files:
        result = process_single_pdf(pdf_file, output_dir, extractor)
        results.append(result)

    end_time = datetime.now()
    elapsed = (end_time - start_time).total_seconds()

    # 生成测试报告
    logger.info("=" * 80)
    logger.info("批量测试报告")
    logger.info("=" * 80)

    success_count = sum(1 for r in results if r['success'])
    fail_count = len(results) - success_count

    logger.info(f"总计: {len(results)} 个文件")
    logger.info(f"成功: {success_count} 个")
    logger.info(f"失败: {fail_count} 个")
    logger.info(f"耗时: {elapsed:.2f} 秒")
    logger.info("")

    # 成功的文件详情
    if success_count > 0:
        logger.info("✅ 成功文件:")
        for result in results:
            if result['success']:
                logger.info(f"  - {result['pdf_name']}: {result['sections_found']}个板块, {result['total_fields']}个字段")

    # 失败的文件详情
    if fail_count > 0:
        logger.info("")
        logger.info("❌ 失败文件:")
        for result in results:
            if not result['success']:
                logger.info(f"  - {result['pdf_name']}: {result.get('error', 'Unknown error')}")

    logger.info("=" * 80)
    logger.info("批量测试完成")
    logger.info(f"输出目录: {output_dir}")
    logger.info("=" * 80)

    # 保存测试报告
    report_path = output_dir / f"batch_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'total': len(results),
            'success': success_count,
            'fail': fail_count,
            'elapsed_seconds': elapsed,
            'results': results
        }, f, ensure_ascii=False, indent=2)

    logger.info(f"测试报告已保存: {report_path}")

    print(f"\n{'='*80}")
    print(f"✅ 批量测试完成！")
    print(f"{'='*80}")
    print(f"总计: {len(results)} 个文件")
    print(f"成功: {success_count} 个")
    print(f"失败: {fail_count} 个")
    print(f"耗时: {elapsed:.2f} 秒")
    print(f"输出目录: {output_dir}")
    print(f"测试报告: {report_path}")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    main()


# ============================================================
# END OF batch_test_direct_extraction.py
# ============================================================
