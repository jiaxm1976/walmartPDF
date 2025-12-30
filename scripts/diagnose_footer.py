#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ============================================================
# 文件: scripts/diagnose_footer.py
# 功能: 诊断footer板块"期末余额"识别问题
# ============================================================

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import cv2
import numpy as np
from pdf2image import convert_from_path
import logging

from backend.app.services.ocr_engine import OCREngine
from backend.app.services.direct_keyword_extractor import DirectKeywordExtractor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def pdf_to_image(pdf_path: str, dpi: int = 300) -> np.ndarray:
    """将PDF第一页转为图片."""
    images = convert_from_path(pdf_path, dpi=dpi, first_page=1, last_page=1)
    image = np.array(images[0])
    image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
    return image


def split_horizontal(image: np.ndarray, split_ratio: float = 0.63) -> tuple:
    """横向分割图片."""
    height, width = image.shape[:2]
    split_x = int(width * split_ratio)
    left_image = image[0:height, 0:split_x]
    right_image = image[0:height, split_x:width]
    return left_image, right_image


def diagnose_pdf(pdf_path: str):
    """诊断单个PDF的footer板块."""
    pdf_name = Path(pdf_path).stem
    print(f"\n{'='*80}")
    print(f"诊断PDF: {pdf_name}")
    print(f"{'='*80}")

    # Step 1: 转换和分割
    image = pdf_to_image(pdf_path, dpi=300)
    left_image, _ = split_horizontal(image, split_ratio=0.63)
    image_height = left_image.shape[0]
    print(f"左侧图片高度: {image_height}px")

    # Step 2: OCR识别
    ocr_engine = OCREngine()
    extractor = DirectKeywordExtractor(ocr_engine)

    text_blocks = extractor.recognize_full_image(left_image)
    keyword_positions = extractor.find_keyword_positions(text_blocks)
    section_ranges = extractor.calculate_section_ranges(keyword_positions, image_height)

    # Step 3: 分析footer板块
    if 'footer' not in keyword_positions:
        print("❌ 未找到footer关键词（向您支付的金额）")
        return

    footer_keyword_y = keyword_positions['footer']
    print(f"\nFooter关键词Y坐标: {footer_keyword_y}")

    if 'footer' in section_ranges:
        footer_start, footer_end = section_ranges['footer']
        print(f"Footer板块范围: [{footer_start}, {footer_end}) = {footer_end - footer_start}px")
    else:
        print("❌ 未计算footer板块范围")
        return

    # Step 4: 查找所有包含"期末余额"的文本块
    print(f"\n查找所有包含'期末余额'或'余额'的文本块:")
    found_ending_balance = False

    for block in text_blocks:
        text = block['text']
        if '期末余额' in text or '余额' in text:
            y_top = block['y_top']
            y_bottom = block['y_bottom']
            y_center = block['y_center']

            # 判断是否在footer范围内
            in_range = footer_start <= y_bottom < footer_end
            status = "✅ 在范围内" if in_range else "❌ 超出范围"

            print(f"  {status} 文本: '{text}'")
            print(f"    Y坐标: top={y_top}, center={y_center}, bottom={y_bottom}")
            print(f"    footer范围: [{footer_start}, {footer_end})")
            print(f"    偏移: {y_bottom - footer_end}px (超出footer结束边界)")

            if '期末余额' in text:
                found_ending_balance = True

    if not found_ending_balance:
        print(f"\n❌ OCR未识别到'期末余额'文本")
        print(f"   可能原因：")
        print(f"   1. '期末余额'在第2页")
        print(f"   2. OCR识别失败")
        print(f"   3. 文字模糊或被遮挡")
    else:
        print(f"\n✅ OCR识别到'期末余额'，但可能超出footer板块范围")

    # Step 5: 显示footer板块内的所有文本块
    print(f"\nFooter板块内的所有文本块 (Y_bottom在[{footer_start}, {footer_end})范围内):")
    footer_blocks = [b for b in text_blocks if footer_start <= b['y_bottom'] < footer_end]

    for i, block in enumerate(footer_blocks[:20], 1):  # 最多显示20个
        text = block['text']
        y_bottom = block['y_bottom']
        print(f"  {i}. Y={y_bottom}: '{text}'")

    if len(footer_blocks) > 20:
        print(f"  ... 共{len(footer_blocks)}个文本块")

    # Step 6: 建议
    print(f"\n建议:")
    if not found_ending_balance:
        print(f"  • '期末余额'可能在第2页，需要处理多页PDF")
    else:
        max_y = max(b['y_bottom'] for b in text_blocks if '期末余额' in b['text'])
        extension_needed = max_y - footer_keyword_y
        print(f"  • 当前footer扩展: 1000px")
        print(f"  • 实际需要扩展: {extension_needed}px")
        if extension_needed > 1000:
            print(f"  • 建议增加扩展到: {int(extension_needed * 1.2)}px")


def main():
    """主函数."""
    pdf_dir = Path(__file__).parent.parent / "PdfData"
    pdf_files = sorted(pdf_dir.glob("*.pdf"))

    if not pdf_files:
        print("未找到PDF文件")
        return

    # 诊断所有PDF
    for pdf_file in pdf_files:
        try:
            diagnose_pdf(str(pdf_file))
        except Exception as e:
            print(f"❌ 诊断失败: {e}")
            import traceback
            traceback.print_exc()

    print(f"\n{'='*80}")
    print("诊断完成")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    main()
