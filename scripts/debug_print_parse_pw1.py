#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
from backend.app.services.ocr_engine import OCREngine
from backend.app.utils.image_utils import pdf_to_images
from backend.app.utils.text_formatter import merge_text_blocks, jg_structured_data

pdf_path = '20260101账单/MP_09232025_statement_summary_PW1.pdf'
images = pdf_to_images(pdf_path, dpi=800, grayscale=True)
if not images:
    print('无法读取 PDF 图像')
    raise SystemExit(1)
img = images[0]
import numpy as np
img = np.array(img)

h, w = img.shape[:2]
left = img[:, :int(w*0.63)]

engine = OCREngine(engine_type='vision')
ocr_results = engine.recognize_image(left)

merged_text, text_infos = merge_text_blocks(ocr_results, y_tolerance=15)
print('--- 合并行输出 (merge_text_blocks) ---')
lines = merged_text.split('\n') if merged_text else []
for i, ln in enumerate(lines,1):
    print(f'{i:03d}: {ln}')

print('\n--- jg_structured_data JSON ---')
structured = jg_structured_data(lines)
print(json.dumps(structured, ensure_ascii=False, indent=2))

print('\n--- 检查 footer/向您支付的金额 值 ---')
try:
    classdata = structured.get('classdata', {})
    for cat in classdata.get('category_details', []):
        name = cat.get('类别名称')
        for detail in cat.get('明细列表', []):
            if '向您支付' in str(detail.get('字段名')) or '支付' in str(detail.get('字段名')):
                print(f"类别: {name} -> {detail}")
except Exception:
    pass
