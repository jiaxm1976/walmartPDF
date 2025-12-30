# ============================================================
# 文件: backend/app/services/left_image_processor_service.py
# 功能: 左侧图片OCR文本提取与结构化数据处理服务
# 作者: 开发团队
# 创建时间: 2025-12-27
# 最后修改: 2025-12-27
# 依赖: numpy, logging, typing, text_formatter, ocr_service
# 说明: 实现左侧图片的OCR识别、文本块合并、行处理和结构化数据提取
# ============================================================

import logging
import numpy as np
from typing import List, Tuple, Dict, Any, Optional

from backend.app.utils.text_formatter import merge_text_blocks, format_text
from backend.app.services.ocr_service import get_ocr_service
from backend.app.services.ocr_engine import OCREngine

# 创建logger实例
logger = logging.getLogger(__name__)


class LeftImageProcessorService:
    """左侧图片处理服务类.
    
    负责接收左侧图片，通过OCR提取文本块，进行格式化处理，并基于坐标信息合并行，
    最终输出结构化的文本数据。
    
    核心功能:
    1. 图片质量检测与预处理
    2. OCR识别与文本块提取
    3. 文本格式化处理
    4. 基于坐标的文本行合并
    5. 结构化数据提取
    6. 完整的错误处理与日志记录
    """
    
    def __init__(self, ocr_engine: Optional[OCREngine] = None):
        """初始化左侧图片处理服务.
        
        Args:
            ocr_engine: 可选的OCR引擎实例，如不提供则使用默认引擎
        """
        logger.info("=" * 60)
        logger.info("初始化左侧图片处理服务")
        logger.info("=" * 60)
        
        # 如果提供了OCR引擎实例，则直接使用
        # 否则通过ocr_service获取默认引擎
        if ocr_engine:
            self.ocr_engine = ocr_engine
            logger.info("使用提供的OCR引擎实例")
        else: 
            self.ocr_service = get_ocr_service()
            self.ocr_engine = None #
            logger.info("将使用默认OCR服务引擎")
        
        logger.info("左侧图片处理服务初始化完成")
    
    def ensure_ocr_engine(self) -> OCREngine:
        """确保OCR引擎已加载.
        
        如果没有直接提供OCR引擎实例，则从OCR服务获取.
        
        Returns:
            OCREngine: OCR引擎实例
            
        Raises:
            RuntimeError: OCR引擎获取失败
        """
        if self.ocr_engine is None:
            try:
                self.ocr_engine = self.ocr_service.ensure_engine_loaded()
            except Exception as e:
                logger.error(f"获取OCR引擎失败: {e}")
                raise RuntimeError(f"获取OCR引擎失败: {e}") from e
        return self.ocr_engine
    
    def preprocess_image(self, image: np.ndarray, dpi: int = 300) -> np.ndarray:
        """图片预处理.
        
        根据图片质量和分辨率进行动态预处理，提高OCR识别准确率.
        
        Args:
            image: 输入图片（numpy数组，BGR格式）
            dpi: 图片DPI，用于动态调整预处理策略
            
        Returns:
            np.ndarray: 预处理后的图片
        """
        logger.debug(f"开始图片预处理，当前DPI: {dpi}")
        
        try:
            # 根据DPI动态调整预处理参数
            enhance = dpi < 300  # 低分辨率图片需要增强
            
            from backend.app.utils.image_utils import preprocess_image
            processed_image = preprocess_image(image, enhance=enhance)
            
            logger.debug("图片预处理完成")
            return processed_image
        except Exception as e:
            logger.warning(f"图片预处理失败，将使用原图: {e}")
            return image
    
    def extract_text_blocks(self, image: np.ndarray) -> List[Tuple]:
        """从图片中提取包含坐标信息的文本块.
        
        Args:
            image: 输入图片（numpy数组，BGR格式）
            
        Returns:
            List[Tuple]: OCR识别结果列表，格式: [(box, (text, confidence)), ...]
            
        Raises:
            RuntimeError: OCR识别失败
        """
        logger.info("开始提取文本块")
        
        try:
            engine = self.ensure_ocr_engine()
            
            # 进行OCR识别，启用预处理
            ocr_results = engine.recognize_image(image, preprocess=True)
            
            logger.info(f"成功提取 {len(ocr_results)} 个文本块")
            return ocr_results
        except Exception as e:
            logger.error(f"提取文本块失败: {e}")
            raise RuntimeError(f"提取文本块失败: {e}") from e
    
    def format_text_blocks(self, ocr_results: List[Tuple]) -> List[Tuple[List, Tuple[str, float]]]:
        """格式化文本块内容.
        
        对OCR识别的文本块进行清洗、编码统一、特殊符号处理等格式化操作.
        
        Args:
            ocr_results: OCR识别结果列表
            
        Returns:
            List[Tuple]: 格式化后的文本块列表
        """
        logger.debug("开始格式化文本块")
        
        formatted_results = []
        for box, (text, confidence) in ocr_results:
            # 应用文本格式化规则
            formatted_text = format_text(text)
            formatted_results.append((box, (formatted_text, confidence)))
            #logger.info(f"格式化前: {text} -> 格式化后: {formatted_text}AAA：{confidence}")
        
        logger.debug(f"成功格式化 {len(formatted_results)} 个文本块")
        return formatted_results
    
    def merge_text_lines(self, ocr_results: List[Tuple], y_tolerance: int = 15) -> List[Dict[str, Any]]:
        """基于坐标信息合并文本行.
        
        将Y坐标相近的文本块合并为一行，确保语义连贯.
        
        Args:
            ocr_results: OCR识别结果列表
            y_tolerance: Y坐标容差，用于判断文本块是否在同一行
            
        Returns:
            List[Dict[str, Any]]: 文本行列表，每个元素包含text、confidence、bbox、y等字段
        """
        logger.info(f"开始合并文本行，Y坐标容差: {y_tolerance}")
        
        try:
            # 使用text_formatter中的merge_text_blocks函数合并文本块
            merged_text, text_infos = merge_text_blocks(ocr_results, y_tolerance=y_tolerance)
            text_lines = []
            
            # # 将合并后的文本按行分割
            # lines = merged_text.split('\n')
            
            # for line in lines:
            #     if line.strip():
            #         # 计算该行的平均置信度和合并边界框
            #         line_text_infos = []
            #         for info in text_infos:
            #             if info.text in line:
            #                 line_text_infos.append(info)
                    
            #         # 创建文本行字典
            #         text_line = {
            #             "text": line.strip(),
            #             "confidence": sum(info.confidence for info in line_text_infos) / len(line_text_infos) if line_text_infos else 0.0,
            #             "y": sum(info.center_y for info in line_text_infos) / len(line_text_infos) if line_text_infos else 0.0,
            #             "bbox": self._merge_bboxes([info.box for info in line_text_infos]) if line_text_infos else []
            #         }
                    
            #         text_lines.append(text_line)
            logger.info(f"成功merged_text合并为 {merged_text} 行文本")
            logger.info(f"成功合并为 {len(text_infos)} 行文本")
            return merged_text, text_infos
        except Exception as e:
            logger.error(f"合并文本行失败: {e}")
            return []
    
    def _merge_bboxes(self, bboxes: List[List[List[float]]]) -> List[List[float]]:
        """合并多个边界框为一个.
        
        Args:
            bboxes: 边界框列表
            
        Returns:
            List[List[float]]: 合并后的边界框
        """
        if not bboxes:
            return []
            
        min_x = min(box[0][0] for box in bboxes)
        min_y = min(box[0][1] for box in bboxes)
        max_x = max(box[2][0] for box in bboxes)
        max_y = max(box[2][1] for box in bboxes)
        
        return [[min_x, min_y], [max_x, min_y], [max_x, max_y], [min_x, max_y]]
    
    def extract_structured_data(self, text_lines: List[Dict[str, Any]]) -> Dict[str, Any]:
        """从文本行中提取结构化数据.
        
        基于文本内容和格式，提取关键字和对应的值，形成结构化数据.
        
        Args:
            text_lines: 文本行列表，每个元素包含text、confidence、bbox、y等字段
            
        Returns:
            Dict[str, Any]: 结构化数据字典
        """
        import time
        logger.info("开始提取结构化数据")
        
        try:
            # 初始化结构化数据
            structured_data = {
                "classdata": {
                    "text_lines": text_lines,
                    "key_value_pairs": {},
                    "category_details": []  # 存储最终的类别+明细
                },
                "metadata": {
                    "line_count": len(text_lines),
                    "category_count": 0,
                    "detail_count": 0,
                    "processing_time": time.strftime("%Y-%m-%d %H:%M:%S")
                }
            }

            # 核心解析逻辑
            current_category = "header"  # 临时存储当前类别名
            current_details = []   # 临时存储当前类别的明细

            for i, line_dict in enumerate(text_lines, start=1):
                line = line_dict["text"]  # 从字典中获取文本内容
                
                # ---- 判断1：是【类别行】（纯字符串，无逗号） ----
                if "," not in line and i>2:
                    # 如果不是第一个类别，先把上一个类别的数据存入结构体
                    if current_category and current_details:
                        structured_data["classdata"]["category_details"].append({
                            "类别名称": current_category,
                            "明细列表": current_details
                        })
                    # 切换为新的类别
                    current_category = line
                    current_details = []  # 清空明细，准备存新类别的数据
                # ---- 判断2：是【明细行】（有逗号，字段名+金额） ----
                else:
                    if "向您支付的金额" in line.strip() and i>15:
                        # 如果不是第一个类别，先把上一个类别的数据存入结构体
                        if current_category and current_details:
                            structured_data["classdata"]["category_details"].append({
                                "类别名称": current_category,
                                "明细列表": current_details
                            })
                        # 切换为新的类别
                        current_category = "footer"
                        current_details = []  # 清空明细，准备存新类别的数
                    else:
                        # 解析明细行：剔除单引号 + 分割字段名和金额
                        field_name, amount_str = line.replace("'", "").split(",")
                        # 金额转数值类型(float)，并去除首尾空格（防止格式不规范）
                        amount = float(amount_str.strip())
                        # 把解析后的明细存入临时列表
                        current_details.append({
                            "字段名": field_name.strip(),
                            "金额": amount
                        })

            # ---- 处理最后一个类别的数据（循环结束后，最后一个类别还没存入） ----
            if current_category and current_details:
                structured_data["classdata"]["category_details"].append({
                    "类别名称": current_category,
                    "明细列表": current_details
                })

            # ========== 4. 自动更新元数据统计信息 ==========
            structured_data["metadata"]["category_count"] = len(structured_data["classdata"]["category_details"])
            # 统计所有明细的总行数
            total_detail = sum(len(item["明细列表"]) for item in structured_data["classdata"]["category_details"])
            structured_data["metadata"]["detail_count"] = total_detail
                    
            #logger.info(f"成功提取 {len(structured_data['key_value_pairs'])} 个键值对")
            return structured_data
        except Exception as e:
            logger.error(f"提取结构化数据失败: {e}")
            # 返回部分数据，而不是空字典
            return structured_data
    
    def process_left_image(self, image: np.ndarray, dpi: int = 800) -> Dict[str, Any]:
        """处理左侧图片的主函数.
        
        整合所有处理步骤，从图片输入到结构化数据输出.
        
        Args:
            image: 输入图片（numpy数组，BGR格式）
            dpi: 图片DPI，用于动态调整处理参数
            
        Returns:
            Dict[str, Any]: 处理结果，包含原始文本行和结构化数据
            
        Raises:
            RuntimeError: 处理过程中发生严重错误
        """
        logger.info("=" * 60)
        logger.info("开始处理左侧图片")
        logger.info("=" * 60)
        
        try:
            # 1. 图片预处理
            processed_image = self.preprocess_image(image, dpi=dpi)
            
            # 2. 提取文本块
            ocr_results = self.extract_text_blocks(processed_image)
            #logger.info(f"提取文本块 {ocr_results} ")
            
            # 3. 格式化文本块
            formatted_results = self.format_text_blocks(ocr_results)
            #logger.info(f"格式化文本块 {formatted_results} ")
            
            # 4. 合并文本行
            text_lines = self.merge_text_lines(formatted_results)
            logger.info(f"合并文本行 {text_lines} ")
            
            # 5. 提取结构化数据
            structured_data = self.extract_structured_data(text_lines)
            logger.info(f"提取结structured_data构化数据 {structured_data} ")
            
            logger.info("左侧图片处理完成")
            logger.info("=" * 60)

            
            return structured_data
        except Exception as e:
            logger.error(f"左侧图片处理失败: {e}")
            raise RuntimeError(f"左侧图片处理失败: {e}") from e


# ========== 全局服务实例 ==========
_left_image_processor_instance: Optional[LeftImageProcessorService] = None


def get_left_image_processor() -> LeftImageProcessorService:
    """获取左侧图片处理服务单例实例.
    
    Returns:
        LeftImageProcessorService: 左侧图片处理服务实例
        
    Example:
        >>> processor = get_left_image_processor()
        >>> results = processor.process_left_image(image)
    """
    global _left_image_processor_instance
    
    if _left_image_processor_instance is None:
        _left_image_processor_instance = LeftImageProcessorService()
    
    return _left_image_processor_instance