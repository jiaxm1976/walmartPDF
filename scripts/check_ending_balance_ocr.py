#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 检查"期末余额"区域的OCR识别情况

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import cv2
import numpy as np
from pdf2image import convert_from_path
from backend.app.services.ocr_engine import OCREngine

# 测试文件
test_files = [
    'PdfData/MP_01142025_statement_summary.pdf',
    'PdfData/MP_02112025_statement_summary.pdf',
    'PdfData/MP_08262025_statement_summary.pdf'
]

for pdf_path in test_files:
    print(f"\n{'='*80}")
    print(f"检查PDF: {Path(pdf_path).stem}")
    print(f"{'='*80}\n")

    # 转换PDF
    images = convert_from_path(pdf_path, dpi=300, first_page=1, last_page=1)
    image = np.array(images[0])
    image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

    height, width = image.shape[:2]
    split_x = int(width * 0.63)
    left_image = image[0:height, 0:split_x]

    print(f"图片尺寸: {left_image.shape}")

    # 使用极低置信度阈值的OCR（0.1）
    print(f"\n测试1: 置信度阈值 = 0.1")
    ocr_engine = OCREngine(confidence_threshold=0.1)
    ocr_results = ocr_engine.recognize_image(left_image)

    # 查找"期末余额"附近的所有文本块（Y坐标在3000-3500范围）
    print(f"\nY坐标在3000-3500范围内的所有文本块:")
    for box, (text, confidence) in ocr_results:
        y_top = int(box[0][1])
        y_bottom = int(box[2][1])

        if 3000 <= y_top <= 3500 or 3000 <= y_bottom <= 3500:
            print(f"  Y=[{y_top:4d}, {y_bottom:4d}] conf={confidence:.3f}: '{text}'")

    # 测试2: 完全无阈值（confidence_threshold=0.0）
    print(f"\n测试2: 置信度阈值 = 0.0 (无过滤)")
    ocr_engine2 = OCREngine(confidence_threshold=0.0)
    ocr_results2 = ocr_engine2.recognize_image(left_image)

    print(f"\nY坐标在3000-3500范围内的所有文本块（无置信度过滤）:")
    for box, (text, confidence) in ocr_results2:
        y_top = int(box[0][1])
        y_bottom = int(box[2][1])

        if 3000 <= y_top <= 3500 or 3000 <= y_bottom <= 3500:
            print(f"  Y=[{y_top:4d}, {y_bottom:4d}] conf={confidence:.3f}: '{text}'")
