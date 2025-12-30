#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分析销售模块的OCR识别过程，查看原始文本行
"""

import sys
import os
import json
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent.parent))

from app.services.pdf_parser_service import PDFParserService
from app.services.left_section_ocr import LeftSectionOCR
from app.config import settings


def analyze_sales_section(pdf_path: str):
    """分析销售模块的OCR识别过程"""
    print(f"分析PDF文件: {pdf_path}")
    print("=" * 60)
    
    try:
        # 初始化PDF解析服务
        parser = PDFParserService(dpi=settings.PDF_DPI)
        
        # 解析PDF文件
        print("1. 正在解析PDF文件...")
        parse_result = parser.parse_pdf(pdf_path)
        
        if not parse_result["success"]:
            print(f"解析失败: {parse_result['error']}")
            return
        
        parsed_data = parse_result["data"]
        print(f"解析成功，耗时: {parse_result['process_time']:.2f}秒")
        print()
        
        # 获取销售模块的原始数据
        left_section = parsed_data.get("left_section", {})
        sales_data = left_section.get("sales", {})
        
        print("2. 销售模块原始解析数据:")
        for key, value in sales_data.items():
            print(f"  {key}: {value}")
        print()
        
        # 重新提取销售模块的文本行
        print("3. 重新提取销售模块的文本行...")
        
        # 为了获取销售模块的图片，我们需要重新解析并保存中间结果
        output_dir = Path("/tmp/sales_analysis")
        output_dir.mkdir(exist_ok=True)
        
        # 解析PDF并保存中间结果
        parse_result_with_temp = parser.parse_pdf(pdf_path, output_dir=str(output_dir))
        
        if parse_result_with_temp["success"]:
            print(f"  中间结果已保存到: {output_dir}")
            
            # 查看保存的文件
            print("  保存的文件:")
            for file in output_dir.glob("*.*"):
                print(f"    - {file.name}")
            
            # 查看解析数据的JSON文件
            parsed_data_file = output_dir / "parsed_data.json"
            if parsed_data_file.exists():
                with open(parsed_data_file, "r", encoding="utf-8") as f:
                    parsed_data_detail = json.load(f)
                
                print("\n4. 详细解析数据:")
                sales_detail = parsed_data_detail.get("left_section", {}).get("sales", {})
                print("  销售模块详细数据:")
                for key, value in sales_detail.items():
                    print(f"    {key}: {value}")
        
        print("\n=" * 60)
        print("分析完成")
        
    except Exception as e:
        print(f"分析过程中出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"用法: {sys.argv[0]} <pdf_file_path>")
        print("示例: python analyze_sales_section.py /path/to/your/pdf/file.pdf")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    if not os.path.exists(pdf_path):
        print(f"文件不存在: {pdf_path}")
        sys.exit(1)
    
    analyze_sales_section(pdf_path)
