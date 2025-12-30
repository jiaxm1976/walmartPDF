#!/usr/bin/env python3
# 查看数据库当前状态

import logging
import sys

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 添加项目根目录到Python路径
sys.path.insert(0, '/Users/jiaxinming/JxmWork/walmart-a/backend')

try:
    from database.config import engine
    from sqlalchemy import text
    logger.info("数据库引擎导入成功")
except ImportError as e:
    logger.error(f"数据库引擎导入失败: {e}")
    sys.exit(1)

def check_db_status():
    """查看数据库当前状态"""
    try:
        with engine.connect() as connection:
            logger.info("数据库连接成功")
            
            # 查看所有表
            logger.info("查看数据库中的所有表...")
            tables_result = connection.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
            tables = tables_result.fetchall()
            logger.info(f"共有 {len(tables)} 张表")
            for table in tables:
                logger.info(f"  - {table.name}")
            
            # 查看pdf_files表的记录
            logger.info("\n查看pdf_files表的记录...")
            pdfs_result = connection.execute(text("SELECT * FROM pdf_files"))
            pdfs = pdfs_result.fetchall()
            logger.info(f"pdf_files表共有 {len(pdfs)} 条记录")
            for pdf in pdfs:
                logger.info(f"  - id={pdf.id}, filename={pdf.filename}, status={pdf.process_status}")
            
            # 查看sales_details表的记录
            logger.info("\n查看sales_details表的记录...")
            sales_result = connection.execute(text("SELECT * FROM sales_details"))
            sales = sales_result.fetchall()
            logger.info(f"sales_details表共有 {len(sales)} 条记录")
            for record in sales[:3]:  # 只显示前3条
                logger.info(f"  - id={record.id}, pdf_file_id={record.pdf_file_id}")
            
            return True
            
    except Exception as e:
        logger.error(f"检查失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    check_db_status()
