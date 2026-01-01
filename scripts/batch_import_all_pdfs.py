#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 4 批量导入所有 PDF 脚本

功能：
  1. 遍历所有测试 PDF 文件
  2. 执行 jg_structured_data() 解析
  3. 批量导入到数据库
  4. 生成导入统计报告

使用方式：
  python scripts/batch_import_all_pdfs.py

前置条件：
  - Phase 2 已完成（数据库初始化）
  - Phase 3 通过（单 PDF 导入测试）

"""

import sys
import json
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.app.services.pdf_parser import jg_structured_data
from backend.database.structured_importer import StructuredDataImporter


class BatchImportLogger:
    """批量导入日志记录"""
    
    def __init__(self):
        self.records = []  # 导入记录
        self.errors = []   # 错误记录
    
    def log(self, message: str, level='INFO'):
        """记录日志"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        prefix = {
            'INFO': '✓',
            'WARN': '⚠',
            'ERROR': '✗',
            'DEBUG': '→'
        }.get(level, '•')
        log_msg = f'[{timestamp}] {prefix} {message}'
        print(log_msg)
        
        if level == 'ERROR':
            self.errors.append(message)
    
    def add_record(self, pdf_name: str, statement_id: int, section_count: int):
        """记录导入成功"""
        self.records.append({
            'pdf_name': pdf_name,
            'statement_id': statement_id,
            'section_count': section_count,
            'timestamp': datetime.now().isoformat()
        })
    
    def summary(self):
        """生成统计摘要"""
        return {
            'total_pdfs': len(self.records),
            'total_sections': sum(r['section_count'] for r in self.records),
            'errors': len(self.errors),
            'success_rate': f'{len(self.records) / (len(self.records) + len(self.errors)) * 100:.1f}%' if (len(self.records) + len(self.errors)) > 0 else 'N/A'
        }


def find_test_pdfs():
    """查找测试 PDF 文件"""
    test_dir = Path('backend/tests/test_data')
    if not test_dir.exists():
        print(f'✗ 测试目录不存在: {test_dir}')
        return []
    
    pdfs = sorted(list(test_dir.glob('*.pdf')))
    return pdfs


def process_pdf(pdf_path: Path, importer: StructuredDataImporter, logger: BatchImportLogger) -> Tuple[bool, int]:
    """处理单个 PDF"""
    pdf_name = pdf_path.name
    
    try:
        # 解析 PDF
        logger.log(f'正在处理: {pdf_name}', 'INFO')
        jg_data = jg_structured_data(str(pdf_path))
        
        if not isinstance(jg_data, dict) or 'sections' not in jg_data:
            logger.log(f'  → 数据格式错误', 'ERROR')
            return False, 0
        
        # 导入数据
        statement_id = importer.import_jg_data(pdf_name, jg_data)
        if statement_id is None:
            logger.log(f'  → 导入失败', 'ERROR')
            return False, 0
        
        # 统计板块数
        section_count = len(jg_data['sections'])
        logger.log(f'  ✓ 导入成功 (statement_id={statement_id}, 板块={section_count})', 'INFO')
        logger.add_record(pdf_name, statement_id, section_count)
        
        return True, section_count
        
    except Exception as e:
        logger.log(f'  ✗ 处理失败: {e}', 'ERROR')
        return False, 0


def verify_database(logger: BatchImportLogger) -> Dict:
    """验证数据库完整性"""
    db_path = 'backend/data/walmart_pdf_parser.db'
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 统计记录
        cursor.execute("SELECT COUNT(*) FROM statements;")
        statement_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM section_data;")
        section_data_count = cursor.fetchone()[0]
        
        # 板块分布
        cursor.execute("""
            SELECT section_name, COUNT(*) as count 
            FROM section_data 
            GROUP BY section_name
            ORDER BY count DESC
        """)
        section_dist = dict(cursor.fetchall())
        
        # 低频字段合并统计
        cursor.execute("""
            SELECT COUNT(*) FROM section_data 
            WHERE json_extract(data, '$.' || section_name || '_其他') IS NOT NULL
        """)
        other_fields_count = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'statement_count': statement_count,
            'section_data_count': section_data_count,
            'section_distribution': section_dist,
            'other_fields_count': other_fields_count
        }
        
    except Exception as e:
        logger.log(f'验证失败: {e}', 'ERROR')
        return {}


def main():
    """主流程"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║      Walmart PDF 数据库 V2 - Phase 4 批量导入所有 PDF      ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    logger = BatchImportLogger()
    
    # 查找 PDF
    pdfs = find_test_pdfs()
    if not pdfs:
        logger.log('未找到测试 PDF', 'ERROR')
        return 1
    
    logger.log(f'找到 {len(pdfs)} 个 PDF 文件', 'INFO')
    
    # 初始化导入器
    db_path = 'backend/data/walmart_pdf_parser.db'
    importer = StructuredDataImporter(db_path)
    
    try:
        importer.connect()
        logger.log(f'已连接数据库: {db_path}', 'INFO')
        
        # 处理每个 PDF
        print('\n' + '='*60)
        logger.log(f'开始批量导入 {len(pdfs)} 个 PDF...', 'INFO')
        print('='*60 + '\n')
        
        for i, pdf_path in enumerate(pdfs, 1):
            logger.log(f'[{i}/{len(pdfs)}] {pdf_path.name}', 'DEBUG')
            process_pdf(pdf_path, importer, logger)
        
        importer.disconnect()
        logger.log('导入完成', 'INFO')
        
    except Exception as e:
        logger.log(f'批量导入失败: {e}', 'ERROR')
        return 1
    
    # 验证
    print('\n' + '='*60)
    logger.log('正在验证数据库...', 'INFO')
    print('='*60 + '\n')
    
    db_info = verify_database(logger)
    
    # 生成报告
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║                    ✓ Phase 4 完成！                         ║
╚══════════════════════════════════════════════════════════════╝

📊 导入统计：
  ✓ 已导入 {logger.summary()['total_pdfs']} 个 PDF
  ✓ 已创建 {logger.summary()['total_sections']} 个板块记录
  ✓ 成功率: {logger.summary()['success_rate']}

📈 数据库验证：
  ✓ statements 表: {db_info.get('statement_count', 0)} 条记录
  ✓ section_data 表: {db_info.get('section_data_count', 0)} 条记录
  ✓ 低频字段合并: {db_info.get('other_fields_count', 0)} 个

📍 板块分布：
""")
    
    for section_name, count in db_info.get('section_distribution', {}).items():
        print(f'  • {section_name}: {count} 条')
    
    if logger.errors:
        print(f'\n⚠️  错误总结：')
        for error in logger.errors:
            print(f'  - {error}')
    
    print(f"""
🚀 下一步 (Phase 5): 验证查询模式
  python scripts/verify_queries.py

""")
    
    return 0 if len(logger.errors) == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
