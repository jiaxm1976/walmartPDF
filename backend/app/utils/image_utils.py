# ============================================================
# 文件: backend/app/utils/image_utils.py
# 功能: 图像处理工具函数
# 作者: 开发团队
# 创建时间: 2025-12-13
# 最后修改: 2025-12-13
# 说明: 提供PDF转图片、图像预处理等工具函数
# ============================================================

import logging  # 日志记录
from typing import List, Tuple, Optional  # 类型提示
from pathlib import Path  # 路径处理
import os  # 操作系统接口

# 创建logger实例
logger = logging.getLogger(__name__)


def pdf_to_images(
    pdf_path: str,
    dpi: int = 600,
    output_dir: Optional[str] = None,
    save_images: bool = True,
    grayscale: bool = True
) -> List:
    """将PDF转换为高分辨率图片.

    Args:
        pdf_path: PDF文件路径
        dpi: 分辨率（默认600 DPI，确保OCR准确率）
        output_dir: 输出目录（可选），如果不指定则不保存
        save_images: 是否保存图片到磁盘
        grayscale: 是否转换为灰度图（默认True，提高OCR准确率）

    Returns:
        list: PIL Image对象列表

    Raises:
        ImportError: 当pdf2image未安装时
        FileNotFoundError: 当PDF文件不存在时

    Example:
        >>> images = pdf_to_images('statement.pdf', dpi=600, grayscale=True)
        >>> print(f"转换了 {len(images)} 页")
    """
    try:
        # 导入pdf2image
        from pdf2image import convert_from_path
    except ImportError:
        logger.error("pdf2image未安装，请运行: pip install pdf2image")
        logger.error("还需要安装poppler: https://github.com/oschwartz10612/poppler-windows/releases/")
        raise

    # 检查PDF文件是否存在
    pdf_path_obj = Path(pdf_path)
    if not pdf_path_obj.exists():
        raise FileNotFoundError(f"PDF文件不存在: {pdf_path}")

    logger.info(f"开始转换PDF: {pdf_path_obj.name}")
    logger.info(f"  分辨率: {dpi} DPI")
    logger.info(f"  灰度模式: {'开启' if grayscale else '关闭'}")

    try:
        # 转换PDF为图片
        # dpi: 分辨率，越高质量越好但文件越大
        # fmt: 输出格式
        # grayscale: 灰度模式，可以提高OCR准确率（蓝色/彩色文字更清晰）
        # 注意：需要在系统PATH中配置poppler路径，或者通过环境变量指定
        # Windows: 将poppler的bin目录添加到系统PATH
        # 如果已配置系统环境变量，则不需要指定poppler_path参数
        images = convert_from_path(
            pdf_path,
            dpi=dpi,
            fmt='png',  # PNG格式保留更多细节
            grayscale=grayscale  # 转换为灰度图，提高OCR准确率
        )

        logger.info(f"  成功转换 {len(images)} 页")

        # 如果需要保存图片
        if save_images and output_dir:
            # 创建输出目录
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)

            # 生成基础文件名（使用PDF文件名）
            base_name = pdf_path_obj.stem

            # 保存每一页
            for i, image in enumerate(images, start=1):
                # 生成文件名：基础名_页码.png
                image_filename = f"{base_name}_page_{i}.png"
                image_path = output_path / image_filename

                # 保存图片
                image.save(str(image_path), 'PNG')
                logger.debug(f"  保存: {image_filename}")

            logger.info(f"  图片已保存到: {output_dir}")

        return images

    except Exception as e:
        logger.error(f"PDF转换失败: {e}")
        raise


def preprocess_image(image, enhance: bool = True):
    """图像预处理，提高OCR准确率.

    处理步骤：
    1. 灰度化
    2. 二值化（自适应阈值）
    3. 降噪
    4. 对比度增强（可选）

    Args:
        image: PIL Image对象或numpy数组
        enhance: 是否进行对比度增强

    Returns:
        numpy.ndarray: 预处理后的图像数组

    Example:
        >>> processed = preprocess_image(image)
    """
    try:
        # 导入必要的库
        import numpy as np
        import cv2
        from PIL import Image

        # 转换为numpy数组
        if isinstance(image, Image.Image):
            # PIL Image转numpy
            img_array = np.array(image)
        else:
            # 假设已经是numpy数组
            img_array = image

        # 1. 灰度化（如果是彩色图片）
        if len(img_array.shape) == 3:
            # RGB转灰度
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            logger.debug("  - 灰度化完成")
        else:
            gray = img_array

        # 2. 二值化（自适应阈值）
        # 使用自适应阈值可以处理光照不均匀的情况
        binary = cv2.adaptiveThreshold(
            gray,
            255,  # 最大值
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,  # 自适应方法
            cv2.THRESH_BINARY,  # 二值化类型
            11,  # 邻域大小
            2   # 常数C
        )
        logger.debug("  - 二值化完成")

        # 3. 降噪
        # 使用形态学操作去除小噪点
        kernel = np.ones((2, 2), np.uint8)
        denoised = cv2.morphologyEx(
            binary,
            cv2.MORPH_CLOSE,  # 闭运算（先膨胀后腐蚀）
            kernel
        )
        logger.debug("  - 降噪完成")

        # 4. 对比度增强（可选）
        if enhance:
            # 使用CLAHE（限制对比度自适应直方图均衡化）增强对比度
            # 比普通直方图均衡化效果更好，避免过度增强
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(denoised)
            
            # 5. 锐化处理，增强边缘和细节
            sharpening_kernel = np.array([[0, -1, 0],
                                         [-1, 5, -1],
                                         [0, -1, 0]])
            sharpened = cv2.filter2D(enhanced, -1, sharpening_kernel)
            
            logger.debug("  - 对比度增强完成")
            logger.debug("  - 锐化处理完成")
            return sharpened
        else:
            return denoised

    except Exception as e:
        logger.error(f"图像预处理失败: {e}")
        # 预处理失败时返回原图
        return np.array(image) if isinstance(image, Image.Image) else image


