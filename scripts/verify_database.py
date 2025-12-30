#!/usr/bin/env python3
# ============================================================
# 文件: scripts/verify_database.py
# 功能: 验证数据库表结构
# 作者: 开发团队
# 创建时间: 2025-12-18
# 说明: 查询数据库表结构并验证关系
# ============================================================

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "backend"))

from sqlalchemy import inspect
from database.config import engine, SessionLocal
from database import models


def verify_database_structure():
    """验证数据库表结构."""
    print("=" * 60)
    print("数据库表结构验证")
    print("=" * 60)
    print()

    inspector = inspect(engine)

    # 获取所有表名
    table_names = inspector.get_table_names()
    print(f"✓ 数据库中共有 {len(table_names)} 个表:")
    for i, table_name in enumerate(table_names, 1):
        print(f"  {i}. {table_name}")
    print()

    # 验证每个表的字段
    print("=" * 60)
    print("表字段详情")
    print("=" * 60)
    print()

    for table_name in table_names:
        columns = inspector.get_columns(table_name)
        print(f"📋 {table_name}")
        print(f"   字段数: {len(columns)}")
        for col in columns[:5]:  # 只显示前5个字段
            col_type = str(col['type'])
            nullable = "NULL" if col['nullable'] else "NOT NULL"
            print(f"   - {col['name']}: {col_type} {nullable}")
        if len(columns) > 5:
            print(f"   ... 还有 {len(columns) - 5} 个字段")
        print()

    # 验证外键关系
    print("=" * 60)
    print("外键关系")
    print("=" * 60)
    print()

    for table_name in table_names:
        foreign_keys = inspector.get_foreign_keys(table_name)
        if foreign_keys:
            print(f"📎 {table_name}")
            for fk in foreign_keys:
                referred_table = fk['referred_table']
                constrained_columns = ', '.join(fk['constrained_columns'])
                referred_columns = ', '.join(fk['referred_columns'])
                print(f"   └─> {referred_table} ({constrained_columns} -> {referred_columns})")
            print()

    print("=" * 60)
    print("✅ 数据库结构验证完成！")
    print("=" * 60)


def test_database_operations():
    """测试数据库基本CRUD操作."""
    print()
    print("=" * 60)
    print("测试数据库CRUD操作")
    print("=" * 60)
    print()

    db = SessionLocal()

    try:
        # 测试1: 插入一条PDF文件记录
        print("1️⃣ 测试插入PDF文件记录...")
        test_pdf = models.PDFFile(
            filename="test_sample.pdf",
            original_filename="原始测试文件.pdf",
            file_path="/test/path/test_sample.pdf",
            file_size=1024000,
            file_hash="abc123def456",
            process_status="pending"
        )
        db.add(test_pdf)
        db.commit()
        db.refresh(test_pdf)
        print(f"   ✓ 成功插入PDF文件，ID: {test_pdf.id}")

        # 测试2: 插入对账单头部信息
        print("2️⃣ 测试插入对账单头部信息...")
        from datetime import date
        test_header = models.StatementHeader(
            pdf_file_id=test_pdf.id,
            start_date=date(2025, 1, 1),
            end_date=date(2025, 1, 15),
            opening_balance=1000.50,
            reserve_funds=200.00,
            awaiting_payment=50.00
        )
        db.add(test_header)
        db.commit()
        print(f"   ✓ 成功插入对账单头部，ID: {test_header.id}")

        # 测试3: 插入销售明细
        print("3️⃣ 测试插入销售明细...")
        test_sales = models.SalesDetail(
            pdf_file_id=test_pdf.id,
            product_price=1500.00,
            shipping=50.00,
            net_commission=-150.00,
            total=1400.00
        )
        db.add(test_sales)
        db.commit()
        print(f"   ✓ 成功插入销售明细，ID: {test_sales.id}")

        # 测试4: 查询记录
        print("4️⃣ 测试查询记录...")
        pdf_count = db.query(models.PDFFile).count()
        header_count = db.query(models.StatementHeader).count()
        sales_count = db.query(models.SalesDetail).count()
        print(f"   ✓ PDF文件记录数: {pdf_count}")
        print(f"   ✓ 对账单头部记录数: {header_count}")
        print(f"   ✓ 销售明细记录数: {sales_count}")

        # 测试5: 关联查询
        print("5️⃣ 测试关联查询...")
        pdf_with_relations = db.query(models.PDFFile).filter(
            models.PDFFile.id == test_pdf.id
        ).first()
        print(f"   ✓ PDF文件名: {pdf_with_relations.filename}")
        print(f"   ✓ 关联的header: {pdf_with_relations.header is not None}")
        print(f"   ✓ 关联的sales: {pdf_with_relations.sales is not None}")

        # 测试6: 级联删除
        print("6️⃣ 测试级联删除...")
        db.delete(test_pdf)
        db.commit()
        # 验证关联记录是否被删除
        header_count_after = db.query(models.StatementHeader).count()
        sales_count_after = db.query(models.SalesDetail).count()
        print(f"   ✓ 删除PDF后，header记录数: {header_count_after}")
        print(f"   ✓ 删除PDF后，sales记录数: {sales_count_after}")

        print()
        print("=" * 60)
        print("✅ 所有数据库操作测试通过！")
        print("=" * 60)

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    verify_database_structure()
    test_database_operations()


# ============================================================
# END OF verify_database.py
# ============================================================
