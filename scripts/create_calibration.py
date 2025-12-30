# ============================================================
# 文件: scripts/create_calibration.py
# 功能: 创建OCR校准图片并生成校准函数
# 作者: 开发团队
# 创建时间: 2025-12-14
# 说明: 一次性校准，生成校准函数供后续使用
# ============================================================

import sys
import os
import logging
import numpy as np
import cv2
import pickle
from pathlib import Path
from scipy.interpolate import interp1d

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.app.services.ocr_engine import OCREngine


def create_calibration_image(width: int, height: int, interval: int = 50):
    """创建校准图片.

    纯白色背景，每隔interval像素添加一个Y坐标标注。

    Args:
        width: 图片宽度
        height: 图片高度
        interval: 标注间隔（像素）

    Returns:
        numpy.ndarray: 校准图片
    """
    # 创建白色背景
    img = np.ones((height, width, 3), dtype=np.uint8) * 255

    # 定义文字属性
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.8
    font_thickness = 2
    text_color = (0, 0, 0)  # 黑色

    # 添加Y坐标标注
    for y in range(0, height, interval):
        text = f"Y={y}"

        # 在左侧添加标注（X=50）
        cv2.putText(img, text, (50, y + 8), font, font_scale, text_color, font_thickness)

        # 在中间添加标注（X=width//2），增加识别点
        cv2.putText(img, text, (width // 2, y + 8), font, font_scale, text_color, font_thickness)

        # 在右侧添加标注（X=width-200），进一步增加识别点
        cv2.putText(img, text, (width - 200, y + 8), font, font_scale, text_color, font_thickness)

    return img


def add_geometric_anchors(img, anchor_positions):
    """在图片上添加几何锚点标记.

    Args:
        img: 原始图片
        anchor_positions: 锚点Y坐标列表

    Returns:
        numpy.ndarray: 带几何标记的图片
    """
    img_with_marks = img.copy()

    # 在左侧边缘添加小红色方块
    for y in anchor_positions:
        cv2.rectangle(img_with_marks, (0, y-2), (8, y+2), (0, 0, 255), -1)

    return img_with_marks


def detect_geometric_anchors(img, expected_positions):
    """检测几何锚点的实际位置.

    Args:
        img: 带几何标记的图片
        expected_positions: 预期的Y坐标列表

    Returns:
        list: [(预期Y, 检测到的Y), ...]
    """
    # 提取图片左侧边缘
    left_edge = img[:, 0:15]

    # 检测红色方块
    red_mask = cv2.inRange(left_edge, (0, 0, 200), (50, 50, 255))

    # 找到红色区域的Y坐标
    contours, _ = cv2.findContours(red_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    detected_y = sorted([cv2.boundingRect(c)[1] for c in contours])

    # 匹配预期位置和检测位置
    reference_points = []
    for i, expected in enumerate(expected_positions):
        if i < len(detected_y):
            reference_points.append((expected, detected_y[i]))

    return reference_points


def extract_reference_points_from_ocr(ocr_results):
    """从OCR结果中提取参考点.

    Args:
        ocr_results: OCR识别结果列表

    Returns:
        list: [(标注值, OCR_Y坐标), ...]
    """
    import re
    reference_points = []

    for box, (text, confidence) in ocr_results:
        # 匹配 "Y=数字" 格式
        match = re.match(r'Y=(\d+)', text.strip())
        if match:
            labeled_y = int(match.group(1))  # 标注的Y值
            # 使用box中心Y坐标（修复坐标偏差问题，2025-12-15）
            y_top = box[0][1]      # 顶部Y坐标
            y_bottom = box[2][1]   # 底部Y坐标
            ocr_y = int((y_top + y_bottom) / 2)  # 中心Y坐标
            reference_points.append((labeled_y, ocr_y))

    return sorted(reference_points)  # 按标注值排序


def build_calibration_function(reference_points, logger):
    """建立坐标校准函数.

    Args:
        reference_points: [(标注值, OCR_Y), ...]
        logger: 日志记录器

    Returns:
        function: 输入OCR坐标，输出校准后的真实坐标
    """
    if len(reference_points) < 2:
        logger.error("参考点数量不足，无法建立校准函数")
        return None

    labeled_values = [p[0] for p in reference_points]  # [0, 50, 100, ...]
    ocr_values = [p[1] for p in reference_points]      # [8, 58, 108, ...]

    # 计算偏差统计
    deviations = [ocr - labeled for labeled, ocr in reference_points]
    avg_deviation = np.mean(deviations)
    max_deviation = np.max(np.abs(deviations))
    min_deviation = np.min(np.abs(deviations))

    logger.info(f"\n校准函数统计信息：")
    logger.info(f"  参考点数量: {len(reference_points)}")
    logger.info(f"  平均偏差: {avg_deviation:.2f}px")
    logger.info(f"  最大偏差: {max_deviation:.2f}px")
    logger.info(f"  最小偏差: {min_deviation:.2f}px")

    # 显示部分参考点
    logger.info(f"\n参考点详情（前10个和后5个）：")
    for i, (labeled, ocr) in enumerate(reference_points):
        deviation = ocr - labeled
        if i < 10 or i >= len(reference_points) - 5:
            logger.info(f"  Y={labeled} → OCR识别在Y={ocr}，偏差={deviation:+d}px")
        elif i == 10:
            logger.info(f"  ... (省略中间{len(reference_points)-15}个点)")

    # 线性插值校准函数：OCR坐标 → 真实坐标
    calibration_func = interp1d(
        ocr_values,      # 输入：OCR识别到的Y坐标
        labeled_values,  # 输出：真实应该在的Y坐标
        kind='linear',   # 线性插值
        fill_value='extrapolate'  # 超出范围则外推
    )

    return calibration_func


def main():
    """主函数：创建校准图片并生成校准函数."""

    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)

    logger.info("=" * 80)
    logger.info("OCR坐标校准系统 - 创建校准函数")
    logger.info("=" * 80)

    # 创建输出目录
    output_dir = "calibration_data"
    os.makedirs(output_dir, exist_ok=True)

    # 步骤1: 创建校准图片（300 DPI标准尺寸）
    logger.info("\n步骤1/7: 创建标准校准图片")

    # 300 DPI下左侧图片的标准尺寸（从实际业务中获取）
    # 这个尺寸应该与实际业务图片的左侧部分一致
    width = 2174   # 左侧图片宽度
    height = 3508  # 左侧图片高度
    interval = 50  # 每50px一个标注

    logger.info(f"  图片尺寸: {width}×{height}")
    logger.info(f"  标注间隔: {interval}px")

    calib_img = create_calibration_image(width, height, interval)

    # 保存纯净校准图片
    calib_path = os.path.join(output_dir, "calibration_standard.png")
    cv2.imwrite(calib_path, calib_img)
    logger.info(f"  已保存: {calib_path}")

    # 步骤2: 添加几何锚点（用于验证）
    logger.info("\n步骤2/7: 添加几何锚点")

    anchor_positions = list(range(0, height, 500))  # 每500px一个锚点
    calib_img_with_marks = add_geometric_anchors(calib_img, anchor_positions)

    # 保存带锚点的图片
    calib_marked_path = os.path.join(output_dir, "calibration_with_marks.png")
    cv2.imwrite(calib_marked_path, calib_img_with_marks)
    logger.info(f"  已保存: {calib_marked_path}")
    logger.info(f"  锚点数量: {len(anchor_positions)}")

    # 步骤3: 验证几何锚点（确认图片坐标系统正确）
    logger.info("\n步骤3/7: 验证几何锚点")

    geometric_ref_points = detect_geometric_anchors(calib_img_with_marks, anchor_positions)

    logger.info(f"  检测到 {len(geometric_ref_points)} 个几何锚点")
    for expected, detected in geometric_ref_points[:5]:
        error = detected - expected
        logger.info(f"    预期Y={expected}, 检测Y={detected}, 误差={error:+d}px")

    # 步骤4: 初始化OCR引擎
    logger.info("\n步骤4/7: 初始化OCR引擎")

    ocr_engine = OCREngine(
        use_gpu=None,  # 自动检测
        lang='ch',
        confidence_threshold=0.5
    )

    # 步骤5: OCR识别校准图片（使用纯净版本，无几何标记）
    logger.info("\n步骤5/7: OCR识别校准图片")

    ocr_results = ocr_engine.recognize_image(calib_img, preprocess=False)
    logger.info(f"  识别到 {len(ocr_results)} 个文本块")

    # 步骤6: 提取参考点并建立校准函数
    logger.info("\n步骤6/7: 提取参考点并建立校准函数")

    ocr_ref_points = extract_reference_points_from_ocr(ocr_results)
    logger.info(f"  成功提取 {len(ocr_ref_points)} 个参考点")

    if len(ocr_ref_points) < 10:
        logger.error("参考点数量太少，校准可能不准确！")
        logger.error("建议检查OCR识别结果")
        return

    calibration_func = build_calibration_function(ocr_ref_points, logger)

    if calibration_func is None:
        logger.error("校准函数创建失败！")
        return

    # 步骤7: 保存校准函数
    logger.info("\n步骤7/7: 保存校准函数")

    calib_func_path = os.path.join(output_dir, "ocr_calibration_300dpi.pkl")

    # 保存为pickle文件
    with open(calib_func_path, 'wb') as f:
        pickle.dump({
            'calibration_func': calibration_func,
            'reference_points': ocr_ref_points,
            'width': width,
            'height': height,
            'interval': interval,
            'dpi': 300
        }, f)

    logger.info(f"  已保存: {calib_func_path}")

    # 测试校准函数
    logger.info("\n校准函数测试：")
    test_values = [500, 1000, 1500, 2000, 2500, 3000]
    for test_y in test_values:
        calibrated_y = int(calibration_func(test_y))
        offset = calibrated_y - test_y
        logger.info(f"  输入OCR坐标={test_y} → 校准后={calibrated_y} (偏移{offset:+d}px)")

    logger.info("\n" + "=" * 80)
    logger.info("校准完成！")
    logger.info("=" * 80)
    logger.info(f"\n校准数据已保存到: {output_dir}/")
    logger.info("现在可以在业务流程中使用校准函数了。")


if __name__ == "__main__":
    main()
