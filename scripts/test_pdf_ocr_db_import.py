# -*- coding: utf-8 -*-
"""
测试脚本：PDF OCR 数据导入格式化结果导出
功能：
- 从 parse_pdf_file() 进入，调用 process_left_image()
- 在格式化文本块后，将结果导出到 txt 文件
"""
import os
import cv2
from backend.app.services.left_image_processor_service import LeftImageProcessorService
from backend.app.services.pdf_parser import parse_pdf_file

# 输入 PDF 文件路径（请根据实际情况调整）
PDF_PATH = "PdfData/MP_01142025_statement_summary.pdf"
# 输出 txt 文件路径
OUTPUT_TXT = "output/formatted_text_blocks.txt"

if __name__ == "__main__":
    print(f"开始测试 PDF OCR 数据导入流程...")
    print(f"输入文件: {PDF_PATH}")
    
    # 1. 解析 PDF，获取解析结果
    try:
        pdf_result = parse_pdf_file(PDF_PATH)
        print(f"PDF 解析成功")
        
        # 从解析结果中获取左侧图片（需要根据实际结构调整）
        # 假设结果中有 left_section_data 或类似字段包含图片数据
        # 这里需要根据实际的 pdf_result 结构来调整
        
        # 如果 pdf_result 中没有直接的图片数据，我们需要另一种方式
        # 让我们直接使用 LeftImageProcessorService 来处理
        
        print("注意：此测试需要直接提供图片数据")
        print("请修改脚本以适配实际的数据流程")
        
    except Exception as e:
        print(f"PDF 解析失败: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
