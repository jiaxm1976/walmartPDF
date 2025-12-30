#!/usr/bin/env python3
# 检查关联表是否有数据持久化记录

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
    from database.models import (
        PDFFile, SalesDetail, RefundDetail, StatementHeader, PaymentDetail
    )
    logger.info("模块导入成功")
except ImportError as e:
    logger.error(f"模块导入失败: {e}")
    sys.exit(1)

def check_related_tables():
    """检查关联表的数据持久化情况"""
    try:
        db = next(get_db())
        logger.info("数据库连接成功")
        
        # 获取最新的PDF记录
        latest_pdf = db.query(PDFFile).order_by(PDFFile.id.desc()).first()
        if not latest_pdf:
            logger.error("数据库中没有PDF记录")
            return False
        
        logger.info(f"\n检查PDF文件: id={latest_pdf.id}, filename={latest_pdf.filename}")
        logger.info(f"状态: {latest_pdf.process_status}")
        logger.info(f"校验问题: {latest_pdf.validation_issues}")
        
        # 检查各关联表
        tables_to_check = [
            ("销售详情", SalesDetail),
            ("退款详情", RefundDetail),
            ("报表表头", StatementHeader),
            ("付款详情", PaymentDetail)
        ]
        
        for table_name, model in tables_to_check:
            count = db.query(model).filter_by(pdf_file_id=latest_pdf.id).count()
            logger.info(f"{table_name}表记录数: {count}")
            
            # 如果有记录，显示前几条数据
            if count > 0:
                records = db.query(model).filter_by(pdf_file_id=latest_pdf.id).limit(3).all()
                for i, record in enumerate(records, 1):
                    logger.info(f"  记录{i}: {record.__dict__}")
            
        return True
        
    except Exception as e:
        logger.error(f"检查失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = check_related_tables()
    if success:
        logger.info("\n✅ 关联表检查完成！")
        sys.exit(0)
    else:
        logger.error("\n❌ 关联表检查失败！")
        sys.exit(1)
