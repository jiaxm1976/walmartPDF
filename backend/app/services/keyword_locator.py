# ============================================================
# 文件: services/keyword_locator.py
# 功能: 图像横向分割 + OCR关键词定位
# 作者: 开发团队
# 创建时间: 2025-12-14
# 最后修改: 2025-12-19
# 版本: v2.1 (重命名版)
# ============================================================

"""
关键词定位模块

实现功能：
1. 横向分割：将图片按63%分成左右两部分
2. OCR关键词定位：识别左侧图片中的板块关键词，提取Y坐标

说明：
- 原文件名: image_splitter.py
- 重命名原因: 更准确反映实际功能（横向分割+关键词定位，不做上下分割）
- 重命名日期: 2025-12-19
"""

import logging  # 日志记录
from typing import Dict, Tuple, List, Optional  # 类型提示
import numpy as np  # 数组操作

# 导入项目内部模块
from backend.app.services.ocr_engine import OCREngine  # OCR引擎
from backend.app.utils.image_utils import ImageProcessor  # 图像处理工具
# 移除预处理函数导入

# 创建logger实例
logger = logging.getLogger(__name__)


# ============================================================
# 自定义异常类
# ============================================================

class KeywordNotFoundError(Exception):
    """关键词识别失败异常.

    当必需的关键词（如"销售"、"退款"）未在OCR结果中找到时抛出。
    """
    pass


class OCRError(Exception):
    """OCR识别失败异常.

    当OCR引擎无法识别图片或返回空结果时抛出。
    """
    pass


# ============================================================
# 图像分割器主类（精简版）
# ============================================================

