#!/usr/bin/env python3
"""
查看数据库中的PDF记录
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.config import SessionLocal
from database.models import PDFFile

def main():
    print("=== 数据库中的PDF记录 ===")
    
    db = SessionLocal()
    try:
        pdf_files = db.query(PDFFile).all()
        
        if not pdf_files:
            print("没有PDF记录")
            return
        
        print(f"共找到 {len(pdf_files)} 条记录：")
        print("-" * 60)
        print(f"{'ID':<5} {'文件名':<50} {'状态':<10} {'验证问题':<5}")
        print("-" * 60)
        
        for pdf in pdf_files:
            has_validation_issues = "有" if pdf.validation_issues else "无"
            print(f"{pdf.id:<5} {pdf.filename:<50} {pdf.process_status:<10} {has_validation_issues:<5}")
            
    finally:
        db.close()

if __name__ == "__main__":
    main()
