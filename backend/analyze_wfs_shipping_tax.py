#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分析脚本：检查wfs_shipping_tax_refund字段的解析情况
"""

import json
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent.parent))

from app.services.pdf_parser_service import PDFParserService
from app.services.left_section_ocr import LeftSectionOCR
from app.services.ocr_engine import OCREngine
from app.services.keyword_locator import KeywordLocator
from app.services.keyword_extractor import KeywordExtractor
from app.services.left_section_cutter import LeftSectionCutter
from app.utils.image_utils import pdf_to_images
import cv2
import numpy as np

def analyze_wfs_shipping_tax(pdf_path: str):
    """分析wfs_shipping_tax_refund字段的解析情况"""
    print(f"分析PDF文件: {pdf_path}")
    print("=" * 60)
    
    try:
        # 初始化PDF解析服务
        parser = PDFParserService()
        
        # 直接调用解析方法获取原始数据
        parse_result = parser.parse_pdf(pdf_path)
        
        if not parse_result["success"]:
            print(f"解析失败: {parse_result['error']}")
            return
        
        # 获取原始解析数据
        raw_data = parse_result["data"]
        left_section = raw_data.get("left_section", {})
        
        # 分析sales模块
        if "sales" in left_section:
            print("1. Sales模块原始解析数据:")
            print(json.dumps(left_section["sales"], ensure_ascii=False, indent=2))
            
            # 检查是否有wfs_shipping_tax_refund相关的键
            sales_keys = list(left_section["sales"].keys())
            print(f"\n2. Sales模块包含的键: {sales_keys}")
            
            # 查找可能的字段变体
            tax_refund_variants = []
            for key in sales_keys:
                if "税" in key or "tax" in key.lower():
                    tax_refund_variants.append(key)
            
            if tax_refund_variants:
                print(f"\n3. 可能的税相关字段变体: {tax_refund_variants}")
            else:
                print("\n3. 未找到税相关字段")
        else:
            print("1. Sales模块数据不存在")
            
        # 分析总计校验情况
        print("\n4. 总计字段校验:")
        db_data, validation_results = parser.convert_to_database_format(raw_data)
        for result in validation_results:
            if result["section"] == "sales":
                print(f"   - {result['message']}")
                break
                
    except Exception as e:
        print(f"分析过程出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("用法: python analyze_wfs_shipping_tax.py <pdf_file_path>")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    analyze_wfs_shipping_tax(pdf_path)
