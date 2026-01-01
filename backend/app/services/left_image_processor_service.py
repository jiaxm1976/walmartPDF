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
            #logger.info(f"成功merged_text合并为 {merged_text} 行文本")
            #logger.info(f"成功合并为 {len(text_infos)} 行文本")
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
    
    def _has_amount(self, text: str) -> bool:
        """判断文本是否包含金额特征（逗号、数字、美元符号等）.
        
        Args:
            text: 待判断的文本
            
        Returns:
            bool: 是否包含金额特征
        """
        # 检查是否包含逗号（分隔字段和金额）
        if "," not in text:
            return False
        
        # 检查是否包含数字、美元符号、减号等金额特征
        import re
        amount_pattern = r'[\d\$¥\-\.]+'
        parts = text.split(",")
        if len(parts) >= 2:
            # 检查分割后的第二部分是否包含数字/金额特征
            return bool(re.search(amount_pattern, parts[-1]))
        return False
    
    def _is_section_header(self, text: str, line_no: int) -> bool:
        """判断文本是否为板块标题（如"销售"、"退款"等）.
        
        Args:
            text: 待判断的文本
            line_no: 行号
            
        Returns:
            bool: 是否为板块标题
        """
        # 板块关键词列表
        section_keywords = ["销售", "退款", "调整", "其他活动", "沃尔玛商品服务(WFS)", "WFS"]
        
        # 去除引号和空格后的文本
        clean_text = text.strip().replace("'", "").strip()
        
        # 检查是否为板块关键词
        for keyword in section_keywords:
            if clean_text == keyword or (keyword in clean_text and "，" not in clean_text and "," not in clean_text):
                return True
        
        # 特殊处理：WFS 板块的 OCR 识别错误
        # 处理诸如 "沃尔玛商品服务(WVFS)" 这样的 OCR 错误
        if "沃尔玛商品服务" in clean_text and ("WFS" in clean_text or "WVFS" in clean_text or "VFS" in clean_text):
            logger.debug(f"[行 {line_no}] 检测到 WFS 板块标题（含 OCR 错误）：{clean_text}")
            return True
        
        return False
    
    def jg_structured_data(self, text_lines: List[str]) -> Dict[str, Any]:
        """将合并后的文本行结构化为板块+明细格式.
        
        根据行的内容特征（是否包含金额），自动识别板块和明细，支持动态切换板块.
        
        Args:
            text_lines: 合并后的文本行列表（可以是字符串或dict，从merge_text_lines返回）
            
        Returns:
            Dict[str, Any]: 板块结构化数据
                {
                    "sections": {
                        "header": [...],
                        "销售": [...],
                        ...
                        "footer": [...]
                    },
                    "metadata": {
                        "section_order": ["header", "销售", ...],
                        "section_count": <int>,
                        "detail_count": <int>,
                        "processed_at": "..."
                    }
                }
        """
        import time
        import re
        
        logger.info("开始新的板块结构化数据提取")
        
        try:
            # 处理 text_lines 的格式（可能是字符串或字典）
            if isinstance(text_lines, str):
                # 如果是字符串，按换行符分割
                lines = text_lines.split("\n")
            elif isinstance(text_lines, list) and text_lines and isinstance(text_lines[0], dict):
                # 如果是字典列表，提取 "text" 字段
                lines = [line.get("text", "") for line in text_lines]
            elif isinstance(text_lines, list) and text_lines and isinstance(text_lines[0], str):
                # 如果是字符串列表，直接使用
                lines = text_lines
            else:
                # 其他情况，尝试转换为列表
                lines = [str(text_lines)]
            
            # 初始化结果结构
            structured_data = {
                "sections": {},
                "metadata": {
                    "section_order": [],
                    "section_count": 0,
                    "detail_count": 0,
                    "processed_at": time.strftime("%Y-%m-%d %H:%M:%S")
                }
            }
            
            current_section = "header"
            second_payment_found = False  # 追踪是否遇到第二个"向您支付的金额"
            payment_count = 0
            
            # 初始化第一个板块
            structured_data["sections"][current_section] = []
            structured_data["metadata"]["section_order"].append(current_section)
            
            # 扫描所有行
            for line_no, line in enumerate(lines, start=1):
                if not line.strip():
                    continue
                
                line = line.strip()
                
                # ---- 判断 1：第二个"向您支付的金额" → 切换到 footer ----
                if "向您支付的金额" in line:
                    payment_count += 1
                    if payment_count == 2 and not second_payment_found:
                        logger.info(f"[行 {line_no}] 检测到第二个'向您支付的金额'，切换到 Footer 板块")
                        second_payment_found = True
                        current_section = "footer"
                        if current_section not in structured_data["sections"]:
                            structured_data["sections"][current_section] = []
                            structured_data["metadata"]["section_order"].append(current_section)
                
                # ---- 判断 2：是否为板块标题行 ----
                if self._is_section_header(line, line_no) and line_no > 2:
                    # 切换板块
                    clean_section_name = line.strip().replace("'", "").strip()
                    
                    # 处理 WFS 板块的 OCR 识别错误（如 WVFS -> WFS）
                    if "沃尔玛商品服务" in clean_section_name:
                        # 统一纠正为标准的 WFS 板块名称
                        clean_section_name = "沃尔玛商品服务(WFS)"
                        logger.info(f"[行 {line_no}] 纠正 WFS 板块名称为标准格式")
                    
                    if clean_section_name != current_section:
                        logger.info(f"[行 {line_no}] 检测到板块标题：{clean_section_name}，切换板块")
                        current_section = clean_section_name
                        if current_section not in structured_data["sections"]:
                            structured_data["sections"][current_section] = []
                            structured_data["metadata"]["section_order"].append(current_section)
                    continue  # 板块标题行本身不作为明细存储
                
                # ---- 判断 3：是否为明细行（包含金额） ----
                if self._has_amount(line):
                    # 解析明细行：字段名 + 金额
                    try:
                        parts = line.replace("'", "").split(",")
                        if len(parts) >= 2:
                            field_name = parts[0].strip()
                            amount_str = parts[-1].strip()
                            
                            # 尝试解析为浮点数
                            try:
                                amount = float(amount_str.replace("美元", "").replace("$", "").strip())
                            except ValueError:
                                # 如果解析失败，保留原始字符串
                                amount = amount_str
                            
                            detail_item = {
                                "field": field_name,
                                "value": amount,
                                "raw": line,
                                "line_no": line_no
                            }
                            structured_data["sections"][current_section].append(detail_item)
                            logger.debug(f"[行 {line_no}] [{current_section}] {field_name} = {amount}")
                    except Exception as e:
                        logger.warning(f"[行 {line_no}] 解析明细行失败: {line}，错误: {e}")
                else:
                    # ---- 判断 4：非金额行但可能是描述（如日期区间） ----
                    if line_no == 1 or (current_section == "header" and line_no <= 3):
                        # 日期行或 header 中的非金额行
                        detail_item = {
                            "field": "统计区间",
                            "value": line,
                            "raw": line,
                            "line_no": line_no
                        }
                        structured_data["sections"][current_section].append(detail_item)
                        logger.debug(f"[行 {line_no}] [{current_section}] 描述行：{line}")
            
            # ---- 更新元数据 ----
            structured_data["metadata"]["section_count"] = len(structured_data["sections"])
            total_details = sum(len(items) for items in structured_data["sections"].values())
            structured_data["metadata"]["detail_count"] = total_details
            
            logger.info(f"✓ 结构化提取完成：{structured_data['metadata']['section_count']} 个板块，"
                       f"{structured_data['metadata']['detail_count']} 个明细项")
            
            return structured_data
            
        except Exception as e:
            logger.error(f"结构化数据提取失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {
                "sections": {},
                "metadata": {
                    "section_order": [],
                    "section_count": 0,
                    "detail_count": 0,
                    "processed_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "error": str(e)
                }
            }
    
    def extract_structured_data(self, text_lines: List[Dict[str, Any]]) -> Dict[str, Any]:
        """从文本行中提取结构化数据（已弃用，使用 jg_structured_data）.
        
        此函数保留用于向后兼容，建议直接使用 jg_structured_data.
        
        Args:
            text_lines: 文本行列表
            
        Returns:
            Dict[str, Any]: 结构化数据字典
        """
        logger.warning("extract_structured_data 已弃用，请使用 jg_structured_data")
        return self.jg_structured_data(text_lines)
    
    def process_left_image(self, image: np.ndarray, dpi: int = 800) -> Dict[str, Any]:
        """处理左侧图片的主函数.
        
        整合所有处理步骤，从图片输入到结构化数据输出.
        流程：
        1. 图片预处理
        2. 提取文本块（OCR）
        3. 格式化文本块
        4. 合并文本行
        5. 结构化数据提取（按板块+明细）
        
        Args:
            image: 输入图片（numpy数组，BGR格式）
            dpi: 图片DPI，用于动态调整处理参数
            
        Returns:
            Dict[str, Any]: 处理结果，包含板块结构化数据
            
        Raises:
            RuntimeError: 处理过程中发生严重错误
        """
        logger.info("=" * 60)
        logger.info("开始处理左侧图片")
        logger.info("=" * 60)
        
        try:
            # Step 1: 图片预处理
            logger.info("Step 1: 图片预处理")
            processed_image = self.preprocess_image(image, dpi=dpi)
            
            # Step 2: 提取文本块
            logger.info("Step 2: 提取文本块（OCR）")
            ocr_results = self.extract_text_blocks(processed_image)
            logger.info(f"  ✓ 成功提取 {len(ocr_results)} 个文本块")
            
            # Step 3: 格式化文本块
            logger.info("Step 3: 格式化文本块")
            formatted_results = self.format_text_blocks(ocr_results)
            logger.info(f"  ✓ 成功格式化 {len(formatted_results)} 个文本块")
            
            # Step 4: 合并文本行
            logger.info("Step 4: 合并文本行")
            merged_text, text_infos = self.merge_text_lines(formatted_results)
            logger.info(f"  ✓ 合并完成：合并文本长度 {len(str(merged_text))} 字符")
            
            # Step 5: 结构化数据提取
            logger.info("Step 5: 结构化数据提取（板块+明细）")
            structured_data = self.jg_structured_data(merged_text)
            logger.info(f"  ✓ 提取完成：{structured_data['metadata']['section_count']} 个板块，"
                       f"{structured_data['metadata']['detail_count']} 个明细项")
            
            logger.info("=" * 60)
            logger.info("左侧图片处理完成")
            logger.info("=" * 60)
            
            return structured_data
            
        except Exception as e:
            logger.error("=" * 60)
            logger.error(f"左侧图片处理失败: {e}")
            logger.error("=" * 60)
            import traceback
            logger.error(traceback.format_exc())
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