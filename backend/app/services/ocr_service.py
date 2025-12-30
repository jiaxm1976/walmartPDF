#!/usr/bin/env python3
# ============================================================
# 文件: backend/app/services/ocr_service.py
# 功能: OCR服务守护类
# 作者: 开发团队
# 创建时间: 2025-12-16
# 说明: 封装OCR引擎单例,提供统一的调用接口和性能监控
# ============================================================

import logging
import time
from typing import List, Dict, Any, Tuple, Optional
from pathlib import Path

from .ocr_engine import OCREngine

# 创建logger实例
logger = logging.getLogger(__name__)


class OCRService:
    """OCR服务类.

    封装OCR引擎单例,提供统一的调用接口。
    支持性能监控、错误处理、日志记录。

    Attributes:
        engine: OCR引擎单例实例
        call_count: 调用次数统计
        total_time: 总处理时间（秒）
    """

    def __init__(self):
        """初始化OCR服务."""
        self.engine: Optional[OCREngine] = None
        self.call_count = 0
        self.total_time = 0.0

        logger.info("OCR服务初始化完成")

    def ensure_engine_loaded(self) -> OCREngine:
        """确保OCR引擎已加载.

        使用懒加载模式,首次调用时才加载引擎。

        Returns:
            OCREngine: OCR引擎实例

        Raises:
            RuntimeError: 引擎加载失败
        """
        if self.engine is None:
            logger.info("首次调用,正在加载OCR引擎...")

            try:
                self.engine = OCREngine()
                logger.info("OCR引擎加载成功")
            except Exception as e:
                logger.error(f"OCR引擎加载失败: {e}")
                raise RuntimeError(f"OCR引擎加载失败: {e}") from e

        return self.engine

    def recognize_image(
        self,
        image,
        preprocess: bool = True
    ) -> List[Tuple[List, Tuple[str, float]]]:
        """识别图片中的文字.

        Args:
            image: 图片对象（PIL Image或numpy数组）
            preprocess: 是否预处理图片

        Returns:
            list: OCR识别结果列表
                格式: [(box_coordinates, (text, confidence)), ...]

        Raises:
            RuntimeError: OCR识别失败
        """
        # 确保引擎已加载
        engine = self.ensure_engine_loaded()

        # 记录开始时间
        start_time = time.time()

        try:
            # 执行识别
            results = engine.recognize_image(image, preprocess=preprocess)

            # 统计信息
            elapsed_time = time.time() - start_time
            self.call_count += 1
            self.total_time += elapsed_time

            logger.debug(
                f"OCR识别完成: {len(results)}个文本块, "
                f"耗时{elapsed_time:.2f}秒"
            )

            return results

        except Exception as e:
            logger.error(f"OCR识别失败: {e}")
            raise RuntimeError(f"OCR识别失败: {e}") from e

    def recognize_region(
        self,
        image,
        region: Tuple[int, int, int, int],
        preprocess: bool = True
    ) -> List[Tuple[List, Tuple[str, float]]]:
        """识别图片中指定区域的文字.

        Args:
            image: 图片对象
            region: 区域坐标 (x, y, width, height)
            preprocess: 是否预处理

        Returns:
            list: OCR识别结果

        Raises:
            RuntimeError: OCR识别失败
        """
        engine = self.ensure_engine_loaded()

        start_time = time.time()

        try:
            results = engine.recognize_region(image, region, preprocess=preprocess)

            elapsed_time = time.time() - start_time
            self.call_count += 1
            self.total_time += elapsed_time

            logger.debug(
                f"区域OCR识别完成: {len(results)}个文本块, "
                f"耗时{elapsed_time:.2f}秒"
            )

            return results

        except Exception as e:
            logger.error(f"区域OCR识别失败: {e}")
            raise RuntimeError(f"区域OCR识别失败: {e}") from e

    def extract_text_only(
        self,
        image,
        preprocess: bool = False,
        join_with: str = '\n'
    ) -> str:
        """提取图片中的所有文字（纯文本）.

        Args:
            image: 图片对象
            preprocess: 是否预处理
            join_with: 文本连接符

        Returns:
            str: 提取的纯文本内容
        """
        engine = self.ensure_engine_loaded()

        start_time = time.time()

        try:
            text = engine.extract_text_only(
                image,
                preprocess=preprocess,
                join_with=join_with
            )

            elapsed_time = time.time() - start_time
            self.call_count += 1
            self.total_time += elapsed_time

            logger.debug(
                f"文本提取完成: {len(text)}字符, "
                f"耗时{elapsed_time:.2f}秒"
            )

            return text

        except Exception as e:
            logger.error(f"文本提取失败: {e}")
            return ""

    def find_keyword_position(
        self,
        image,
        keyword: str,
        preprocess: bool = False
    ) -> Optional[Tuple[int, int, int, int]]:
        """在图片中查找关键词的位置.

        Args:
            image: 图片对象
            keyword: 要查找的关键词
            preprocess: 是否预处理

        Returns:
            tuple: 关键词所在的边界框 (x, y, width, height)，未找到返回None
        """
        engine = self.ensure_engine_loaded()

        start_time = time.time()

        try:
            bbox = engine.find_keyword_position(
                image,
                keyword,
                preprocess=preprocess
            )

            elapsed_time = time.time() - start_time
            self.call_count += 1
            self.total_time += elapsed_time

            if bbox:
                logger.debug(f"关键词'{keyword}'定位成功, 耗时{elapsed_time:.2f}秒")
            else:
                logger.debug(f"关键词'{keyword}'未找到, 耗时{elapsed_time:.2f}秒")

            return bbox

        except Exception as e:
            logger.error(f"关键词定位失败: {e}")
            return None

    def find_multiple_keywords(
        self,
        image,
        keywords: List[str],
        preprocess: bool = False
    ) -> Dict[str, Optional[Tuple[int, int, int, int]]]:
        """批量查找多个关键词的位置.

        Args:
            image: 图片对象
            keywords: 关键词列表
            preprocess: 是否预处理

        Returns:
            dict: 关键词到位置的映射
        """
        engine = self.ensure_engine_loaded()

        start_time = time.time()

        try:
            positions = engine.find_multiple_keywords(
                image,
                keywords,
                preprocess=preprocess
            )

            elapsed_time = time.time() - start_time
            self.call_count += 1
            self.total_time += elapsed_time

            found_count = sum(1 for pos in positions.values() if pos is not None)
            logger.debug(
                f"批量关键词定位完成: {found_count}/{len(keywords)}个找到, "
                f"耗时{elapsed_time:.2f}秒"
            )

            return positions

        except Exception as e:
            logger.error(f"批量关键词定位失败: {e}")
            return {kw: None for kw in keywords}

    def get_statistics(self) -> Dict[str, Any]:
        """获取服务统计信息.

        Returns:
            dict: 统计信息
                - call_count: 调用次数
                - total_time: 总处理时间（秒）
                - avg_time: 平均处理时间（秒）
                - engine_loaded: 引擎是否已加载
        """
        stats = {
            'call_count': self.call_count,
            'total_time': self.total_time,
            'avg_time': self.total_time / self.call_count if self.call_count > 0 else 0,
            'engine_loaded': self.engine is not None
        }

        if self.engine:
            stats['engine_info'] = self.engine.get_engine_info()

        return stats

    def reset_statistics(self):
        """重置统计信息."""
        self.call_count = 0
        self.total_time = 0.0
        logger.info("OCR服务统计信息已重置")


# ========== 全局服务实例 ==========
_ocr_service_instance: Optional[OCRService] = None


def get_ocr_service() -> OCRService:
    """获取OCR服务单例实例.

    Returns:
        OCRService: OCR服务实例

    Example:
        >>> service = get_ocr_service()
        >>> results = service.recognize_image(image)
    """
    global _ocr_service_instance

    if _ocr_service_instance is None:
        _ocr_service_instance = OCRService()

    return _ocr_service_instance
  