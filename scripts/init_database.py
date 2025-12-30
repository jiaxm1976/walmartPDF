#!/usr/bin/env python3
# ============================================================
# 文件: scripts/init_database.py
# 功能: 初始化数据库（创建所有表）
# 作者: 开发团队
# 创建时间: 2025-12-18
# 说明: 使用SQLAlchemy创建数据库表结构
# ============================================================

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "backend"))

from database.config import init_database, get_database_url, DB_TYPE


def main():
    """初始化数据库主函数."""
    print("=" * 60)
    print("Walmart PDF解析系统 - 数据库初始化")
    print("=" * 60)
    print(f"数据库类型: {DB_TYPE}")
    print(f"数据库URL: {get_database_url()}")
    print()

    try:
        # 初始化数据库
        init_database()
        print()
        print("=" * 60)
        print("✅ 数据库初始化成功！")
        print("=" * 60)
        print()
        print("已创建的表:")
        print("  1. pdf_files          - PDF文件主表")
        print("  2. statement_headers  - 对账单头部信息")
        print("  3. sales_details      - 销售明细")
        print("  4. refund_details     - 退款明细")
        print("  5. adjustment_details - 调整明细")
        print("  6. wfs_details        - WFS服务明细")
        print("  7. other_activity_details - 其他活动明细")
        print("  8. statement_footers  - 对账单尾部信息")
        print("  9. payment_details    - 付款详情")
        print(" 10. dynamic_fields     - 动态字段扩展")
        print()

        if DB_TYPE == "sqlite":
            db_path = project_root / "walmart_pdf_parser.db"
            print(f"SQLite数据库文件位置: {db_path}")
            print(f"文件大小: {db_path.stat().st_size if db_path.exists() else 0} bytes")

    except Exception as e:
        print()
        print("=" * 60)
        print("❌ 数据库初始化失败！")
        print("=" * 60)
        print(f"错误信息: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()


# ============================================================
# END OF init_database.py
# ============================================================
