# ============================================================
# 文件: backend/app/services/keyword_extractor.py
# 功能: 关键词提取和Y坐标定位
# 作者: 开发团队
# 创建时间: 2025-12-18
# ============================================================

import logging
import re
from typing import Dict, List, Tuple
import numpy as np

# 导入文本预处理工具
# 移除预处理函数导入

logger = logging.getLogger(__name__)


class KeywordExtractor:
    """关键词提取器.

    功能:
    - 从OCR结果中提取关键词
    - 定位关键词的Y坐标
    - 用于板块切分

    关键词匹配策略:
    - 使用正则表达式精确匹配板块标题
    - 避免误匹配（如"退款"匹配到"WFS运输退款"）
    - 优先匹配完整形式，再匹配简写形式
    """

    # 板块标题关键词的正则表达式模式（精确匹配）
    # 格式: (关键词标识, 正则模式, 说明)
    # 注意：由于文本已预处理（空格清除、小写转大写、全角转半角），模式不需要包含\s*
    SECTION_KEYWORDS = [
        # 核心板块（严格匹配，避免误识别）
        ("销售", r"^销售$", "完全匹配'销售'，不匹配'销售额'等"),
        ("退款", r"^退款$", "完全匹配'退款'，不匹配'WFS运输退款'"),
        ("调整", r"^调整$", "完全匹配'调整'"),

        # WFS板块（支持多种表达）
        ("沃尔玛商品服务", r"沃尔玛商品服务|沃尔玛配送服务|WALMARTFULFILLMENT", "匹配各种WFS表达"),
        ("WFS", r"^WFS$", "完全匹配'WFS'缩写"),

        # 其他板块
        ("其他活动", r"^其他活动", "匹配'其他活动'开头"),

        # Footer板块（支持多种表达）
        ("向您支付的金额", r"向您支付的金额|付款给您|AMOUNTSPaid", "匹配付款相关表达"),
        ("期末余额", r"期末余额|结束余额|ENDINGBALANCE", "匹配余额相关表达"),
    ]

    # Footer关键词必须在图片下半部分（Y > 图片高度的60%）
    # 原因：Footer板块包含"向您支付的金额"和"期末余额"，总是位于PDF底部
    # 如果在上半部分出现，说明是OCR误识别或重复文本
    MIN_FOOTER_Y_RATIO = 0.6

    def __init__(self, ocr_engine):
        """初始化关键词提取器.

        Args:
            ocr_engine: OCR引擎实例
        """
        self.ocr_engine = ocr_engine

    def extract_keywords_positions(
        self,
        image: np.ndarray,
        ocr_results: List[Tuple]
    ) -> Dict[str, int]:
        """从OCR结果中提取关键词及其Y坐标（带位置验证和精确匹配）.

        Args:
            image: 输入图片
            ocr_results: OCR识别结果

        Returns:
            Dict[str, int]: 关键词到Y坐标的映射

        关键词匹配规则：
        1. 使用正则表达式精确匹配板块标题
        2. Footer关键词必须在图片下半部分（Y > 60%高度）
        3. 每个关键词只记录第一次匹配的位置
        4. 跳过不合理位置的关键词（防止误识别）

        示例：
        - "退款" 只匹配独立的"退款"文本
        - "WFS运输退款" 不会被误匹配为"退款"
        """
        keyword_map = {}
        image_height = image.shape[0]
        min_footer_y = image_height * self.MIN_FOOTER_Y_RATIO

        for box, (text, confidence) in ocr_results:
            # 计算Y坐标（使用底部坐标）
            y_coord = int(box[2][1])

            # 移除预处理：文本保持原样
            text_cleaned = text

            # 使用正则表达式匹配关键词（不需要忽略大小写，因为文本已转大写）
            for keyword_id, pattern, description in self.SECTION_KEYWORDS:
                # 尝试匹配
                if re.search(pattern, text_cleaned):
                    # Footer关键词位置验证
                    if keyword_id in ["向您支付的金额", "期末余额"]:
                        if y_coord < min_footer_y:
                            logger.warning(
                                f"跳过错误的footer位置: '{keyword_id}' (匹配文本='{text_cleaned}') "
                                f"@ Y={y_coord} (< {min_footer_y:.0f}, 图片高度={image_height})"
                            )
                            continue

                    # 记录关键词的Y坐标（只记录第一次匹配）
                    if keyword_id not in keyword_map:
                        keyword_map[keyword_id] = y_coord
                        logger.debug(
                            f"识别到关键词: {keyword_id} @ Y={y_coord} "
                            f"(匹配文本='{text_cleaned}', 模式='{pattern}')"
                        )
                        # 找到匹配后跳出循环，避免一个文本匹配多个关键词
                        break

        logger.info(f"提取到 {len(keyword_map)} 个关键词")
        return keyword_map


# ============================================================
# END OF keyword_extractor.py
# ============================================================
