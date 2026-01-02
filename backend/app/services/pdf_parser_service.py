# ============================================================# 文件: backend/app/services/pdf_parser_service.py# 功能: PDF解析服务（集成Phase 2完整流程）# 作者: 开发团队# 创建时间: 2025-12-18# 说明: 封装PDF解析pipeline，供API调用# ============================================================

import logging
import json
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
import cv2
import numpy as np

# 导入Phase 2的服务模块
from backend.app.services.keyword_locator import KeywordLocator
from backend.app.services.left_image_processor_service import get_left_image_processor
from backend.app.utils.image_utils import pdf_to_images
from backend.app.services.ocr_engine import OCREngine
from backend.app.services.right_section_ocr import RightSectionOCR


logger = logging.getLogger(__name__)



class PDFParserService:
    """PDF解析服务类.

    功能:
    - 集成Phase 2的完整解析流程（Steps 1-6）
    - 提供统一的解析接口
    - 处理异常和错误
    - 返回结构化数据

    使用示例:
    ```python
    parser = PDFParserService()
    result = parser.parse_pdf("/path/to/pdf")
    if result["success"]:
        data = result["data"]
        # 保存到数据库
    else:
        error = result["error"]
    ```
    """

    def __init__(self, dpi: int = 800):
        """初始化PDF解析服务.

        Args:
            dpi: PDF转图片的DPI（默认800）
        """
        self.dpi = dpi
        logger.info(f"初始化PDF解析服务 (DPI={dpi})")


    def parse_pdf_direct(
        self,
        pdf_path: str,
        output_dir: Optional[str] = None
    ) -> Dict[str, Any]:
        """解析PDF文件（直接处理左侧板块，跳过关键词提取和板块切分）.

        Args:
            pdf_path: PDF文件路径
            output_dir: 输出目录（可选，用于保存中间结果）

        Returns:
            Dict: 解析结果
                {
                    "success": True/False,
                    "data": {
                        "left_section": {...},
                        "right_section": {...}
                    },
                    "error": "错误信息（如果失败）",
                    "process_time": 处理时间（秒）
                }
        """
        start_time = datetime.now()
        logger.info("=" * 60)
        logger.info(f"开始直接解析PDF: {pdf_path}")
        logger.info("=" * 60)

        try:

            # Step 1: PDF转灰度图片
            logger.info("Step 1: PDF转灰度图片...")
            gray_images = pdf_to_images(pdf_path, dpi=self.dpi, grayscale=True)
            if not gray_images:
                raise ValueError("PDF转图片失败：未生成任何图片")

            # 将PIL Image转换为numpy数组
            gray_images_np = []
            for img in gray_images:
                img_array = np.array(img)
                # 如果是彩色图（3通道），转为灰度
                if len(img_array.shape) == 3:
                    img_array = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
                gray_images_np.append(img_array)
            gray_images = gray_images_np

            # 只处理第1页（核心数据在第1页）
            first_page = gray_images[0]
            logger.info(f"  ✓ 转换成功: {first_page.shape}")

            # Step 2: 横向分割（63%位置）
            logger.info("Step 2: 横向分割左右侧...")
            splitter = KeywordLocator()
            left_image, right_image = splitter.split_horizontal(first_page)
            logger.info(f"  ✓ 左侧图片: {left_image.shape}")
            logger.info(f"  ✓ 右侧图片: {right_image.shape}")

            # Step 3: 直接处理左侧板块（使用新的左侧图片处理器）
            logger.info("Step 3: 直接处理左侧板块...")
            left_processor = get_left_image_processor()
            left_data = left_processor.process_left_image(left_image, dpi=self.dpi)
            
            # Step 4: 右侧OCR识别（仅传右侧图像；OCR 引擎在 RightSectionOCR 内部初始化）
            logger.info("Step 4: 右侧OCR识别...")
            try:
                right_ocr = RightSectionOCR()
                right_result = right_ocr.process_right_image(right_image)
                # right_result 格式: {"payment_details": {...}}
                right_data = right_result.get('payment_details', {}) if isinstance(right_result, dict) else {}
                logger.info(f"  ✓ 提取到付款详情: {len(right_data)} 个字段")
            except Exception as e:
                logger.warning(f"⚠ 右侧 OCR 识别失败，已跳过右侧数据: {e}")
                right_data = {}

            
            # 适配新的板块结构化数据格式
            section_count = left_data.get("metadata", {}).get("section_count", 0)
            detail_count = left_data.get("metadata", {}).get("detail_count", 0)
            logger.info(f"  ✓ 提取到 {section_count} 个板块，{detail_count} 个明细项")

           
            # 整合数据
            result_data = {
                "left_section": left_data,
                "right_section": right_data
            }

            # 保存中间结果（可选）
            if output_dir:
                # 对于直接处理模式，我们只有左右图片，没有板块切分图片
                # 创建一个虚拟的section_images，只包含整个left_image
                section_images = {"entire_left": left_image}
                self._save_intermediate_results(
                    output_dir,
                    left_image,
                    right_image,
                    section_images,
                    result_data
                )

            # 计算处理时间
            end_time = datetime.now()
            process_time = (end_time - start_time).total_seconds()

            logger.info("=" * 60)
            logger.info(f"✅ PDF直接解析完成！耗时: {process_time:.2f}秒")
            logger.info("=" * 60)

            return {
                "success": True,
                "data": result_data,
                "error": None,
                "process_time": process_time
            }

        except Exception as e:
            # 计算处理时间
            end_time = datetime.now()
            process_time = (end_time - start_time).total_seconds()

            logger.error("=" * 60)
            logger.error(f"❌ PDF直接解析失败: {e}")
            logger.error("=" * 60)
            import traceback
            traceback.print_exc()

            return {
                "success": False,
                "data": None,
                "error": str(e),
                "process_time": process_time
            }

    def _save_intermediate_results(
        self,
        output_dir: str,
        left_image: np.ndarray,
        right_image: np.ndarray,
        section_images: Dict[str, np.ndarray],
        result_data: Dict[str, Any]
    ):
        """保存中间结果（用于调试）.

        Args:
            output_dir: 输出目录
            left_image: 左侧图片
            right_image: 右侧图片
            section_images: 板块图片字典
            result_data: 解析结果数据
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # 保存左右侧图片
        cv2.imwrite(str(output_path / "left_image.png"), left_image)
        cv2.imwrite(str(output_path / "right_image.png"), right_image)

        # 保存板块图片
        for section_name, section_image in section_images.items():
            cv2.imwrite(str(output_path / f"{section_name}.png"), section_image)

        # 保存JSON数据
        with open(output_path / "parsed_data.json", "w", encoding="utf-8") as f:
            json.dump(result_data, f, ensure_ascii=False, indent=2)

        logger.info(f"中间结果已保存到: {output_path}")

    