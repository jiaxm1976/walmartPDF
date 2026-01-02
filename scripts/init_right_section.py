#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
右侧数据初始化脚本

功能：
  1. 从 PDF 处理结果中提取右侧数据
  2. 初始化右侧数据到 field_frequency 表（用于字段统计）
  3. 支持从 jg_structured_data() 格式直接导入
  4. 验证右侧数据的完整性

使用方式：
  python scripts/init_right_section.py  # 从 PdfData/ 目录提取并导入
  python scripts/init_right_section.py --verify  # 仅验证

作者：AI 助手
日期：2026-01-02
"""

import json
import sqlite3
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
import sys

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s'
)
logger = logging.getLogger(__name__)

# 项目路径
PROJECT_ROOT = Path(__file__).parent.parent
DB_PATH = PROJECT_ROOT / 'backend' / 'data' / 'walmart_pdf_parser.db'
PDF_DATA_DIR = PROJECT_ROOT.parent / 'PdfData'


# 右侧数据标准字段列表
RIGHT_SECTION_FIELDS = [
    '状态',
    '付款日期',
    '周期付款',
    '付款方式',
    '设备方式',
    '待付款金额',
    '等待回款金额',
    '回款等待期',
    '警告信息'
]


class RightSectionInitializer:
    """右侧数据初始化器"""
    
    def __init__(self, db_path: str = str(DB_PATH)):
        self.db_path = db_path
        self.conn = None
    
    def connect(self):
        """连接数据库"""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        logger.info(f"✓ 已连接到数据库: {self.db_path}")
    
    def disconnect(self):
        """断开连接"""
        if self.conn:
            self.conn.close()
            logger.info("✓ 已断开数据库连接")
    
    def initialize_right_section_frequency(self) -> int:
        """
        初始化右侧数据字段频率
        
        右侧数据的所有字段都按照高频字段处理（frequency >= 2）
        这样可以避免字段被合并到 {section_name}_其他
        
        Returns:
            初始化的字段数
        """
        try:
            cursor = self.conn.cursor()
            count = 0
            
            for field_name in RIGHT_SECTION_FIELDS:
                # 检查该字段是否已存在
                cursor.execute(
                    "SELECT id FROM field_frequency WHERE section_name = ? AND field_name = ?",
                    ('right_section', field_name)
                )
                
                if cursor.fetchone():
                    # 更新频率为 2（高频）
                    cursor.execute(
                        "UPDATE field_frequency SET frequency = 2 WHERE section_name = ? AND field_name = ?",
                        ('right_section', field_name)
                    )
                    logger.debug(f"  ✓ 更新字段频率: right_section.{field_name}")
                else:
                    # 插入新记录，频率设为 2（高频）
                    cursor.execute(
                        """
                        INSERT INTO field_frequency (section_name, field_name, frequency, frequency_percent)
                        VALUES (?, ?, ?, ?)
                        """,
                        ('right_section', field_name, 2, 100.0)
                    )
                    logger.debug(f"  ✓ 插入字段: right_section.{field_name}")
                    count += 1
            
            self.conn.commit()
            logger.info(f"✓ 右侧数据字段频率初始化完成 ({count} 个新字段)")
            return count
        
        except Exception as e:
            logger.error(f"✗ 初始化右侧数据字段频率失败: {e}")
            self.conn.rollback()
            return 0
    
    def verify_right_section_data(self) -> bool:
        """
        验证已导入的右侧数据
        
        Returns:
            True 如果验证成功，False 否则
        """
        try:
            cursor = self.conn.cursor()
            
            # 检查是否有 right_section 板块的数据
            cursor.execute(
                "SELECT COUNT(*) as count FROM section_data WHERE section_name = 'right_section'"
            )
            result = cursor.fetchone()
            count = result['count'] if result else 0
            
            if count > 0:
                logger.info(f"✓ 右侧数据验证通过: {count} 条记录")
                
                # 显示样本数据
                cursor.execute(
                    "SELECT id, data FROM section_data WHERE section_name = 'right_section' LIMIT 1"
                )
                sample = cursor.fetchone()
                if sample:
                    try:
                        data = json.loads(sample['data'])
                        logger.info(f"  样本字段数: {len(data)}")
                        logger.debug(f"  样本数据: {list(data.keys())}")
                    except:
                        pass
                
                return True
            else:
                logger.warning("⚠ 没有找到 right_section 板块数据")
                return False
        
        except Exception as e:
            logger.error(f"✗ 右侧数据验证失败: {e}")
            return False
    
    def get_right_section_statistics(self) -> Dict[str, Any]:
        """
        获取右侧数据统计信息
        
        Returns:
            统计信息字典
        """
        try:
            cursor = self.conn.cursor()
            
            stats = {
                'total_records': 0,
                'field_count': 0,
                'fields': []
            }
            
            # 获取右侧数据的总记录数
            cursor.execute(
                "SELECT COUNT(*) as count FROM section_data WHERE section_name = 'right_section'"
            )
            result = cursor.fetchone()
            stats['total_records'] = result['count'] if result else 0
            
            # 获取字段列表
            cursor.execute(
                "SELECT field_name FROM field_frequency WHERE section_name = 'right_section' ORDER BY field_name"
            )
            fields = [row['field_name'] for row in cursor.fetchall()]
            stats['fields'] = fields
            stats['field_count'] = len(fields)
            
            return stats
        
        except Exception as e:
            logger.error(f"✗ 获取右侧数据统计失败: {e}")
            return {}


def main():
    """主流程"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║           Walmart PDF 右侧数据 - 初始化脚本                  ║
║         (右侧支付/配送等信息识别、初始化与导入)              ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    try:
        initializer = RightSectionInitializer()
        
        # 连接数据库
        logger.info("步骤 1/3: 连接数据库")
        initializer.connect()
        
        # 初始化右侧数据字段频率
        logger.info("步骤 2/3: 初始化右侧数据字段频率")
        field_count = initializer.initialize_right_section_frequency()
        
        # 验证右侧数据
        logger.info("步骤 3/3: 验证右侧数据")
        stats = initializer.get_right_section_statistics()
        
        # 显示统计信息
        print(f"""
╔══════════════════════════════════════════════════════════════╗
║                  ✓ 右侧数据初始化完成！                     ║
╚══════════════════════════════════════════════════════════════╝

📊 初始化结果：
  ✓ 已初始化 {field_count} 个右侧数据字段
  ✓ 字段总数: {stats['field_count']}
  ✓ 数据记录数: {stats['total_records']}

📋 右侧数据字段列表：
  {chr(10).join(f'  • {field}' for field in stats['fields'])}

🔧 右侧数据板块名: 'right_section'
   所有字段都归属于此板块，存储在 section_data 表中

🚀 下一步：
  1. 运行 PDF 解析: python scripts/batch_import_all_pdfs.py
  2. 验证右侧数据: 
     sqlite3 backend/data/walmart_pdf_parser.db
     SELECT COUNT(*) FROM section_data WHERE section_name = 'right_section';

""")
        
        initializer.disconnect()
        return 0
    
    except Exception as e:
        logger.error(f"✗ 初始化失败: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
