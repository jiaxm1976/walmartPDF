#!/usr/bin/env python3
# ============================================================
# 文件: scripts/test_pdf_to_database.py
# 功能: 独立测试脚本 - PDF完整解析流程并保存到数据库
# 创建时间: 2025-12-19
# 说明: 不依赖API服务，直接调用Python函数测试
# ============================================================

import sys
import os
from pathlib import Path

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "backend"))

import logging
from datetime import datetime
import json

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """主测试流程."""

    print("=" * 70)
    print("  PDF解析完整流程测试")
    print("=" * 70)
    print()

    # 1. 导入必要模块
    print("📦 步骤1: 导入模块...")
    try:
        from app.services.pdf_parser_service import PDFParserService
        from database.config import SessionLocal, engine
        from database.models import Base, PDFFile, StatementHeader, SalesDetail, RefundDetail
        from app.crud.pdf_file import (
            create_pdf_file,
            create_statement_header,
            create_sales_detail,
            create_refund_detail,
            get_pdf_file,
            get_complete_statement_data
        )
        print("  ✓ 模块导入成功")
    except Exception as e:
        print(f"  ✗ 模块导入失败: {e}")
        return False

    # 2. 检查数据库
    print("\n📊 步骤2: 检查数据库...")
    try:
        # 确保表存在
        Base.metadata.create_all(bind=engine)
        print("  ✓ 数据库表检查完成")
    except Exception as e:
        print(f"  ✗ 数据库检查失败: {e}")
        return False

    # 3. 准备测试PDF
    print("\n📄 步骤3: 准备测试PDF...")
    test_pdf_path = PROJECT_ROOT / "PdfData" / "MP_01142025_statement_summary.pdf"

    if not test_pdf_path.exists():
        print(f"  ✗ 测试PDF不存在: {test_pdf_path}")
        return False

    print(f"  ✓ 测试PDF: {test_pdf_path.name}")
    print(f"    文件大小: {test_pdf_path.stat().st_size / 1024:.2f} KB")

    # 4. 执行PDF解析
    print("\n🔍 步骤4: 执行PDF解析...")
    try:
        parser = PDFParserService()
        result = parser.parse_pdf(str(test_pdf_path))

        if not result or not result.get('success'):
            print(f"  ✗ 解析失败: {result.get('error', '未知错误')}")
            return False

        print("  ✓ PDF解析成功")
        print(f"    处理时间: {result.get('process_time', 0):.2f}秒")

        # 显示解析结果摘要
        data = result.get('data', {})
        sections = data.get('sections', {})
        print(f"\n  📊 解析结果摘要:")
        print(f"    - Header板块: {'✓' if sections.get('header') else '✗'}")
        print(f"    - Sales板块: {'✓' if sections.get('sales') else '✗'}")
        print(f"    - Refund板块: {'✓' if sections.get('refund') else '✗'}")
        print(f"    - Footer板块: {'✓' if sections.get('footer') else '✗'}")

        # 保存JSON到文件（用于对比）
        output_json_path = PROJECT_ROOT / "test_output_direct.json"
        with open(output_json_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2, default=str)
        print(f"\n  💾 JSON结果已保存: {output_json_path}")

    except Exception as e:
        print(f"  ✗ 解析过程出错: {e}")
        import traceback
        traceback.print_exc()
        return False

    # 5. 保存到数据库
    print("\n💾 步骤5: 保存到数据库...")
    db = SessionLocal()
    try:
        # 创建PDF文件记录
        pdf_data = {
            "filename": test_pdf_path.name,
            "file_path": str(test_pdf_path),
            "file_size": test_pdf_path.stat().st_size,
            "file_hash": "test_hash_" + datetime.now().strftime("%Y%m%d%H%M%S"),
            "status": "completed"
        }

        db_pdf = create_pdf_file(db, pdf_data)
        pdf_id = db_pdf.id
        print(f"  ✓ PDF记录创建成功 (ID: {pdf_id})")

        # 保存Header板块
        header_data = sections.get('header', {})
        if header_data:
            header_record = {
                "pdf_id": pdf_id,
                "statement_period_start": header_data.get('statement_period_start'),
                "statement_period_end": header_data.get('statement_period_end'),
            }
            create_statement_header(db, header_record)
            print("  ✓ Header板块保存成功")

        # 保存Sales板块
        sales_data = sections.get('sales', {})
        if sales_data:
            sales_record = {
                "pdf_id": pdf_id,
                "total_sales": sales_data.get('total_sales'),
                "units_sold": sales_data.get('units_sold'),
            }
            create_sales_detail(db, sales_record)
            print("  ✓ Sales板块保存成功")

        # 保存Refund板块
        refund_data = sections.get('refund', {})
        if refund_data:
            refund_record = {
                "pdf_id": pdf_id,
                "total_refund": refund_data.get('total_refund'),
            }
            create_refund_detail(db, refund_record)
            print("  ✓ Refund板块保存成功")

        print(f"\n  ✅ 所有数据保存完成 (PDF ID: {pdf_id})")

        # 6. 验证数据库数据
        print("\n🔍 步骤6: 验证数据库数据...")

        # 查询PDF记录
        pdf_record = get_pdf_file(db, pdf_id)
        if pdf_record:
            print(f"  ✓ PDF记录查询成功:")
            print(f"    - 文件名: {pdf_record.filename}")
            print(f"    - 状态: {pdf_record.status}")
            print(f"    - 上传时间: {pdf_record.upload_time}")
        else:
            print("  ✗ PDF记录查询失败")

        # 查询完整数据
        complete_data = get_complete_statement_data(db, pdf_id)
        if complete_data:
            print(f"\n  ✓ 完整数据查询成功:")
            print(f"    - Header: {bool(complete_data.get('header'))}")
            print(f"    - Sales: {bool(complete_data.get('sales'))}")
            print(f"    - Refund: {bool(complete_data.get('refund'))}")

            # 保存数据库查询结果到JSON
            db_json_path = PROJECT_ROOT / "test_output_from_db.json"
            with open(db_json_path, 'w', encoding='utf-8') as f:
                json.dump(complete_data, f, ensure_ascii=False, indent=2, default=str)
            print(f"\n  💾 数据库数据已保存: {db_json_path}")
        else:
            print("  ✗ 完整数据查询失败")

    except Exception as e:
        print(f"  ✗ 数据库操作失败: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        return False
    finally:
        db.close()

    # 7. 测试总结
    print("\n" + "=" * 70)
    print("  ✅ 测试完成！")
    print("=" * 70)
    print(f"\n📁 输出文件:")
    print(f"  1. test_output_direct.json     - 解析原始结果")
    print(f"  2. test_output_from_db.json    - 数据库查询结果")
    print(f"\n💡 下一步:")
    print(f"  1. 对比两个JSON文件，验证数据一致性")
    print(f"  2. 使用数据库工具查看详细数据")
    print(f"  3. 检查日志了解详细处理过程")
    print()

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
