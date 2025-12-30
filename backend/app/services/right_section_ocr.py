# ============================================================
# 文件: backend/app/services/right_section_ocr.py
# 功能: 右侧付款详情OCR识别和数据提取
# 作者: 开发团队
# 创建时间: 2025-12-18
# 说明: Step 6 - OCR识别右侧付款详情区域并提取结构化数据
# ============================================================

import logging
import re
import json
from typing import Dict, List, Tuple, Any, Optional
from pathlib import Path
import cv2
import numpy as np

from backend.app.services.ocr_engine import OCREngine
from backend.app.utils.text_formatter import merge_text_blocks

logger = logging.getLogger(__name__)


class RightSectionOCR:
    """右侧付款详情OCR识别和数据提取器.

    对Step 2横向分割的右侧图片进行OCR识别，
    提取付款详情并输出JSON格式。

    提取内容：
    - 状态（Status）
    - 付款日期（Payment Date）
    - 周期付款（Payment Frequency）
    - 付款方式（Payment Method）
    - 设备方式（Device Method）
    - 待付款金额（Amount to be Paid）
    - 等待回款金额（Amount Waiting for Return）
    - 回款等待期（Return Waiting Period）
    - 警告信息（Warning Message）
    """

    def __init__(self, ocr_engine: OCREngine):
        """初始化OCR识别器.

        Args:
            ocr_engine: OCR引擎实例
        """
        self.ocr_engine = ocr_engine
        logger.info("=" * 60)
        logger.info("初始化右侧付款详情OCR识别器")
        logger.info("=" * 60)


    def extract_text_blocks(self, image: np.ndarray) -> List[str]:
        """从图片中提取文本块，只返回文本内容，不包含坐标信息.

        Args:
            image: 输入图片（numpy数组）

        Returns:
            List[str]: 文本块列表
        """
        # 使用新的recognize_image_text方法获取文本块
        text_blocks = self.ocr_engine.recognize_image_text(image)
        
        logger.info(f"\n===== extract_text_blocks返回值 =====")
        logger.info(f"文本块数量: {len(text_blocks)}")
        for i, text in enumerate(text_blocks):
            logger.info(f"文本块 {i+1}: {text}")
        logger.info("====================================\n")
        
        return text_blocks
        
    def extract_text_lines(self, image: np.ndarray) -> List[Tuple[str, float]]:
        """从图片中提取文本行.

        OCR可能将同一行文本分成多个块（如标签和值分开）。
        本函数将Y坐标相近的文本块合并为一行。

        Args:
            image: 输入图片（numpy数组）

        Returns:
            List[Tuple[str, float]]: 文本行列表 [(文本, Y坐标), ...]
                按Y坐标从上到下排序
        """
        # OCR识别
        ocr_results = self.ocr_engine.recognize_image(image)
        
        # 输出recognize_image函数的返回值
        logger.info("\n===== recognize_image函数返回值 =====")
        logger.info(f"OCR结果数量: {len(ocr_results)}")
        for i, (box, (text, confidence)) in enumerate(ocr_results):
            logger.info(f"结果 {i+1}:")
            logger.info(f"  文本: {text}")
            logger.info(f"  置信度: {confidence:.2f}")
            logger.info(f"  坐标框: {box}")
        logger.info("====================================\n")
        
        # 使用text_formatter中的merge_text_blocks函数合并文本块
        merged_text, text_infos = merge_text_blocks(ocr_results, y_tolerance=15)
        
        # 将合并后的文本字符串转换为List[Tuple[str, float]]格式
        text_lines = []
        if merged_text:
            lines = merged_text.split('\n')
            for line in lines:
                if line.strip():
                    # 解析每行的文本块，格式为：'文本1','文本2','文本3'
                    text_blocks = line.split(',')
                    # 移除单引号并合并为一个字符串
                    merged_line_text = ' '.join([tb.strip().strip("'") for tb in text_blocks])
                    # 计算该行的Y坐标（取所有文本块的中心Y坐标平均值）
                    line_y = sum(info.center_y for info in text_infos) / len(text_infos) if text_infos else 0.0
                    text_lines.append((merged_line_text, line_y))
        
        # 按Y坐标排序
        text_lines.sort(key=lambda x: x[1])
        
        return text_lines


    def extract_payment_details(
        self,
        text_lines: List[Tuple[str, float]]
    ) -> Dict[str, str]:
        """从文本行中提取付款详情键值对.

        解析模式：
        1. "标签 值" -> {"标签": "值"}（同一行，优先）
        2. "标签" + "值" -> {"标签": "值"}（分两行）

        特殊处理：
        - 日期字段：提取完整日期（包括时区信息）
        - 金额字段：统一格式（保留"美元"后缀）
        - 警告信息：提取完整文本

        Args:
            text_lines: 文本行列表

        Returns:
            Dict[str, str]: 键值对字典
        """
        data = {}
        i = 0

        # 定义标准字段名映射（统一命名规范）
        field_name_mapping = {
            '状态': '状态',
            '付款日期': '付款日期',
            '周期付款': '周期付款',
            '付款方式': '付款方式',
            '设备方式': '设备方式',
            '待付款金额': '待付款金额',
            '等待回款金额': '等待回款金额',
            '回款等待期': '回款等待期',
        }

        while i < len(text_lines):
            text = text_lines[i][0].strip()

            # 跳过标题行（"付款详情"）
            if text in ['付款详情', 'Payment Details']:
                i += 1
                continue

            # 模式1（优先）: "标签 值" 在同一行
            # 例如: "状态 不予付款" 或 "周期付款 每周"
            # 策略：检查是否包含已知字段名
            for field_name in field_name_mapping.keys():
                if text.startswith(field_name):
                    # 提取值（移除字段名）
                    value = text[len(field_name):].strip()
                    if value:
                        # 规范化字段名
                        normalized_field = field_name_mapping[field_name]
                        data[normalized_field] = value
                        i += 1
                        break
            else:
                # 模式2: 标签和值分两行
                # 检查当前行是否是已知字段名
                if text in field_name_mapping.keys():
                    # 查找下一行的值
                    if i + 1 < len(text_lines):
                        next_text = text_lines[i + 1][0].strip()
                        # 规范化字段名
                        normalized_field = field_name_mapping[text]
                        data[normalized_field] = next_text
                        i += 2
                        continue

                # 模式3: 警告信息（通常以特殊符号开头）
                # 例如: "⚠ 被扣置因与付款相关的账户审查。"
                if any(symbol in text for symbol in ['⚠', '△', '警告', '提示', '注意']):
                    # 移除警告符号
                    warning_text = re.sub(r'[⚠△]', '', text).strip()
                    data['警告信息'] = warning_text
                    i += 1
                    continue

                # 其他情况：跳过
                i += 1

        return data


    def process_right_image(self, image: np.ndarray) -> Dict[str, Any]:
        """处理右侧付款详情图片.

        Args:
            image: 右侧图片（numpy数组）

        Returns:
            Dict: 付款详情数据
        """
        logger.info("处理右侧付款详情...")

        # 提取文本行
        text_lines = self.extract_text_lines(image)
        logger.info(f"  提取到 {len(text_lines)} 行文本")

        # 提取付款详情
        payment_details = self.extract_payment_details(text_lines)
        logger.info(f"  提取到 {len(payment_details)} 个字段")

        # 构建结果
        result = {
            "payment_details": payment_details
        }

        return result


    def save_json(self, data: Dict[str, Any], output_path: str):
        """保存JSON数据到文件.

        Args:
            data: 结构化数据
            output_path: 输出文件路径
        """
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        logger.info(f"JSON数据已保存: {output_path}")


# ============================================================
# END OF right_section_ocr.py
# ============================================================
