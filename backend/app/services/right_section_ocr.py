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
from typing import Dict, List, Tuple, Any, Optional, Union
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

    def __init__(self, ocr_engine: Optional[OCREngine] = None):
        """初始化OCR识别器。

        如果外部未提供 `ocr_engine`，在此处自动初始化一个 `OCREngine` 实例。

        Args:
            ocr_engine: 可选的 OCR 引擎实例；若为 None 则内部创建默认引擎
        """
        if ocr_engine is None:
            try:
                self.ocr_engine = OCREngine()
            except Exception as e:
                logger.error(f"初始化 OCREngine 失败: {e}")
                raise
        else:
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

    def ocr_recognize(self, image: np.ndarray) -> Dict[str, Any]:
        """
        兼容层：调用底层 OCR 引擎并返回统一的字典格式：
        {'text_lines': [ { 'text': str, 'bbox': [x1,y1,x2,y2], 'confidence': float, 'vertical_center': float }, ... ]}
        本方法便于单元测试 patch() 替换。
        """
        try:
            # 优先使用 recognize_image（返回带坐标和置信度的结构）
            results = self.ocr_engine.recognize_image(image)
        except Exception:
            try:
                # 退回到简单识别方法
                results = self.ocr_engine.recognize_image_text(image)
            except Exception:
                return {'text_lines': []}

        # 标准化返回
        text_lines = []
        try:
            # recognize_image 可能返回 list of (box, (text, confidence))
            if isinstance(results, list):
                for box, (text, confidence) in results:
                    try:
                        bbox = [int(box[0][0]), int(box[0][1]), int(box[2][0]), int(box[2][1])]
                    except Exception:
                        # fallback if box is simple list
                        bbox = list(box) if isinstance(box, (list, tuple)) else []
                    try:
                        vertical_center = (bbox[1] + bbox[3]) / 2 if bbox else None
                    except Exception:
                        vertical_center = None
                    text_lines.append({
                        'text': text,
                        'bbox': bbox,
                        'confidence': float(confidence) if confidence is not None else None,
                        'vertical_center': vertical_center
                    })
            elif isinstance(results, dict) and 'text_lines' in results:
                # already in expected format
                text_lines = results['text_lines']
            else:
                # unexpected format
                return {'text_lines': []}
        except Exception:
            return {'text_lines': []}

        return {'text_lines': text_lines}
        
    def extract_text_lines(self, image: np.ndarray) -> List[Dict[str, Any]]:
        """从图片中提取文本行.

        OCR可能将同一行文本分成多个块（如标签和值分开）。
        本函数将Y坐标相近的文本块合并为一行。

        Args:
            image: 输入图片（numpy数组）

        Returns:
            List[Tuple[str, float]]: 文本行列表 [(文本, Y坐标), ...]
                按Y坐标从上到下排序
        """
        # 使用兼容的 OCR 接口获取结果（便于测试 patch）
        try:
            ocr_out = self.ocr_recognize(image)
        except Exception as e:
            logger.warning(f"OCR 识别失败: {e}")
            return []

        if not ocr_out or not isinstance(ocr_out, dict):
            return []

        lines = ocr_out.get('text_lines', [])
        result_lines = []

        for item in lines:
            try:
                if isinstance(item, dict):
                    text = item.get('text', '').strip()
                    bbox = item.get('bbox')
                    vc = item.get('vertical_center')
                    conf = item.get('confidence')
                    # ensure keys exist
                    entry = {
                        'text': text,
                        'bbox': bbox,
                        'confidence': conf,
                        'vertical_center': vc
                    }
                    result_lines.append(entry)
                elif isinstance(item, (list, tuple)) and len(item) >= 2:
                    # e.g., (text, y)
                    text = item[0]
                    vc = item[1]
                    result_lines.append({'text': str(text), 'vertical_center': float(vc)})
                else:
                    # unknown format, skip
                    continue
            except Exception:
                continue

        return result_lines


    def extract_payment_details(
        self,
        text_lines: List[Union[Dict[str, Any], Tuple[Any, float], str]]
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
            # 支持多种输入格式：dict({'text':...}), tuple (text, y), 或简单字符串
            cur = text_lines[i]
            if isinstance(cur, dict):
                text = str(cur.get('text', '')).strip()
                bbox = cur.get('bbox')
                vertical_center = cur.get('vertical_center')
            elif isinstance(cur, (list, tuple)) and len(cur) >= 1:
                text = str(cur[0]).strip()
                vertical_center = cur[1] if len(cur) > 1 else None
                bbox = None
            else:
                # 非标准格式，跳过
                i += 1
                continue

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
                        nxt = text_lines[i + 1]
                        if isinstance(nxt, dict):
                            next_text = str(nxt.get('text', '')).strip()
                        elif isinstance(nxt, (list, tuple)) and len(nxt) >= 1:
                            next_text = str(nxt[0]).strip()
                        else:
                            next_text = ''
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

    def process_right_section(self, image: np.ndarray) -> Dict[str, Any]:
        """
        兼容方法：处理右侧图片并直接返回键值对字典（供测试使用）。
        返回格式：{ '状态': '...', '付款日期': '...' }
        """
        try:
            text_lines = self.extract_text_lines(image)
            details = self.extract_payment_details(text_lines)
            return details
        except Exception as e:
            logger.error(f"处理右侧板块失败: {e}")
            return {}


    def save_json(self, data: Dict[str, Any], output_path: str) -> None:
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