class KeywordLocator:
    """关键词定位器.

    负责将PDF图片进行横向分割，并提取左侧图片的关键词坐标。

    实现的步骤：
    Step 1: 横向分割图片（63%位置）
    Step 2: OCR识别左侧图片，提取关键词Y坐标

    Attributes:
        ocr_engine: OCR识别引擎实例
        image_processor: 图像处理工具实例
        split_ratio: 横向分割比例（统一为0.63）
    """

    def __init__(self, ocr_engine: Optional[OCREngine] = None):
        """初始化关键词定位器.

        Args:
            ocr_engine: OCR引擎实例，如果为None则创建新实例
        """
        # 初始化OCR引擎
        if ocr_engine is None:
            logger.info("创建新的OCR引擎实例")
            self.ocr_engine = OCREngine()
        else:
            self.ocr_engine = ocr_engine

        # 初始化图像处理器
        self.image_processor = ImageProcessor()

        # 横向分割比例（统一为63%）
        self.split_ratio = 0.63

        logger.info("KeywordLocator初始化完成（v2.1）")


    # ========================================
    # Step 2: 横向分割功能
    # ========================================

    def split_horizontal(self, image: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """横向分割图片（63%位置）.

        将图片按照63%比例分割成左右两部分。
        - 左侧（63%）：包含板块标题和总计信息，需要进一步切分
        - 右侧（37%）：包含明细数据，整体OCR识别

        Args:
            image: 输入图片（numpy数组）

        Returns:
            tuple: (left_image, right_image) 左右两部分图片
                - left_image: 左侧63%的图片
                - right_image: 右侧37%的图片

        Example:
            >>> import cv2
            >>> image = cv2.imread("statement_page1.png")
            >>> splitter = ImageSplitter()
            >>> left, right = splitter.split_horizontal(image)
            >>> print(f"左侧尺寸: {left.shape}, 右侧尺寸: {right.shape}")
            左侧尺寸: (2200, 1386, 3), 右侧尺寸: (2200, 814, 3)

        Note:
            - 分割比例统一为0.63（63%）
            - 左侧图片将在Step 4中按板块切分
            - 右侧图片将在Step 6中整体识别
        """
        # 获取图片尺寸
        height, width = image.shape[:2]

        # 计算分割线X坐标（63%位置）
        split_x = int(width * self.split_ratio)

        logger.info(f"横向分割：图片宽度={width}px, 分割位置={split_x}px ({self.split_ratio*100:.0f}%)")

        # 分割图片
        # 左侧：从0到split_x（63%）
        left_image = image[0:height, 0:split_x]

        # 右侧：从split_x到width（37%）
        right_image = image[0:height, split_x:width]

        logger.info(f"分割完成 - 左侧: {left_image.shape}, 右侧: {right_image.shape}")

        return left_image, right_image


    # ========================================
    # Step 3: OCR关键词定位功能
    # ========================================

    def extract_keywords_positions(self, image: np.ndarray) -> Tuple[Dict, List]:
        """提取关键词的Y坐标.

        使用OCR识别左侧图片中的所有文本，提取特定关键词的Y坐标。
        这些Y坐标将在Step 4中用于计算板块边界。

        需识别的关键词（7个板块）：
        1. 回款等待 - header板块结束标志
        2. 销售 - sales板块标题
        3. 退款 - refund板块标题
        4. 调整 - adjustment板块标题
        5. 沃尔玛商品服务(WFS) - wfs板块标题
        6. 其他活动 - other板块标题
        7. 向您支付的金额 - footer板块开始标志

        Args:
            image: 左侧图片（numpy数组）

        Returns:
            tuple: (keyword_map, ocr_results)
                - keyword_map: 关键词位置映射字典
                    {
                        'header': {'回款等待': 150},
                        'sales': {'销售': 300},
                        'refund': {'退款': 500},
                        ...
                    }
                - ocr_results: 完整OCR识别结果（供调试使用）

        Raises:
            OCRError: OCR识别失败或返回空结果

        Example:
            >>> left_image = splitter.split_horizontal(image)[0]
            >>> keyword_map, ocr_results = splitter.extract_keywords_positions(left_image)
            >>> print(f"销售板块Y坐标: {keyword_map['sales']['销售']}")
            销售板块Y坐标: 305

        Note:
            - Y坐标已应用校准函数修正（修复50px偏差问题）
            - 使用文本框中心Y坐标，比顶部坐标更稳定
            - 支持容错匹配（如"销售："也能识别为"销售"）
        """
        logger.info("开始OCR识别，提取关键词坐标")

        # 执行OCR识别
        try:
            ocr_results = self.ocr_engine.recognize_image(image)
        except Exception as e:
            logger.error(f"OCR识别失败: {e}")
            raise OCRError(f"OCR识别失败: {e}")

        # 检查OCR结果
        if not ocr_results or len(ocr_results) == 0:
            logger.error("OCR返回空结果")
            raise OCRError("OCR识别结果为空")

        # 初始化关键词映射表
        keyword_map = {
            'header': {},       # 头部板块关键词
            'sales': {},        # 销售板块关键词
            'refund': {},       # 退款板块关键词
            'adjustment': {},   # 调整板块关键词
            'wfs': {},          # WFS板块关键词
            'other': {},        # 其他活动板块关键词
            'footer': {}        # 尾部板块关键词
        }

        # 遍历OCR结果，提取关键词
        # OCR返回格式: [(box, (text, confidence)), ...]
        for box, (text, confidence) in ocr_results:
            # 获取文本内容并进行预处理
            # 移除预处理: text = preprocess_text(text)

            # 获取文本框中心Y坐标
            # box格式: [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
            # 其中: [x1,y1]=左上角, [x2,y2]=右上角, [x3,y3]=右下角, [x4,y4]=左下角
            #
            # 使用中心Y坐标的原因：
            # 1. 中心坐标不受字体大小变化影响，更稳定
            # 2. 避免baseline和box顶部的不一致性问题
            # 3. 对于不同大小的文字，中心位置的偏差最小
            y_top = box[0][1]      # 顶部Y坐标
            y_bottom = box[2][1]   # 底部Y坐标
            y_raw = int((y_top + y_bottom) / 2)  # OCR原始中心Y坐标

            # ===== 应用坐标校准 (2025-12-16) =====
            # 修复坐标偏差问题：OCR识别的坐标存在系统性偏差（约50px）
            # 通过预先生成的校准函数进行修正
            y_coord = self.ocr_engine.calibrate_y_coordinate(y_raw)
            offset = y_coord - y_raw  # 计算实际偏移量

            # 记录校准详情（DEBUG级别）
            logger.debug(f"坐标校准: Y_raw={y_raw} → Y_calibrated={y_coord}, offset={offset:+d}px")
            # =====================================

            # 精确匹配或包含匹配关键词
            # 注意：文本已预处理（清除空格、小写转大写、全角转半角）

            # Header板块: 精确匹配"回款等待"
            if text == '回款等待':
                keyword_map['header']['回款等待'] = y_coord
                logger.debug(f"找到关键词 '回款等待': Y_raw={y_raw}, Y_calibrated={y_coord}, offset={offset:+d}px")

            # Sales板块: 精确匹配"销售"或包含"销售"
            elif text == '销售' or text.startswith('销售'):
                keyword_map['sales']['销售'] = y_coord
                logger.debug(f"找到关键词 '销售': Y_raw={y_raw}, Y_calibrated={y_coord}, offset={offset:+d}px (OCR文本='{text}')")

            # Refund板块: 精确匹配"退款"或包含"退款"
            elif text == '退款' or text.startswith('退款'):
                keyword_map['refund']['退款'] = y_coord
                logger.debug(f"找到关键词 '退款': Y_raw={y_raw}, Y_calibrated={y_coord}, offset={offset:+d}px (OCR文本='{text}')")

            # Adjustment板块: 精确匹配"调整"或以"调整"开头
            elif text == '调整' or text.startswith('调整'):
                keyword_map['adjustment']['调整'] = y_coord
                logger.debug(f"找到关键词 '调整': Y_raw={y_raw}, Y_calibrated={y_coord}, offset={offset:+d}px (OCR文本='{text}')")

            # WFS板块: 支持多种命名方式（已预处理）
            # - "沃尔玛商品服务" (旧版PDF)
            # - "沃尔玛配送服务" 或 "沃尔玛配送服务(WFS)" (新版PDF，括号已转半角)
            elif '沃尔玛商品服务' in text or '沃尔玛配送服务' in text:
                # 统一使用"沃尔玛商品服务"作为key（保持向后兼容）
                keyword_map['wfs']['沃尔玛商品服务'] = y_coord
                logger.debug(f"找到关键词 'WFS板块': Y_raw={y_raw}, Y_calibrated={y_coord}, offset={offset:+d}px (OCR文本='{text}')")

            # Other板块: 精确匹配"其他活动"或包含"其他活动"
            elif text == '其他活动' or '其他活动' in text:
                keyword_map['other']['其他活动'] = y_coord
                logger.debug(f"找到关键词 '其他活动': Y_raw={y_raw}, Y_calibrated={y_coord}, offset={offset:+d}px (OCR文本='{text}')")

            # Footer板块: 包含"向您支付"，取Y坐标最大的（图片尾部的那个）
            elif '向您支付' in text:
                # 如果未记录或当前Y坐标更大（更靠下），则更新
                if '向您支付的金额' not in keyword_map['footer'] or y_coord > keyword_map['footer']['向您支付的金额']:
                    keyword_map['footer']['向您支付的金额'] = y_coord
                    logger.debug(f"找到关键词 '向您支付的金额': Y_raw={y_raw}, Y_calibrated={y_coord}, offset={offset:+d}px (OCR文本='{text}')")

        # 记录识别结果统计
        total_keywords = sum(len(v) for v in keyword_map.values())
        logger.info(f"关键词识别完成，共找到 {total_keywords} 个关键词")

        return keyword_map, ocr_results


    # ========================================
    # 可视化功能
    # ========================================

    def visualize_keywords(
        self,
        left_image: np.ndarray,
        keyword_map: Dict,
        output_path: str
    ) -> str:
        """在左侧图片上绘制关键词Y坐标线，用于验证识别准确性.

        Args:
            left_image: 左侧图片（numpy数组）
            keyword_map: 关键词位置映射字典
            output_path: 输出图片路径

        Returns:
            str: 可视化图片路径

        Example:
            >>> left_image, _ = splitter.split_horizontal(image)
            >>> keyword_map, _ = splitter.extract_keywords_positions(left_image)
            >>> vis_path = splitter.visualize_keywords(
            ...     left_image,
            ...     keyword_map,
            ...     "output/keywords_visualization.png"
            ... )
        """
        import cv2

        # 复制图片（避免修改原图）
        vis_image = left_image.copy()

        # 获取图片尺寸
        height, width = vis_image.shape[:2]

        # 定义颜色和样式
        LINE_COLOR = (0, 0, 255)      # 红色
        LINE_THICKNESS = 3             # 线条粗细
        FONT = cv2.FONT_HERSHEY_SIMPLEX
        FONT_SCALE = 1.2
        FONT_THICKNESS = 3
        TEXT_COLOR = (0, 0, 255)       # 红色

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

        # 遍历所有关键词，绘制Y坐标线
        for section, keywords in keyword_map.items():
            for keyword, y_coord in keywords.items():
                # 绘制水平线（穿过整个图片宽度）
                cv2.line(vis_image, (0, y_coord), (width, y_coord), LINE_COLOR, LINE_THICKNESS)

                # 添加文字标注：关键词名称 + Y坐标
                cn_name = section_names_cn.get(section, keyword)
                label_text = f"{cn_name}: Y={y_coord}"

                # 文字位置：靠右侧，避免遮挡左侧内容
                text_x = width - 550
                text_y = y_coord - 15

                # 绘制文字（带阴影效果，增强可读性）
                # 阴影
                cv2.putText(vis_image, label_text, (text_x + 2, text_y + 2),
                           FONT, FONT_SCALE, (0, 0, 0), FONT_THICKNESS + 1)
                # 正文
                cv2.putText(vis_image, label_text, (text_x, text_y),
                           FONT, FONT_SCALE, TEXT_COLOR, FONT_THICKNESS)

        # 保存可视化图片
        cv2.imwrite(output_path, vis_image)

        logger.info(f"可视化图片已保存: {output_path}")

        return output_path


# ============================================================
# END OF image_splitter.py (精简版 v2.1)
# ============================================================

# 说明：
# 1. 本文件仅保留Step 2-3的基础功能
# 2. 后续功能由以下新模块实现：
#    - Step 4: left_section_cutter.py (左侧板块切分)
#    - Step 5: section_data_extractor.py (左侧数据提取)
#    - Step 6: right_column_extractor.py (右侧数据提取)
#    - Step 6.5: json_formatter.py (JSON整合)
#    - Step 7: database_service.py (数据库写入)
#
# 3. 旧代码备份位置: archived/backup_20251216/
#
# 最后修改: 2025-12-16
# 修改内容: 删除第275行之后的所有代码，只保留核心的横向分割和关键词定位功能
