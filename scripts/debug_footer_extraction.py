#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 调试footer板块数据提取问题

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import cv2
import numpy as np
from pdf2image import convert_from_path
import logging
import re

from backend.app.services.ocr_engine import OCREngine
from backend.app.services.direct_keyword_extractor import DirectKeywordExtractor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def debug_footer_extraction(pdf_path: str):
    """调试单个PDF的footer数据提取."""
    pdf_name = Path(pdf_path).stem
    print(f"\n{'='*80}")
    print(f"调试PDF: {pdf_name}")
    print(f"{'='*80}\n")

    # 转换和分割
    images = convert_from_path(pdf_path, dpi=300, first_page=1, last_page=1)
    image = np.array(images[0])
    image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

    height, width = image.shape[:2]
    split_x = int(width * 0.63)
    left_image = image[0:height, 0:split_x]

    # OCR识别
    ocr_engine = OCREngine()
    extractor = DirectKeywordExtractor(ocr_engine)

    text_blocks = extractor.recognize_full_image(left_image)
    keyword_positions = extractor.find_keyword_positions(text_blocks)
    image_height = left_image.shape[0]
    section_ranges = extractor.calculate_section_ranges(keyword_positions, image_height)
    classified_blocks = extractor.classify_text_blocks_by_range(text_blocks, section_ranges)

    # 获取footer板块的文本块
    footer_blocks = classified_blocks.get('footer', [])
    print(f"Footer板块包含 {len(footer_blocks)} 个文本块\n")

    # 显示所有footer文本块
    print("Footer板块的所有文本块（按Y坐标排序）:")
    footer_blocks_sorted = sorted(footer_blocks, key=lambda x: x['y_bottom'])
    for i, block in enumerate(footer_blocks_sorted, 1):
        text = block['text']
        y_bottom = block['y_bottom']
        print(f"  {i}. Y={y_bottom}: '{text}'")

    # 模拟extract_key_value_pairs的处理过程
    print(f"\n模拟extract_key_value_pairs处理过程:")
    print(f"{'='*80}")

    # 合并Y坐标相近的文本块
    Y_THRESHOLD = 30
    merged_lines = []
    i = 0
    sorted_blocks = sorted(footer_blocks, key=lambda x: x['y_bottom'])

    while i < len(sorted_blocks):
        current_block = sorted_blocks[i]
        line_blocks = [current_block]

        j = i + 1
        while j < len(sorted_blocks):
            next_block = sorted_blocks[j]
            if abs(next_block['y_bottom'] - current_block['y_bottom']) <= Y_THRESHOLD:
                line_blocks.append(next_block)
                j += 1
            else:
                break

        line_blocks.sort(key=lambda x: x['x_left'])
        merged_text = ' '.join([b['text'] for b in line_blocks])
        merged_lines.append((merged_text, current_block['y_bottom']))

        i = j

    print(f"\n合并后的文本行（Y阈值={Y_THRESHOLD}px）:")
    for idx, (line, y_coord) in enumerate(merged_lines, 1):
        print(f"  {idx}. Y={y_coord}: '{line}'")

    # 提取金额
    def extract_amount(text):
        """提取金额."""
        # 格式1: $ 金额
        match = re.search(r'([-−]?)\s*[$＄]\s*(\d+[,\d]*\.?\d*)', text)
        if match:
            sign = match.group(1).replace('−', '-')
            number = match.group(2).replace(',', '')
            return sign + number

        # 格式2: 金额 美元
        match = re.search(r'([-−]?)\s*(\d+[,\d]*\.?\d*)\s*美元', text)
        if match:
            sign = match.group(1).replace('−', '-')
            number = match.group(2).replace(',', '')
            return sign + number

        return None

    print(f"\n提取键值对:")
    data = {}
    for line, y_coord in merged_lines:
        amount_value = extract_amount(line)
        if amount_value:
            # 移除金额部分
            key_part = line
            key_part = re.sub(r'[-−]?\s*[$＄]\s*\d+[,\d]*\.?\d*', '', key_part)
            key_part = re.sub(r'[-−]?\s*\d+[,\d]*\.?\d*\s*美元', '', key_part)
            key_part = key_part.replace(':', '').replace('：', '').strip()

            if key_part:
                data[key_part] = amount_value
                print(f"  ✓ '{key_part}' = {amount_value}")
            else:
                print(f"  ✗ 孤立金额（无标签）: {amount_value}")
        else:
            # 检查是否包含"期末余额"
            if '期末余额' in line:
                print(f"  ⚠️  发现'期末余额'但无金额: '{line}'")

    print(f"\n最终提取的键值对:")
    for k, v in data.items():
        print(f"  {k}: {v}")

    if '期末余额' not in data:
        print(f"\n❌ 未提取到'期末余额'")
        print(f"\n可能原因分析:")

        # 查找包含"期末余额"的行
        ending_balance_lines = [(line, y) for line, y in merged_lines if '期末余额' in line]
        if ending_balance_lines:
            print(f"  • 找到{len(ending_balance_lines)}行包含'期末余额':")
            for line, y in ending_balance_lines:
                print(f"    Y={y}: '{line}'")
                amt = extract_amount(line)
                if amt:
                    print(f"      → 金额: {amt}")
                else:
                    print(f"      → 未识别到金额")
        else:
            print(f"  • 未找到包含'期末余额'的行")
            print(f"  • 可能'期末余额'和金额在不同行，但Y坐标差距>{Y_THRESHOLD}px")


def main():
    """主函数."""
    # 调试3个有问题的文件
    pdf_dir = Path(__file__).parent.parent / "PdfData"
    problem_files = [
        'MP_01142025_statement_summary.pdf',
        'MP_02112025_statement_summary.pdf',
        'MP_08262025_statement_summary.pdf'
    ]

    for pdf_file in problem_files:
        pdf_path = pdf_dir / pdf_file
        if pdf_path.exists():
            try:
                debug_footer_extraction(str(pdf_path))
            except Exception as e:
                print(f"❌ 调试失败: {e}")
                import traceback
                traceback.print_exc()
        else:
            print(f"❌ 文件不存在: {pdf_path}")


if __name__ == "__main__":
    main()
