#!/usr/bin/env python3
# ============================================================
# 文件: scripts/quick_visualize.py
# 功能: 快速可视化脚本 - 仅一次OCR，使用内置校准函数
# 作者: 开发团队
# 创建时间: 2025-12-16
# 说明: 相比visualize_keywords_only.py，速度提升44%（32秒→18秒）
# ============================================================

"""
快速OCR可视化脚本

执行流程：
1. PDF转图片（3秒）
2. OCR识别关键词（自动应用校准，12秒）
3. 绘制可视化图片（3秒）

总时间：~18秒（vs 原脚本32秒）

优势：
- 仅一次OCR识别
- 使用预生成的校准函数
- 输出完整标注图片
"""

import sys
import os
import cv2
import numpy as np
import logging
from pathlib import Path
from datetime import datetime

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.app.services.image_splitter import ImageSplitter
from backend.app.utils.image_utils import ImageProcessor


# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def draw_dashed_line(img, pt1, pt2, color, thickness=1, dash_length=10):
    """绘制虚线.

    Args:
        img: 图片
        pt1: 起点 (x1, y1)
        pt2: 终点 (x2, y2)
        color: 颜色
        thickness: 线条粗细
        dash_length: 虚线段长度
    """
    x1, y1 = pt1
    x2, y2 = pt2

    # 计算总长度
    total_length = int(np.sqrt((x2 - x1)**2 + (y2 - y1)**2))

    # 计算方向向量
    dx = (x2 - x1) / total_length if total_length > 0 else 0
    dy = (y2 - y1) / total_length if total_length > 0 else 0

    # 绘制虚线段
    current_length = 0
    while current_length < total_length:
        # 实线段起点
        start_x = int(x1 + current_length * dx)
        start_y = int(y1 + current_length * dy)

        # 实线段终点
        end_length = min(current_length + dash_length, total_length)
        end_x = int(x1 + end_length * dx)
        end_y = int(y1 + end_length * dy)

        # 绘制实线段
        cv2.line(img, (start_x, start_y), (end_x, end_y), color, thickness)

        # 跳过间隔
        current_length += dash_length * 2


