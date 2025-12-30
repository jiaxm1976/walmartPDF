# ============================================================
# 文件: backend/app/services/ocr_engine.py
# 功能: OCR识别引擎封装类
# 作者: 开发团队
# 创建时间: 2025-12-13
# 最后修改: 2025-12-25
# 说明: 支持多种OCR引擎（Apple Vision和PaddleOCR）
# ============================================================

import logging
from typing import List, Dict, Any, Tuple, Optional
from backend.app.utils.text_formatter import format_text
import numpy as np
from pathlib import Path
import pickle

# 创建logger实例
logger = logging.getLogger(__name__)

# 导入配置
from backend.app.config import settings


class OCREngine:
    """OCR识别引擎类（支持多种引擎）.

    根据配置选择不同的OCR引擎实现：
    - Apple Vision (macOS原生，性能优异)
    - PaddleOCR (跨平台，支持多语言)

    Attributes:
        confidence_threshold: 置信度阈值（低于此值的结果会被过滤）
        calibration_func: Y坐标校准函数
        engine_type: OCR引擎类型
    """

    def __init__(
        self,
        confidence_threshold: float = 0.25,
        engine_type: str = None
    ):
        """初始化OCR引擎.

        Args:
            confidence_threshold: 置信度阈值，默认0.5
            engine_type: OCR引擎类型，默认从配置读取
        """
        logger.info("=" * 60)
        
        # 从配置或参数获取引擎类型
        self.engine_type = engine_type or settings.OCR_ENGINE
        logger.info(f"初始化OCR引擎 ({self.engine_type})")
        logger.info("=" * 60)

        self.confidence_threshold = confidence_threshold

        # 根据引擎类型初始化
        if self.engine_type == "vision":
            self._init_vision_engine()
        elif self.engine_type == "paddleocr":
            self._init_paddleocr_engine()
        else:
            raise ValueError(f"不支持的OCR引擎类型: {self.engine_type}")

        logger.info(f"置信度阈值: {confidence_threshold}")
        logger.info("OCR引擎初始化成功")

        # 加载坐标校准函数
        self.calibration_func = None
        self._load_default_calibration()
    
    def _init_vision_engine(self):
        """初始化Apple Vision OCR引擎."""
        # 导入Vision框架
        try:
            import Vision
            from Quartz import CGImageSourceCreateWithData, kCGImageSourceShouldCache
            from Foundation import NSData, NSURL, NSMutableDictionary
            import objc
        except ImportError as e:
            logger.error("Vision框架导入失败，自动回退到PaddleOCR引擎")
            # Vision框架不可用时，自动回退到PaddleOCR引擎
            self.engine_type = "paddleocr"
            self._init_paddleocr_engine()
            return

        self.Vision = Vision
        self.CGImageSourceCreateWithData = CGImageSourceCreateWithData
        self.kCGImageSourceShouldCache = kCGImageSourceShouldCache
        self.NSData = NSData
        self.objc = objc
    
    def _init_paddleocr_engine(self):
        """初始化PaddleOCR引擎."""
        logger.info("初始化PaddleOCR引擎")
        try:
            from paddleocr import PaddleOCR
        except ImportError as e:
            logger.error("PaddleOCR导入失败，请确保已安装paddleocr")
            raise ImportError("PaddleOCR不可用") from e

        # 初始化PaddleOCR，使用英文和中文模型
        self.paddle_ocr = PaddleOCR(
            use_angle_cls=True,
            lang="ch",
            show_log=False
        )


    def _load_default_calibration(self):
        """加载默认的坐标校准函数."""
        try:
            # 尝试加载300 DPI的校准文件
            calibration_file = Path(__file__).parent.parent.parent.parent / 'calibration_data' / 'ocr_calibration_300dpi.pkl'

            if calibration_file.exists():
                with open(calibration_file, 'rb') as f:
                    calibration_data = pickle.load(f)
                    # 尝试两个可能的键名（兼容旧版本）
                    self.calibration_func = calibration_data.get('calibration_func') or \
                                           calibration_data.get('calibration_function')

                if self.calibration_func:
                    logger.info(f"已加载坐标校准函数: {calibration_file}")
                else:
                    logger.warning(
                        f"校准文件中未找到校准函数，"
                        f"可用的键: {list(calibration_data.keys())}"
                    )
            else:
                logger.warning(f"校准文件不存在: {calibration_file}")

        except Exception as e:
            logger.warning(f"加载校准函数失败: {e}")


    def calibrate_y_coordinate(self, y_raw: int) -> int:
        """对OCR识别的Y坐标进行校准.

        Args:
            y_raw: OCR原始识别的Y坐标

        Returns:
            int: 校准后的Y坐标
        """
        if self.calibration_func is None:
            return y_raw

        try:
            y_calibrated = int(self.calibration_func(y_raw))
            return y_calibrated
        except Exception as e:
            logger.warning(f"坐标校准失败: {e}，返回原始坐标")
            return y_raw


    def recognize_image(self, image: np.ndarray, confidence_threshold: float = None, preprocess: bool = False) -> List[Tuple[List, Tuple[str, float]]]:
        """识别图片中的文字.

        Args:
            image: 输入图片（numpy数组，BGR格式）
            confidence_threshold: 置信度阈值，优先级高于实例默认值
            preprocess: 是否对图片进行预处理

        Returns:
            List[Tuple]: OCR识别结果列表
                [
                    (box, (text, confidence)),
                    ...
                ]
                其中box为[[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
        """
        # 应用图片预处理
        if preprocess:
            try:
                from backend.app.utils.image_utils import preprocess_image
                image = preprocess_image(image, enhance=True)
                logger.debug("图片预处理完成")
            except Exception as e:
                logger.warning(f"图片预处理失败: {e}")
        
        # 使用指定的置信度阈值或默认值
        original_threshold = self.confidence_threshold
        if confidence_threshold is not None:
            self.confidence_threshold = confidence_threshold
        
        try:
            if self.engine_type == "vision":
                return self._recognize_image_vision(image)
            elif self.engine_type == "paddleocr":
                return self._recognize_image_paddleocr(image)
            else:
                logger.error(f"不支持的OCR引擎类型: {self.engine_type}")
                return []
        finally:
            # 恢复原始置信度阈值
            if confidence_threshold is not None:
                self.confidence_threshold = original_threshold
            
    def recognize_image_text(self, image: np.ndarray) -> List[str]:
        """识别图片中的文字，只返回整个文本块内容.

        Args:
            image: 输入图片（numpy数组，BGR格式）

        Returns:
            List[str]: OCR识别的文本块列表，按Y坐标从上到下排序
        """
        # 获取完整的OCR识别结果
        ocr_results = self.recognize_image(image)
        
        # 提取文本内容
        text_blocks = []
        for box, (text, confidence) in ocr_results:
            text_blocks.append(text)
        
        logger.info(f"recognize_image_text返回 {len(text_blocks)} 个文本块")
        return text_blocks
    
    def _process_text(self, text: str) -> str:
        """处理文本，应用格式化规则.
        
        调用独立的文本格式化工具进行处理。
        """
        return format_text(text)

    def _recognize_image_vision(self, image: np.ndarray) -> List[Tuple[List, Tuple[str, float]]]:
        """使用Apple Vision引擎识别图片中的文字."""
        import cv2

        # 转换为PNG格式的字节数据
        success, encoded_image = cv2.imencode('.png', image)
        if not success:
            logger.error("图片编码失败")
            return []

        image_data = encoded_image.tobytes()

        # 创建NSData
        ns_data = self.NSData.dataWithBytes_length_(image_data, len(image_data))

        # 创建CGImageSource
        from Quartz import CGImageSourceCreateImageAtIndex
        image_source = self.CGImageSourceCreateWithData(ns_data, None)
        if not image_source:
            logger.error("无法创建CGImageSource")
            return []

        # 获取CGImage
        cg_image = CGImageSourceCreateImageAtIndex(image_source, 0, None)
        if not cg_image:
            logger.error("无法创建CGImage")
            return []

        # 创建文字识别请求
        request = self.Vision.VNRecognizeTextRequest.alloc().init()
        request.setRecognitionLevel_(self.Vision.VNRequestTextRecognitionLevelAccurate)
        request.setRecognitionLanguages_(["zh-Hans", "en-US"])  # 简体中文和英文
        request.setUsesLanguageCorrection_(False)  # 禁用语言校正，提高速度

        # 创建请求处理器
        handler = self.Vision.VNImageRequestHandler.alloc().initWithCGImage_options_(cg_image, None)

        # 执行识别
        error = None
        success = handler.performRequests_error_([request], self.objc.nil)

        if not success:
            logger.error("Vision OCR识别失败")
            return []

        # 解析结果
        results = []
        observations = request.results()

        if not observations:
            logger.warning("OCR未识别到任何文字")
            return []

        height = image.shape[0]

        for observation in observations:
            # 获取识别文本
            top_candidate = observation.topCandidates_(1)[0]
            text = top_candidate.string()
            confidence = float(top_candidate.confidence())

            # 过滤低置信度结果
            if confidence < self.confidence_threshold:
                continue

            # 应用文本处理规则
            processed_text = self._process_text(text)

            # 获取边界框（归一化坐标，原点在左下角）
            bounding_box = observation.boundingBox()
            x = float(bounding_box.origin.x)
            y = float(bounding_box.origin.y)
            w = float(bounding_box.size.width)
            h = float(bounding_box.size.height)

            # 转换为图片坐标系（原点在左上角）
            image_width = image.shape[1]
            image_height = image.shape[0]

            # Vision坐标：(0,0)在左下角，y向上增加
            # 图片坐标：(0,0)在左上角，y向下增加
            x1 = int(x * image_width)
            y1 = int((1 - y - h) * image_height)  # 转换Y坐标
            x2 = int((x + w) * image_width)
            y2 = int((1 - y) * image_height)

            # 构建四角坐标（按PaddleOCR格式）
            box = [
                [x1, y1],  # 左上
                [x2, y1],  # 右上
                [x2, y2],  # 右下
                [x1, y2]   # 左下
                
            ]

            results.append((box, (processed_text, confidence)))

        logger.info(f"Vision OCR识别完成，检测到 {len(results)} 个文本块")
        #logger.info(f"==============================/n: {results}")


        return results
    
    def _recognize_image_paddleocr(self, image: np.ndarray) -> List[Tuple[List, Tuple[str, float]]]:
        """使用PaddleOCR引擎识别图片中的文字."""
        logger.info("使用PaddleOCR引擎识别图片")
        try:
            # PaddleOCR识别
            result = self.paddle_ocr.ocr(image, cls=True)
            ocr_results = []
            
            # 解析PaddleOCR结果
            if result and result[0]:
                for line in result[0]:
                    box = line[0]  # [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
                    text = line[1][0]  # 识别的文本
                    confidence = line[1][1]  # 置信度
                    
                    # 过滤低置信度结果
                    if confidence < self.confidence_threshold:
                        continue
                    
                    # 应用文本处理规则
                    processed_text = self._process_text(text)
                    
                    ocr_results.append((box, (processed_text, confidence)))
            
            logger.info(f"PaddleOCR识别完成，检测到 {len(ocr_results)} 个文本块")
            return ocr_results
        except Exception as e:
            logger.error(f"PaddleOCR识别失败: {e}")
            return []


# ============================================================
# END OF ocr_engine.py
# ============================================================