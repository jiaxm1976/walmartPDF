#!/usr/bin/env python3
# ============================================================
# 检查数据库中的PDF文件
# 作者: 开发团队
# 创建时间: 2025-12-24
# 功能: 检查数据库中存在的PDF文件信息
# ============================================================

import os
import sys
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 导入所需模块
try:
    from database.config import get_db
    from database import models
    logger.info("模块导入成功")
    logger.info(f"可用模型: {dir(models)}")
except ImportError as e:
    logger.error(f"模块导入失败: {e}")
    sys.exit(1)


def check_pdf_files():
    """检查数据库中的PDF文件"""
    logger.info("="*60)
    logger.info("开始检查数据库中的PDF文件")
    logger.info("="*60)
    
    # 创建数据库会话
    try:
        db = next(get_db())
        logger.info("数据库会话创建成功")
    except Exception as e:
        logger.error(f"创建数据库会话失败: {e}")
        return False
    
    # 查询所有PDF文件
    try:
        # 使用getattr动态获取模型
        PDFFile = getattr(models, 'PDFFile', None)
        if not PDFFile:
            logger.error("未找到PDFFile模型")
            return False
        
        pdf_files = db.query(PDFFile).all()
        if not pdf_files:
            logger.info("数据库中没有PDF文件")
            return False
        
        logger.info(f"数据库中共有 {len(pdf_files)} 个PDF文件")
        for pdf in pdf_files:
            logger.info(f"ID: {pdf.id}, 文件名: {pdf.filename}, 状态: {pdf.process_status}, 创建时间: {pdf.created_at}")
        
        return True
        
    except Exception as e:
        logger.error(f"查询PDF文件失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    check_pdf_files()
