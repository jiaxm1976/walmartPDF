#!/usr/bin/env python3
# 清理数据库中状态为'uploaded'的无效记录

import logging
import sys

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 添加项目根目录到Python路径
sys.path.insert(0, '/Users/jiaxinming/JxmWork/walmart-a/backend')

try:
    from sqlalchemy.orm import Session
    from database.config import get_db
    from database.models import PDFFile
    logger.info("模块导入成功")
except ImportError as e:
    logger.error(f"模块导入失败: {e}")
    sys.exit(1)

def cleanup_invalid_status():
    """清理状态为'uploaded'的无效记录"""
    try:
        db = next(get_db())
        logger.info("数据库连接成功")
        
        # 查询所有状态为'uploaded'的记录
        invalid_records = db.query(PDFFile).filter(PDFFile.process_status == 'uploaded').all()
        logger.info(f"找到 {len(invalid_records)} 条状态为'uploaded'的无效记录")
        
        # 删除这些记录
        for record in invalid_records:
            logger.info(f"删除记录: id={record.id}, filename={record.filename}")
            db.delete(record)
        
        db.commit()
        logger.info("清理完成")
        
        # 查看当前数据库中的所有记录
        all_records = db.query(PDFFile).all()
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
