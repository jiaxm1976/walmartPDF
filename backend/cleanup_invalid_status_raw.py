#!/usr/bin/env python3
# 使用原始SQL清理数据库中状态为'uploaded'的无效记录

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

def cleanup_invalid_status():
    """使用原始SQL清理状态为'uploaded'的无效记录"""
    try:
        with engine.connect() as connection:
            logger.info("数据库连接成功")
            
            # 使用原始SQL查询状态为'uploaded'的记录
            logger.info("查询状态为'uploaded'的记录...")
            result = connection.execute(text("SELECT id, filename, process_status FROM pdf_files WHERE process_status = 'uploaded'"))
            invalid_records = result.fetchall()
            logger.info(f"找到 {len(invalid_records)} 条状态为'uploaded'的无效记录")
            
            # 删除这些记录
            if invalid_records:
                logger.info("删除无效记录...")
                delete_result = connection.execute(text("DELETE FROM pdf_files WHERE process_status = 'uploaded'"))
                connection.commit()
                logger.info(f"成功删除 {delete_result.rowcount} 条记录")
            
            # 查看当前数据库中的所有记录
            logger.info("查看当前数据库中的所有记录...")
            all_result = connection.execute(text("SELECT id, filename, process_status FROM pdf_files ORDER BY id"))
            all_records = all_result.fetchall()
            logger.info(f"当前数据库中共有 {len(all_records)} 条记录")
            for record in all_records:
                logger.info(f"  - id={record.id}, filename={record.filename}, status={record.process_status}")
            
    except Exception as e:
        logger.error(f"清理失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    cleanup_invalid_status()