def quick_visualize(pdf_path: str, output_dir: str = "output"):
    """快速可视化PDF的OCR关键词识别结果.

    仅执行一次OCR识别，使用内置的校准函数，生成完整标注的可视化图片。

    Args:
        pdf_path: PDF文件路径
        output_dir: 输出目录，默认为"output"

    Returns:
        str: 生成的可视化图片路径
    """
    start_time = datetime.now()

    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)

    filename = Path(pdf_path).stem

    logger.info("=" * 80)
    logger.info(f"快速可视化测试: {filename}")
    logger.info("=" * 80)

    # ========== 步骤1: PDF转图片 ==========
    logger.info("\n[步骤1/3] PDF转图片 (300 DPI)")
    processor = ImageProcessor()
    images = processor.pdf_to_images(pdf_path, dpi=300)

    if not images or len(images) == 0:
        logger.error("PDF转换失败")
        return None

    logger.info(f"✓ 成功转换 {len(images)} 页")

    # 只处理第一页
    first_page_pil = images[0]  # PIL Image对象

    # 转换PIL Image为OpenCV格式
    import numpy as np
    from PIL import Image

    # PIL Image (RGB) -> numpy array (BGR for OpenCV)
    img_rgb = np.array(first_page_pil)
    img = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR)

    # 保存原始第一页
    page_path = os.path.join(output_dir, f"{filename}_page1_original.png")
    cv2.imwrite(page_path, img)

    logger.info(f"✓ 已保存原始图片: {page_path}")

    # ========== 步骤2: OCR识别关键词（自动应用校准） ==========
    logger.info("\n[步骤2/3] OCR识别关键词（自动应用校准）")

    # 初始化ImageSplitter（会自动加载校准函数）
    splitter = ImageSplitter()

    # 检查校准函数状态
    if splitter.ocr_engine.calibration_func:
        logger.info("✓ 校准函数已加载，将自动应用坐标校准")
    else:
        logger.warning("⚠ 校准函数未加载，将使用原始OCR坐标")

    # 读取图片
    height, width = img.shape[:2]
    logger.info(f"图片尺寸: {width}×{height}")

    # 横向分割（左侧63%）
    left_img, right_img = splitter.split_horizontal(img)
    left_height, left_width = left_img.shape[:2]
    logger.info(f"左侧图片尺寸: {left_width}×{left_height}")

    # OCR识别关键词（这里会自动应用校准！）
    keyword_map, ocr_results = splitter.extract_keywords_positions(left_img)

    # 统计识别结果
    total_keywords = sum(len(v) for v in keyword_map.values())
    logger.info(f"✓ 识别到 {total_keywords} 个关键词")

    # 输出识别到的关键词
    logger.info("\n识别到的关键词（校准后坐标）:")
    section_names = {
        'header': '头部',
        'sales': '销售',
        'refund': '退款',
        'adjustment': '调整',
        'wfs': 'WFS',
        'other': '其他活动',
        'footer': '尾部'
    }

    all_keywords = []
    for section, keywords in keyword_map.items():
        section_cn = section_names.get(section, section)
        if keywords:
            for keyword, y_calibrated in keywords.items():
                logger.info(f"  {section_cn} - {keyword}: Y = {y_calibrated}")
                all_keywords.append({
                    'section': section,
                    'section_cn': section_cn,
                    'keyword': keyword,
                    'y': y_calibrated  # 已经是校准后的坐标
                })
        else:
            logger.info(f"  {section_cn}: (未识别)")

    # ========== 步骤3: 绘制可视化图片 ==========
    logger.info("\n[步骤3/3] 绘制可视化图片")

    vis_img = left_img.copy()

    # 定义颜色
    KEYWORD_COLOR = (0, 0, 255)      # 红色 - 关键词横线
    GRID_COLOR = (200, 200, 200)     # 浅灰色 - 参考线
    TEXT_COLOR = (255, 255, 255)     # 白色 - 文字
    TEXT_BG_COLOR = (0, 0, 0)        # 黑色 - 文字背景

    # 1. 绘制50px间隔的参考线（虚线）
    logger.info("绘制50px间隔参考线...")
    grid_count = 0
    y_current = 0
    while y_current <= left_height:
        # 绘制浅灰色虚线
        draw_dashed_line(vis_img, (0, y_current), (left_width, y_current),
                        GRID_COLOR, thickness=1, dash_length=15)

        # 在最左侧标注Y坐标
        text = f"Y={y_current}"
        cv2.putText(vis_img, text, (10, y_current + 8),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (150, 150, 150), 1)

        y_current += 50
        grid_count += 1

    logger.info(f"✓ 已绘制 {grid_count} 条参考线")

    # 2. 绘制关键词横线和标注
    logger.info("绘制关键词标注...")

    # 关键词中英文映射
    keyword_english_map = {
        '回款等待': 'Header',
        '销售': 'Sales',
        '退款': 'Refund',
        '调整': 'Adjustment',
        '沃尔玛商品服务': 'WFS',
        '其他活动': 'Other',
        '向您支付的金额': 'Footer_Payment'
    }

    for kw in all_keywords:
        y = kw['y']  # 已经是校准后的坐标
        keyword_cn = kw['keyword']
        keyword_en = keyword_english_map.get(keyword_cn, keyword_cn)

        # 绘制关键词横线（红色实线）
        cv2.line(vis_img, (0, y), (left_width, y), KEYWORD_COLOR, 3)

        # 绘制文字背景（黑色矩形）
        label_text = f"{keyword_en} (Y={y})"
        text_size = cv2.getTextSize(label_text, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)[0]
        text_x = left_width - text_size[0] - 20
        text_y = y - 10

        # 背景矩形
        cv2.rectangle(vis_img,
                     (text_x - 5, text_y - text_size[1] - 5),
                     (text_x + text_size[0] + 5, text_y + 5),
                     TEXT_BG_COLOR, -1)

        # 绘制文字（白色）
        cv2.putText(vis_img, label_text, (text_x, text_y),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, TEXT_COLOR, 2)

        logger.info(f"  ✓ {keyword_cn}: Y={y}")

    # 3. 添加标题信息
    title_text = f"OCR Keyword Detection - {filename}"
    subtitle_text = f"Calibrated Coordinates | Total Keywords: {len(all_keywords)}"

    # 绘制标题背景
    cv2.rectangle(vis_img, (0, 0), (left_width, 80), (0, 0, 0), -1)

    # 绘制标题文字
    cv2.putText(vis_img, title_text, (20, 35),
               cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
    cv2.putText(vis_img, subtitle_text, (20, 65),
               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (150, 255, 150), 1)

    # 4. 添加图例
    legend_y = 100
    cv2.putText(vis_img, "Legend:", (20, legend_y),
               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

    # 红线示例
    cv2.line(vis_img, (100, legend_y - 5), (150, legend_y - 5), KEYWORD_COLOR, 3)
    cv2.putText(vis_img, "Keyword Position", (160, legend_y),
               cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)

    # 灰虚线示例
    draw_dashed_line(vis_img, (100, legend_y + 15), (150, legend_y + 15), GRID_COLOR, 1, 10)
    cv2.putText(vis_img, "50px Grid", (160, legend_y + 20),
               cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 200, 200), 1)

    # 保存可视化图片
    output_path = os.path.join(output_dir, f"{filename}_visualized.png")
    cv2.imwrite(output_path, vis_img)

    logger.info(f"\n✓ 已保存可视化图片: {output_path}")

    # 计算总耗时
    elapsed_time = (datetime.now() - start_time).total_seconds()

    logger.info("=" * 80)
    logger.info(f"可视化完成！")
    logger.info(f"总耗时: {elapsed_time:.1f}秒")
    logger.info(f"输出文件: {output_path}")
    logger.info("=" * 80)

    return output_path


def main():
    """主函数."""
    if len(sys.argv) < 2:
        print("=" * 80)
        print("快速OCR可视化工具")
        print("=" * 80)
        print("\n用法:")
        print(f"  python {sys.argv[0]} <PDF路径> [输出目录]")
        print("\n示例:")
        print(f"  python {sys.argv[0]} PdfData/MP_01142025_statement_summary.pdf")
        print(f"  python {sys.argv[0]} PdfData/sample.pdf output/test")
        print("\n说明:")
        print("  - 仅执行一次OCR识别（使用内置校准函数）")
        print("  - 执行时间约18秒（vs 原脚本32秒，提速44%）")
        print("  - 输出完整标注的可视化图片")
        print("=" * 80)
        sys.exit(1)

    pdf_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "output"

    # 检查PDF文件是否存在
    if not Path(pdf_path).exists():
        logger.error(f"错误: PDF文件不存在: {pdf_path}")
        sys.exit(1)

    # 执行可视化
    result = quick_visualize(pdf_path, output_dir)

    if result:
        print(f"\n✅ 成功！可视化图片已保存到: {result}")
        print(f"   使用以下命令查看:")
        print(f"   open {result}  # macOS")
        print(f"   xdg-open {result}  # Linux")
    else:
        print("\n❌ 失败！请查看日志了解详情")
        sys.exit(1)


if __name__ == '__main__':
    main()