def crop_image_region(
    image,
    region: Tuple[int, int, int, int]
) -> any:
    """裁剪图片指定区域.

    Args:
        image: PIL Image对象或numpy数组
        region: 区域坐标 (x, y, width, height)

    Returns:
        裁剪后的图像（类型与输入相同）

    Example:
        >>> region = (100, 200, 500, 300)  # x, y, width, height
        >>> cropped = crop_image_region(image, region)
    """
    try:
        from PIL import Image
        import numpy as np

        # 提取坐标
        x, y, w, h = region

        # 根据输入类型处理
        if isinstance(image, Image.Image):
            # PIL Image使用crop方法
            # 注意：crop接受 (left, top, right, bottom)
            cropped = image.crop((x, y, x + w, y + h))
            logger.debug(f"  裁剪区域: ({x}, {y}, {w}, {h})")
            return cropped

        elif isinstance(image, np.ndarray):
            # numpy数组使用切片
            # 注意：numpy是 [y:y+h, x:x+w]
            cropped = image[y:y+h, x:x+w]
            logger.debug(f"  裁剪区域: ({x}, {y}, {w}, {h})")
            return cropped

        else:
            raise TypeError(f"不支持的图像类型: {type(image)}")

    except Exception as e:
        logger.error(f"图像裁剪失败: {e}")
        raise


def save_image(image, output_path: str, format: str = 'PNG'):
    """保存图片到文件.

    Args:
        image: PIL Image对象或numpy数组
        output_path: 输出文件路径
        format: 图片格式（PNG/JPEG等）

    Example:
        >>> save_image(image, 'output/region_1.png')
    """
    try:
        from PIL import Image
        import numpy as np

        # 确保输出目录存在
        output_dir = Path(output_path).parent
        output_dir.mkdir(parents=True, exist_ok=True)

        # 根据输入类型处理
        if isinstance(image, Image.Image):
            # 直接保存PIL Image
            image.save(output_path, format)
        elif isinstance(image, np.ndarray):
            # numpy数组转PIL Image后保存
            pil_image = Image.fromarray(image)
            pil_image.save(output_path, format)
        else:
            raise TypeError(f"不支持的图像类型: {type(image)}")

        logger.debug(f"  图片已保存: {output_path}")

    except Exception as e:
        logger.error(f"保存图片失败: {e}")
        raise


def get_image_info(image) -> dict:
    """获取图片信息.

    Args:
        image: PIL Image对象或numpy数组

    Returns:
        dict: 图片信息，包含width, height, mode等

    Example:
        >>> info = get_image_info(image)
        >>> print(f"尺寸: {info['width']}x{info['height']}")
    """
    try:
        from PIL import Image
        import numpy as np

        if isinstance(image, Image.Image):
            # PIL Image
            return {
                'width': image.width,
                'height': image.height,
                'mode': image.mode,
                'format': image.format,
                'type': 'PIL.Image'
            }

        elif isinstance(image, np.ndarray):
            # numpy数组
            height, width = image.shape[:2]
            channels = image.shape[2] if len(image.shape) > 2 else 1

            return {
                'width': width,
                'height': height,
                'channels': channels,
                'dtype': str(image.dtype),
                'type': 'numpy.ndarray'
            }

        else:
            raise TypeError(f"不支持的图像类型: {type(image)}")

    except Exception as e:
        logger.error(f"获取图片信息失败: {e}")
        return {}


# ============================================================
# ImageProcessor类（包装类）
# ============================================================

class ImageProcessor:
    """图像处理器类.

    封装图像处理函数，提供面向对象的接口。
    """

    def pdf_to_images(self, *args, **kwargs):
        """PDF转图片"""
        return pdf_to_images(*args, **kwargs)

    def preprocess_image(self, *args, **kwargs):
        """图像预处理"""
        return preprocess_image(*args, **kwargs)

    def crop_image_region(self, *args, **kwargs):
        """裁剪图像区域"""
        return crop_image_region(*args, **kwargs)

    def save_image(self, *args, **kwargs):
        """保存图片"""
        return save_image(*args, **kwargs)

    def get_image_info(self, *args, **kwargs):
        """获取图片信息"""
        return get_image_info(*args, **kwargs)


if __name__ == "__main__":
    # 测试代码
    import sys

    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    if len(sys.argv) > 1:
        # 从命令行参数获取PDF路径
        pdf_path = sys.argv[1]

        try:
            # 测试PDF转图片
            print("=" * 60)
            print("测试PDF转图片功能")
            print("=" * 60)

            images = pdf_to_images(
                pdf_path,
                dpi=600,
                output_dir='test_output',
                save_images=True
            )

            print(f"\n成功转换 {len(images)} 页")

            # 测试图像信息
            if images:
                info = get_image_info(images[0])
                print(f"\n第一页信息:")
                print(f"  尺寸: {info['width']}x{info['height']}")
                print(f"  类型: {info['type']}")

            print("=" * 60)

        except Exception as e:
            print(f"错误: {e}")
            sys.exit(1)

    else:
        print("用法: python image_utils.py <PDF文件路径>")
        sys.exit(1)
