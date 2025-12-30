#!/usr/bin/env python3
"""
检查特定PDF文件的相关表记录
"""
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from database.models import PDFFile

# 创建数据库连接
engine = create_engine('sqlite:////Users/jiaxinming/JxmWork/walmart-a/backend/data/walmart_pdf_parser.db')
Session = sessionmaker(bind=engine)
db = Session()

# 获取最新的PDF文件记录
pdf_file = db.query(PDFFile).order_by(PDFFile.id.desc()).first()
pdf_id = pdf_file.id if pdf_file else None

if not pdf_file:
    print(f"未找到PDF文件: id={pdf_id}")
    sys.exit(1)

print(f"PDF文件信息: {pdf_file.filename} (ID: {pdf_id})")
print(f"处理状态: {pdf_file.process_status}")
print(f"创建时间: {pdf_file.created_at}")
print("=" * 60)

# 检查相关表的记录
related_tables = [
    "adjustment_details",
    "sales_details",
    "refund_details",
    "wfs_details",
    "other_activity_details",
    "statement_headers",
    "statement_footers",
    "payment_details"
]

for table in related_tables:
    # 执行原始SQL查询
    query = text(f"SELECT COUNT(*) FROM {table} WHERE pdf_file_id = :pdf_id")
    result = db.execute(query, {"pdf_id": pdf_id})
    count = result.scalar_one()
    
    print(f"{table} 表中与PDF ID={pdf_id}相关的记录数: {count}")
    
    # 如果有记录，显示前几条
    if count > 0:
        query = text(f"SELECT * FROM {table} WHERE pdf_file_id = :pdf_id LIMIT 2")
        records = db.execute(query, {"pdf_id": pdf_id}).fetchall()
        for i, record in enumerate(records):
            print(f"  第{i+1}条记录: {record}")
        if count > 2:
            print(f"  ... 还有 {count - 2} 条记录")
    print()

db.close()
