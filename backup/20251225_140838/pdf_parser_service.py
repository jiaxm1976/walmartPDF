# ============================================================# 文件: backend/app/services/pdf_parser_service.py# 功能: PDF解析服务（集成Phase 2完整流程）# 作者: 开发团队# 创建时间: 2025-12-18# 说明: 封装PDF解析pipeline，供API调用# ============================================================

import logging
import json
import re
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
from datetime import datetime, date
from decimal import Decimal
import cv2
import numpy as np

# 导入Phase 2的服务模块
from app.services.ocr_engine import OCREngine
from app.services.keyword_locator import KeywordLocator
from app.services.keyword_extractor import KeywordExtractor
from app.services.left_section_cutter import LeftSectionCutter
from app.services.left_section_ocr import LeftSectionOCR
from app.services.right_section_ocr import RightSectionOCR
from app.utils.image_utils import pdf_to_images


logger = logging.getLogger(__name__)


def _safe_decimal(value: str) -> str:
    """安全地清洗字符串用于Decimal转换."""
    if not value or not isinstance(value, str):
        return "0.00"
    # 移除货币符号和空格
    value = value.replace("$", "").replace("¥", "").replace(" ", "").replace(",", "")
    # 只保留数字、小数点和负号
    value = re.sub(r'[^\d.-]', '', value)
    if not value or value in ["-", "."]:
        return "0.00"
    try:
        float(value)
        return value
    except (ValueError, TypeError):
        return "0.00"


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

    def __init__(self, dpi: int = 300):
        """初始化PDF解析服务.

        Args:
            dpi: PDF转图片的DPI（默认300）
        """
        self.dpi = dpi
        self.ocr_engine = None  # 延迟初始化
        logger.info(f"初始化PDF解析服务 (DPI={dpi})")

    def _init_ocr_engine(self):
        """延迟初始化OCR引擎（避免启动时加载）."""
        if self.ocr_engine is None:
            logger.info("初始化OCR引擎...")
            self.ocr_engine = OCREngine()
            logger.info("OCR引擎初始化完成")

    def parse_with_validation(
        self,
        pdf_path: str,
        max_retries: int = 2,
        output_dir: Optional[str] = None
    ) -> Dict[str, Any]:
        """解析PDF文件并进行总计校验，校验失败时重新识别（最多max_retries次）.

        Args:
            pdf_path: PDF文件路径
            max_retries: 最大重试次数（默认3次）
            output_dir: 输出目录（可选，用于保存中间结果）

        Returns:
            Dict: 解析结果
                {
                    "success": True/False,
                    "data": {
                        "db_format": {...},  # 数据库格式数据
                        "validation_results": [...]  # 校验结果列表
                    },
                    "error": "错误信息（如果失败）",
                    "process_time": 处理时间（秒）,
                    "retry_count": 实际重试次数
                }
        """
        start_time = datetime.now()
        logger.info("=" * 60)
        logger.info(f"开始带验证的PDF解析: {pdf_path}")
        logger.info(f"最大重试次数: {max_retries}")
        logger.info("=" * 60)

        retry_count = 0
        all_validation_passed = False
        db_data = None
        validation_results = None

        try:
            while retry_count <= max_retries and not all_validation_passed:
                logger.info(f"第 {retry_count + 1} 次识别")
                
                # 解析PDF
                parse_result = self.parse_pdf(pdf_path, output_dir)
                
                if not parse_result["success"]:
                    raise Exception(f"PDF解析失败: {parse_result['error']}")
                
                # 转换为数据库格式并进行校验
                db_data, validation_results = self.convert_to_database_format(parse_result["data"])
                
                # 检查所有校验是否通过
                all_validation_passed = all(result["valid"] for result in validation_results)
                
                if all_validation_passed:
                    logger.info("✅ 所有板块总计校验通过")
                    break
                else:
                    logger.warning("❌ 部分板块总计校验失败")
                    retry_count += 1
                    
                    if retry_count > max_retries:
                        logger.warning(f"已达到最大重试次数 {max_retries}，停止重新识别")
                        break
                    else:
                        logger.info(f"准备进行第 {retry_count + 1} 次重新识别...")
        
        except Exception as e:
            end_time = datetime.now()
            process_time = (end_time - start_time).total_seconds()
            logger.error(f"带验证的PDF解析失败: {e}")
            return {
                "success": False,
                "data": None,
                "error": str(e),
                "process_time": process_time,
                "retry_count": retry_count
            }

        end_time = datetime.now()
        process_time = (end_time - start_time).total_seconds()

        logger.info("=" * 60)
        logger.info(f"带验证的PDF解析完成！耗时: {process_time:.2f}秒")
        logger.info(f"实际重试次数: {retry_count}")
        logger.info("=" * 60)

        # 生成校验问题信息
        validation_issues = self._format_validation_issues(validation_results)
        
        return {
            "success": True,
            "data": {
                "db_format": db_data,
                "validation_results": validation_results,
                "validation_issues": validation_issues
            },
            "error": None,
            "process_time": process_time,
            "retry_count": retry_count
        }
    
    def _format_validation_issues(self, validation_results: List[Dict[str, Any]]) -> str:
        """将校验结果格式化为适合存储的文本格式.
        
        Args:
            validation_results: 校验结果列表
            
        Returns:
            str: 格式化的校验问题信息
        """
        failed_results = [result for result in validation_results if not result["valid"]]
        
        if not failed_results:
            return ""
        
        issues = []
        for result in failed_results:
            issues.append(f"{result['section']}: 如不完整")
        
        return "\n".join(issues)

    def parse_pdf(
        self,
        pdf_path: str,
        output_dir: Optional[str] = None
    ) -> Dict[str, Any]:
        """解析PDF文件（完整流程）.

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
        logger.info(f"开始解析PDF: {pdf_path}")
        logger.info("=" * 60)

        try:
            # 初始化OCR引擎
            self._init_ocr_engine()

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

            # Step 3: 提取关键词Y坐标
            logger.info("Step 3: 提取关键词Y坐标...")
            keyword_extractor = KeywordExtractor(self.ocr_engine)
            ocr_results = self.ocr_engine.recognize_image(left_image)
            keyword_map = keyword_extractor.extract_keywords_positions(left_image, ocr_results)
            logger.info(f"  ✓ 识别到 {len(keyword_map)} 个关键词")

            # Step 4: 左侧图片板块切分
            logger.info("Step 4: 左侧图片板块切分...")
            cutter = LeftSectionCutter()
            section_ranges = cutter.calculate_section_ranges(keyword_map, left_image.shape[0])

            # 直接在内存中切分，不保存文件
            section_images = {}
            for section_name, (start_y, end_y) in section_ranges.items():
                section_images[section_name] = left_image[start_y:end_y, :]
            logger.info(f"  ✓ 切分为 {len(section_images)} 个板块")

            # Step 5: 左侧OCR识别
            logger.info("Step 5: 左侧OCR识别...")
            left_ocr = LeftSectionOCR(self.ocr_engine)
            left_data = left_ocr.process_all_sections(section_images)
            logger.info(f"  ✓ 提取到 {len(left_data)} 个板块数据")

            # Step 6: 右侧OCR识别
            logger.info("Step 6: 右侧OCR识别...")
            right_ocr = RightSectionOCR(self.ocr_engine)
            right_data = right_ocr.process_right_image(right_image)
            logger.info(f"  ✓ 提取到付款详情")

            # 整合数据
            result_data = {
                "left_section": left_data,
                "right_section": right_data
            }

            # 保存中间结果（可选）
            if output_dir:
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
            logger.info(f"✅ PDF解析完成！耗时: {process_time:.2f}秒")
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
            logger.error(f"❌ PDF解析失败: {e}")
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

    def _validate_total(self, section_data: Dict[str, Decimal], section_name: str) -> Dict[str, Any]:
        """验证板块字段和是否等于总计.

        Args:
            section_data: 板块数据
            section_name: 板块名称

        Returns:
            Dict: 校验结果
                {
                    "valid": bool,  # 是否校验通过
                    "message": str,  # 校验消息
                    "section": str,  # 板块名称
                    "total": Decimal,  # 实际总计
                    "calculated_total": Decimal  # 计算总和
                }
        """
        # 定义各板块需要参与计算的字段
        section_fields = {
            "sales": ["product_price", "shipping", "wfs_shipping_refund", "net_tax_collected", 
                      "net_commission", "withholding_tax", "wfs_shipping_tax_refund", 
                      "walmart_funded_savings"],
            "refund": ["product_price", "shipping", "net_tax_collected", "commission", 
                       "withholding_tax", "walmart_funded_savings"],
            "adjustment": ["global_shipping_label_fee"],
            "wfs": ["wfs_fee", "wfs_ethereum_fee", "wfs_total_discount"],
            "other_activity": ["walmart_product_ads"]
        }
        
        if section_name not in section_fields:
            return {
                "valid": True,
                "message": "未知板块，跳过校验",
                "section": section_name,
                "total": section_data.get("total"),
                "calculated_total": None
            }
            
        # 计算字段总和
        fields_to_sum = section_fields[section_name]
        calculated_total = Decimal("0.00")
        
        for field in fields_to_sum:
            if field in section_data:
                calculated_total += section_data[field]
        
        # 添加低频字段汇总（如果有）
        if "other_total" in section_data:
            calculated_total += section_data["other_total"]
        
        # 处理total字段缺失的情况
        if "total" not in section_data:
            # 自动填充总计字段
            section_data["total"] = calculated_total
            return {
                "valid": True,
                "message": f"板块 '{section_name}' 总计字段缺失，已自动填充为计算总和",
                "section": section_name,
                "total": calculated_total,
                "calculated_total": calculated_total
            }
        
        # 获取板块总计
        total = section_data["total"]
        
        # 允许0.01的误差
        if abs(total - calculated_total) > Decimal("0.01"):
            message = f"板块 '{section_name}' 总计校验失败: 实际总计={total}, 计算总和={calculated_total}, 差异={abs(total - calculated_total)}"
            logger.warning(message)
            return {
                "valid": False,
                "message": message,
                "section": section_name,
                "total": total,
                "calculated_total": calculated_total
            }
        else:
            message = f"板块 '{section_name}' 总计校验通过: 实际总计={total}, 计算总和={calculated_total}"
            logger.info(message)
            return {
                "valid": True,
                "message": message,
                "section": section_name,
                "total": total,
                "calculated_total": calculated_total
            }

    def convert_to_database_format(self, parsed_data: Dict[str, Any]) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """将解析结果转换为数据库格式，并进行总计校验.

        Args:
            parsed_data: 解析结果（包含left_section和right_section）

        Returns:
            Tuple[Dict[str, Any], List[Dict[str, Any]]]: 
                - 数据库格式的数据
                - 校验结果列表
        """
        left_section = parsed_data.get("left_section", {})
        right_section = parsed_data.get("right_section", {})

        db_data = {}
        validation_results = []

        # 预处理所有板块的字段名
        preprocessed_left_section = {}
        for section_name, section_data in left_section.items():
            if isinstance(section_data, dict):
                preprocessed_data = {}
                for field_name, field_value in section_data.items():
                    preprocessed_name = field_name
                    preprocessed_data[preprocessed_name] = field_value
                preprocessed_left_section[section_name] = preprocessed_data
            else:
                preprocessed_left_section[section_name] = section_data

        # 预处理右侧数据的字段名
        preprocessed_right_section = {}
        for section_name, section_data in right_section.items():
            if isinstance(section_data, dict):
                preprocessed_data = {}
                for field_name, field_value in section_data.items():
                    preprocessed_name = field_name
                    preprocessed_data[preprocessed_name] = field_value
                preprocessed_right_section[section_name] = preprocessed_data
            else:
                preprocessed_right_section[section_name] = section_data

        # 转换header数据
        if "header" in preprocessed_left_section:
            db_data["header"] = self._convert_header(preprocessed_left_section["header"])

        # 转换sales数据
        if "sales" in preprocessed_left_section:
            db_data["sales"] = self._convert_sales(preprocessed_left_section["sales"])
            validation_results.append(self._validate_total(db_data["sales"], "sales"))

        # 转换refund数据
        if "refund" in preprocessed_left_section:
            db_data["refund"] = self._convert_refund(preprocessed_left_section["refund"])
            validation_results.append(self._validate_total(db_data["refund"], "refund"))

        # 转换adjustment数据
        if "adjustment" in preprocessed_left_section:
            db_data["adjustment"] = self._convert_adjustment(preprocessed_left_section["adjustment"])
            validation_results.append(self._validate_total(db_data["adjustment"], "adjustment"))

        # 转换wfs数据
        if "wfs" in preprocessed_left_section:
            db_data["wfs"] = self._convert_wfs(preprocessed_left_section["wfs"])
            validation_results.append(self._validate_total(db_data["wfs"], "wfs"))

        # 转换other数据
        if "other" in preprocessed_left_section:
            db_data["other_activity"] = self._convert_other_activity(preprocessed_left_section["other"])
            validation_results.append(self._validate_total(db_data["other_activity"], "other_activity"))

        # 转换footer数据
        if "footer" in preprocessed_left_section:
            db_data["footer"] = self._convert_footer(preprocessed_left_section["footer"])

        # 转换payment数据
        if "payment_details" in preprocessed_right_section:
            db_data["payment"] = self._convert_payment(preprocessed_right_section["payment_details"])

        return db_data, validation_results

    def _parse_chinese_date(self, date_str: str) -> Optional[date]:
        """解析中文日期字符串.

        Args:
            date_str: 中文日期，如"2025年1月14日"

        Returns:
            Optional[date]: 解析后的日期对象
        """
        if not date_str:
            return None

        try:
            # 移除空格
            date_str = date_str.replace(" ", "")
            # 提取年月日
            import re
            match = re.search(r'(\d{4})年(\d{1,2})月(\d{1,2})日', date_str)
            if match:
                year = int(match.group(1))
                month = int(match.group(2))
                day = int(match.group(3))
                return date(year, month, day)
        except Exception as e:
            logger.warning(f"日期解析失败: {date_str}, 错误: {e}")
            return None

    def _convert_header(self, header_data: Dict[str, str]) -> Dict[str, Any]:
        """转换header数据."""
        return {
            "start_date": self._parse_chinese_date(header_data.get("开始日期", "")),
            "end_date": self._parse_chinese_date(header_data.get("结束日期", "")),
            "opening_balance": Decimal(_safe_decimal(header_data.get("期初余额", "0.00"))),
            "reserve_funds": Decimal(_safe_decimal(header_data.get("备用金", "0.00"))),
            "awaiting_payment": Decimal(_safe_decimal(header_data.get("回款等待", "0.00")))
        }

    def _convert_sales(self, sales_data: Dict[str, str]) -> Dict[str, Decimal]:
        """转换sales数据."""
        # 处理总计字段（预处理后统一为"总计"）
        total_value = sales_data.get("总计", "0.00")
        
        # 处理WFS运输退款字段（预处理后无空格）
        wfs_shipping_refund_value = sales_data.get("WFS运输退款", "0.00")
        
        # 处理WFS运输税退款字段（预处理后无空格）
        wfs_shipping_tax_refund_value = sales_data.get("WFS运输税退款", "0.00")
        
        # 处理沃尔玛出资的节余字段（预处理后统一）
        walmart_funded_savings_value = sales_data.get("沃尔玛出资的节余", "0.00")
        if not walmart_funded_savings_value or walmart_funded_savings_value == "0.00":
            walmart_funded_savings_value = sales_data.get("T沃尔玛出资的节余", "0.00")
                
        return {
            "product_price": Decimal(_safe_decimal(sales_data.get("产品价格", "0.00"))),
            "shipping": Decimal(_safe_decimal(sales_data.get("运输", "0.00"))),
            "wfs_shipping_refund": Decimal(_safe_decimal(wfs_shipping_refund_value)),
            "net_tax_collected": Decimal(_safe_decimal(sales_data.get("已收税净额", "0.00"))),
            "net_commission": Decimal(_safe_decimal(sales_data.get("净佣金", "0.00"))),
            "withholding_tax": Decimal(_safe_decimal(sales_data.get("扣缴税款净额", "0.00"))),
            "wfs_shipping_tax_refund": Decimal(_safe_decimal(wfs_shipping_tax_refund_value)),
            "walmart_funded_savings": Decimal(_safe_decimal(walmart_funded_savings_value)),
            "total": Decimal(_safe_decimal(total_value)),
            "other_total": Decimal("0.00")  # 其他低频字段汇总，初始化为0
        }

    def _convert_refund(self, refund_data: Dict[str, str]) -> Dict[str, Decimal]:
        """转换refund数据."""
        # 处理总计字段（预处理后统一为"总计"）
        total_value = refund_data.get("总计", "0.00")
                
        return {
            "product_price": Decimal(_safe_decimal(refund_data.get("产品价格", "0.00"))),
            "shipping": Decimal(_safe_decimal(refund_data.get("运输", "0.00"))),
            "net_tax_collected": Decimal(_safe_decimal(refund_data.get("已收税净额", "0.00"))),
            "commission": Decimal(_safe_decimal(refund_data.get("佣金", "0.00"))),
            "withholding_tax": Decimal(_safe_decimal(refund_data.get("扣缴税款净额", "0.00"))),
            "walmart_funded_savings": Decimal(_safe_decimal(refund_data.get("沃尔玛出资的节余", "0.00"))),
            "total": Decimal(_safe_decimal(total_value)),
            "other_total": Decimal("0.00")  # 其他低频字段汇总
        }

    def _convert_adjustment(self, adjustment_data: Dict[str, str]) -> Dict[str, Decimal]:
        """转换adjustment数据."""
        # 处理总计字段（预处理后统一为"总计"）
        total_value = adjustment_data.get("总计", "0.00")
                
        return {
            "global_shipping_label_fee": Decimal(_safe_decimal(adjustment_data.get("沃尔玛全球运输标签服务费", "0.00"))),
            "total": Decimal(_safe_decimal(total_value)),
            "other_total": Decimal("0.00")  # 其他低频字段汇总
        }

    def _convert_wfs(self, wfs_data: Dict[str, str]) -> Dict[str, Decimal]:
        """转换wfs数据."""
        # 处理总计字段（预处理后统一为"总计"）
        total_value = wfs_data.get("总计", "0.00")
                
        return {
            "wfs_fee": Decimal(_safe_decimal(wfs_data.get("沃尔玛商品服务（WFS）费用", "0.00"))),
            "wfs_ethereum_fee": Decimal(_safe_decimal(wfs_data.get("WFS以太坊费", "0.00"))),
            "wfs_total_discount": Decimal(_safe_decimal(wfs_data.get("WFS总折扣", "0.00"))),
            "total": Decimal(_safe_decimal(total_value)),
            "other_total": Decimal("0.00")  # 其他低频字段汇总
        }

    def _convert_other_activity(self, other_data: Dict[str, str]) -> Dict[str, Decimal]:
        """转换other_activity数据."""
        # 处理总计字段（预处理后统一为"总计"）
        total_value = other_data.get("总计", "0.00")
                
        return {
            "walmart_product_ads": Decimal(_safe_decimal(other_data.get("沃尔玛产品广告费用", "0.00"))),
            "total": Decimal(_safe_decimal(total_value)),
            "other_total": Decimal("0.00")  # 其他低频字段汇总
        }

    def _convert_footer(self, footer_data: Dict[str, str]) -> Dict[str, Decimal]:
        """转换footer数据."""
        return {
            "amount_paid_to_you": Decimal(_safe_decimal(footer_data.get("向您支付的金额", "0.00"))),
            "closing_balance": Decimal(_safe_decimal(footer_data.get("期末余额", "0.00"))),
            "other_total": Decimal("0.00")  # 其他低频字段汇总
        }

    def _convert_payment(self, payment_data: Dict[str, str]) -> Dict[str, Any]:
        """转换payment数据."""
        # 解析付款日期
        payment_date_str = payment_data.get("付款日期", "")
        payment_date = None
        if payment_date_str:
            # 尝试解析日期（可能包含时区信息）
            payment_date = self._parse_chinese_date(payment_date_str)

        return {
            "status": payment_data.get("状态", ""),
            "payment_date": payment_date,
            "payment_frequency": payment_data.get("周期付款", ""),
            "payment_method": payment_data.get("付款方式", ""),
            "device_method": payment_data.get("设备方式", ""),
            "amount_to_be_paid": Decimal(_safe_decimal(payment_data.get("待付款金额", "0.00"))),
            "amount_waiting_return": Decimal(_safe_decimal(payment_data.get("等待回款金额", "0.00"))),
            "return_waiting_period": payment_data.get("回款等待期", ""),
            "warning_message": payment_data.get("警告信息")
        }


# ============================================================
# END OF pdf_parser_service.py
# ============================================================
