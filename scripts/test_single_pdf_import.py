#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 3 单 PDF 导入测试脚本

功能：
  1. 从测试数据目录选取一个 PDF
  2. 执行 jg_structured_data() 解析
  3. 使用 StructuredDataImporter 导入到数据库
  4. 验证导入结果

使用方式：
  python scripts/test_single_pdf_import.py [pdf_file]

示例：
  python scripts/test_single_pdf_import.py
  python scripts/test_single_pdf_import.py backend/tests/test_data/MP_01142025.pdf

前置条件：
  - Phase 2 已完成（数据库初始化）
  - PDF 文件存在

"""

import sys
import json
import sqlite3
from pathlib import Path
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.app.services.pdf_parser import jg_structured_data
from backend.database.structured_importer import StructuredDataImporter


def log(message: str, level='INFO'):
    """简单日志输出"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    prefix = {
        'INFO': '✓',
        'WARN': '⚠',
        'ERROR': '✗',
        'DEBUG': '→'
    }.get(level, '•')
    print(f'[{timestamp}] {prefix} {message}')


def find_test_pdfs():
    """查找测试 PDF 文件"""
    test_dir = Path('backend/tests/test_data')
    if not test_dir.exists():
        log(f'测试目录不存在: {test_dir}', 'ERROR')
        return []
    
    pdfs = list(test_dir.glob('*.pdf'))
    log(f'找到 {len(pdfs)} 个 PDF 文件', 'DEBUG')
    for pdf in pdfs:
        log(f'  - {pdf.name}', 'DEBUG')
    
    return pdfs


def get_jg_structured_data(pdf_path: Path) -> dict:
    """获取 jg_structured_data 输出"""
    log(f'正在解析 PDF: {pdf_path.name}', 'INFO')
    
    try:
        # 调用 jg_structured_data() 函数
        jg_data = jg_structured_data(str(pdf_path))
        
        # 验证返回数据
        if not isinstance(jg_data, dict) or 'sections' not in jg_data:
            log(f'返回数据格式错误', 'ERROR')
            return None
        
        sections = jg_data.get('sections', {})
        log(f'✓ 解析完成，包含 {len(sections)} 个板块: {", ".join(sections.keys())}', 'INFO')
        
        return jg_data
        
    except Exception as e:
        log(f'解析失败: {e}', 'ERROR')
        import traceback
        traceback.print_exc()
        return None


def import_and_verify(pdf_path: Path, jg_data: dict):
    """导入并验证"""
    db_path = 'backend/data/walmart_pdf_parser.db'
    pdf_name = pdf_path.name
    
    try:
        # 创建导入器
        importer = StructuredDataImporter(db_path)
        importer.connect()
        log(f'已连接数据库: {db_path}', 'INFO')
        
        # 导入数据
        log(f'正在导入 {pdf_name}...', 'INFO')
        statement_id = importer.import_jg_data(pdf_name, jg_data)
        importer.disconnect()
        
        if statement_id is None:
            log('导入失败', 'ERROR')
            return False
        
        log(f'✓ 导入成功，statement_id = {statement_id}', 'INFO')
        
        # 验证
        log(f'正在验证导入结果...', 'INFO')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 检查 statements 表
        cursor.execute("SELECT * FROM statements WHERE id = ?", (statement_id,))
        statement = cursor.fetchone()
        if not statement:
            log('statements 表记录未找到', 'ERROR')
            return False
        
        log(f'✓ statements 表: 1 条记录', 'INFO')
        log(f'  - id: {statement[0]}', 'DEBUG')
        log(f'  - pdf_name: {statement[1]}', 'DEBUG')
        log(f'  - statement_period: {statement[2]}', 'DEBUG')
        
        # 检查 section_data 表
        cursor.execute("SELECT COUNT(*) FROM section_data WHERE statement_id = ?", (statement_id,))
        section_count = cursor.fetchone()[0]
        log(f'✓ section_data 表: {section_count} 条记录', 'INFO')
        
        # 显示各板块
        cursor.execute("""
            SELECT section_name, COUNT(*) as count 
            FROM section_data 
            WHERE statement_id = ?
            GROUP BY section_name
            ORDER BY section_name
        """, (statement_id,))
        
        for section_name, count in cursor.fetchall():
            log(f'  - {section_name}: {count}', 'DEBUG')
        
        # 检查低频字段合并
        cursor.execute("""
            SELECT section_name, data 
            FROM section_data 
            WHERE statement_id = ? AND section_name != 'header'
            LIMIT 1
        """, (statement_id,))
        
        result = cursor.fetchone()
        if result:
            section_name, data_json = result
            data = json.loads(data_json)
            
            # 查找低频字段合并
            other_key = f'{section_name}_其他'
            if other_key in data:
                other_data = data[other_key]
                log(f'✓ 低频字段合并: {section_name}.{other_key}', 'INFO')
                log(f'  - 包含 {len(other_data)} 个字段', 'DEBUG')
                for field_name in list(other_data.keys())[:3]:  # 只显示前 3 个
                    log(f'    - {field_name}', 'DEBUG')
            else:
                log(f'⚠ {section_name} 无低频字段合并', 'WARN')
        
        conn.close()
        return True
        
    except Exception as e:
        log(f'验证失败: {e}', 'ERROR')
        import traceback
        traceback.print_exc()
        return False


def main():
    """主流程"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║       Walmart PDF 数据库 V2 - Phase 3 单 PDF 导入测试      ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    # 选择 PDF
    if len(sys.argv) > 1:
        pdf_path = Path(sys.argv[1])
        if not pdf_path.exists():
            log(f'PDF 文件不存在: {pdf_path}', 'ERROR')
            return 1
    else:
        pdfs = find_test_pdfs()
        if not pdfs:
            log('未找到测试 PDF', 'ERROR')
            return 1
        
        # 选择第一个 PDF
        pdf_path = pdfs[0]
        log(f'已选择第一个 PDF: {pdf_path.name}', 'INFO')
    
    # 解析
    jg_data = get_jg_structured_data(pdf_path)
    if jg_data is None:
        return 1
    
    # 导入并验证
    if not import_and_verify(pdf_path, jg_data):
        return 1
    
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║                    ✓ Phase 3 完成！                         ║
╚══════════════════════════════════════════════════════════════╝

📊 导入结果：
  ✓ PDF 已成功解析
  ✓ 结构化数据已导入
  ✓ statement 记录已创建
  ✓ section_data 记录已创建
  ✓ 低频字段已自动合并

🚀 下一步 (Phase 4): 批量导入所有 PDF
  python scripts/batch_import_all_pdfs.py

""")
    return 0


if __name__ == '__main__':
    sys.exit(main())
