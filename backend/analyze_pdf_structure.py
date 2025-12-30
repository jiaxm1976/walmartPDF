#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分析PDF解析结果的结构，确认各板块数据的实际位置（left_section/right_section）
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent.parent))

from app.services.pdf_parser_service import PDFParserService

def analyze_pdf_structure(pdf_path: str):
    """分析PDF解析结果的结构"""
    print(f"分析PDF文件: {pdf_path}")
    print("=" * 60)
    
    try:
        # 初始化PDF解析服务
        parser = PDFParserService()
        
        # 解析PDF文件
        parse_result = parser.parse_pdf(pdf_path)
        
        if not parse_result["success"]:
            print(f"解析失败: {parse_result['error']}")
            return
        
        parsed_data = parse_result["data"]
        
        # 打印解析结果的结构
        print("解析结果结构:")
        print(f"- left_section 包含的板块: {list(parsed_data.get('left_section', {}).keys())}")
        print(f"- right_section 包含的板块: {list(parsed_data.get('right_section', {}).keys())}")
        print()
        
        # 详细打印每个板块的内容
        print("各板块详细内容:")
        print("\n1. left_section:")
        left_data = parsed_data.get('left_section', {})
        for section_name, section_data in left_data.items():
            print(f"   - {section_name}:")
            for key, value in section_data.items():
                print(f"     {key}: {value}")
        
        print("\n2. right_section:")
        right_data = parsed_data.get('right_section', {})
        for section_name, section_data in right_data.items():
            print(f"   - {section_name}:")
            for key, value in section_data.items():
                print(f"     {key}: {value}")
        
        print("\n" + "=" * 60)
        print("分析完成")
        
    except Exception as e:
        print(f"分析过程中出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"用法: {sys.argv[0]} <pdf_file_path>")
        print("示例: python analyze_pdf_structure.py /path/to/your/pdf/file.pdf")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    if not os.path.exists(pdf_path):
        print(f"文件不存在: {pdf_path}")
        sys.exit(1)
    
    analyze_pdf_structure(pdf_path)
