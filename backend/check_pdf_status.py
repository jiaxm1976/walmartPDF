#!/usr/bin/env python3
"""
检查pdf_files表中指定文件的处理状态和验证问题
"""
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.session import SessionLocal
from app.models.pdf_file import PDFFile

def check_pdf_file_status(filename):
    """检查指定文件名的PDF文件状态"""
    db = SessionLocal()
    try:
        # 查询包含指定文件名的所有记录（可能有时间戳前缀）
        pdf_files = db.query(PDFFile).filter(PDFFile.filename.contains(filename)).all()
        
        if not pdf_files:
            print(f"未找到包含 '{filename}' 的PDF文件记录")
            return
            
        print(f"找到 {len(pdf_files)} 条包含 '{filename}' 的记录:")
        print("=" * 60)
        
        for pdf_file in pdf_files:
            print(f"ID: {pdf_file.id}")
            print(f"Filename: {pdf_file.filename}")
            print(f"Upload Date: {pdf_file.upload_date}")
            print(f"Process Status: {pdf_file.process_status}")
            print(f"Validation Issues: {pdf_file.validation_issues}")
            print(f"File Hash: {pdf_file.file_hash}")
            print(f"File Path: {pdf_file.file_path}")
            print(f"Total Amount: {pdf_file.total_amount}")
            print("=" * 60)
            
    finally:
        db.close()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("用法: python check_pdf_status.py <文件名>")
        sys.exit(1)
    
    filename = sys.argv[1]
    check_pdf_file_status(filename)
