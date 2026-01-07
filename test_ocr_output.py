#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from backend.app.services.ocr_engine import OCREngine
from backend.app.utils.image_utils import pdf_to_images
import cv2
import numpy as np

pdf_path = "20260101账单/MP_09232025_statement_summary_PW1.pdf"

# 获取图片
images = pdf_to_images(pdf_path, dpi=800, grayscale=True)
if images:
    img = np.array(images[0])
    if len(img.shape) == 3:
        img = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    
    # 只看左侧部分（约 63%）
    h, w = img.shape
    split_x = int(w * 0.63)
    left_img = img[:, :split_x]
    
    # 对左侧顶部进行OCR（前200行）
    top_img = left_img[:200, :]
    
    # 使用 Vision 引擎（快速）
    try:
        engine = OCREngine(engine_type="vision")
        result = engine.recognize(top_img)
        
        print("OCR 原始输出（前10行）:")
        for i, text in enumerate(result[:10]):
            print(f"  行{i}: {text}")
    except Exception as e:
        print(f"Vision 引擎错误: {e}")
