#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 4 批量导入所有 PDF - 改进版

功能：
  1. 遍历所有测试 PDF 文件
  2. 解析每个 PDF 获取结构化数据
  3. 批量导入到数据库
  4. 生成统计报告

"""

import sys
import json
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.database.structured_importer import StructuredDataImporter
from backend.app.services.pdf_parser_service import PDFParserService


class BatchImportLogger:
    """批量导入日志记录"""
    
    def __init__(self):
        self.records = []
        self.errors = []
    
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
        total = len(self.records) + len(self.errors)
        return {
            'total_pdfs': len(self.records),
            'total_sections': sum(r['section_count'] for r in self.records),
            'errors': len(self.errors),
            'success_rate': f'{len(self.records) / total * 100:.1f}%' if total > 0 else 'N/A'
        }


def find_test_pdfs():
    """查找测试 PDF 文件"""
    # 尝试多个位置
    test_dirs = [
        Path('backend/tests/test_data'),
        Path('PdfData'),
        Path('data/test_pdfs')
    ]
    
    all_pdfs = []
    for test_dir in test_dirs:
        if test_dir.exists():
            pdfs = sorted(list(test_dir.glob('*.pdf')))
            if pdfs:
                print(f'✓ 在 {test_dir} 中找到 {len(pdfs)} 个 PDF 文件')
                all_pdfs.extend(pdfs)
    
    if not all_pdfs:
        print(f'✗ 没有找到任何 PDF 文件')
        return []
    
    return all_pdfs


def process_pdf(pdf_path: Path, importer: StructuredDataImporter, logger: BatchImportLogger) -> Tuple[bool, int]:
    """处理单个 PDF"""
    pdf_name = pdf_path.name
    
    try:
        # Step 1: 解析 PDF
        logger.log(f'[1/3] 正在解析 PDF: {pdf_name}', 'DEBUG')
        parser = PDFParserService()
        result = parser.parse_pdf_direct(str(pdf_path))
        
        if not result.get('success'):
            logger.log(f'PDF 解析失败: {result.get("error")}', 'ERROR')
            return False, 0
        
        # Step 2: 获取结构化数据
        logger.log(f'[2/3] 正在提取结构化数据...', 'DEBUG')
        parsed_data = result.get('data', {})
        
        # parse_pdf_direct 返回 left_section，需要从中提取 jg_structured_data
        left_section = parsed_data.get('left_section', {})
        
        if not left_section:
            logger.log(f'解析结果中没有 left_section 数据', 'WARN')
            jg_data = {"sections": {"header": [], "footer": []}, "metadata": {}}
        else:
            # left_section 已经包含 jg_structured_data 格式的数据
            jg_data = left_section
            
            if not isinstance(jg_data, dict) or 'sections' not in jg_data:
                logger.log(f'结构化数据格式错误，使用默认结构', 'WARN')
                jg_data = {"sections": {"header": [], "footer": []}, "metadata": {}}
        
        # Step 3: 导入到数据库
        logger.log(f'[3/3] 正在导入到数据库...', 'DEBUG')
        statement_id = importer.import_jg_data(pdf_name, jg_data)
        
        if statement_id is None:
            logger.log(f'导入失败', 'ERROR')
            return False, 0
        
        # 统计板块数
        section_count = len(jg_data.get('sections', {}))
        logger.log(f'{pdf_name} → statement_id={statement_id}, 板块={section_count}', 'INFO')
        logger.add_record(pdf_name, statement_id, section_count)
        
        return True, section_count
        
    except Exception as e:
        logger.log(f'{pdf_name} 处理失败: {e}', 'ERROR')
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
        
        conn.close()
        
        return {
            'statement_count': statement_count,
            'section_data_count': section_data_count,
            'section_distribution': section_dist
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
    for pdf in pdfs:
        logger.log(f'  • {pdf.name}', 'DEBUG')
    
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
        
        success_count = 0
        for i, pdf_path in enumerate(pdfs, 1):
            logger.log(f'[{i}/{len(pdfs)}] 处理: {pdf_path.name}', 'DEBUG')
            success, _ = process_pdf(pdf_path, importer, logger)
            if success:
                success_count += 1
        
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

📍 板块分布：
""")
    
    for section_name, count in db_info.get('section_distribution', {}).items():
        print(f'  • {section_name}: {count} 条')
    
    if logger.errors:
        print(f'\n⚠️  错误总结（{len(logger.errors)} 个）：')
        for error in logger.errors[:5]:  # 只显示前 5 个错误
            print(f'  - {error}')
        if len(logger.errors) > 5:
            print(f'  ... 还有 {len(logger.errors) - 5} 个错误')
    
    print(f"""
🚀 下一步 (Phase 5): 验证查询模式
  python scripts/verify_queries.py

""")
    
    return 0 if len(logger.errors) == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
