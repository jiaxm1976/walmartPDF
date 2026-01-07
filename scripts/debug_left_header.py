#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from backend.app.services.ocr_engine import OCREngine
from backend.app.services.left_section_ocr import LeftSectionOCR
from backend.app.utils.image_utils import pdf_to_images
import numpy as np

pdf_path = '20260101账单/MP_09232025_statement_summary_PW1.pdf'
images = pdf_to_images(pdf_path, dpi=800, grayscale=True)
if not images:
    print('无法读取 PDF 图像')
    raise SystemExit(1)
img = np.array(images[0])

h,w = img.shape[:2]
left = img[:, :int(w*0.63)]

engine = OCREngine(engine_type='vision')
ls = LeftSectionOCR(engine)
header = ls.process_header_section(left)
print('--- LeftSectionOCR.process_header_section 输出 ---')
print(header)
