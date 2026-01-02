#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从已解析的 parsed_data.json 导入到数据库（用于手动验证）

用法:
  . .venv/bin/activate && python scripts/import_parsed_json.py

"""
import json
from pathlib import Path
import logging
import sys

PROJECT_ROOT = Path(__file__).parent.parent
PARSED_FILE = PROJECT_ROOT / 'backend' / 'tests' / 'output' / 'manual_run_venv2' / 'parsed_data.json'
DB_PATH = PROJECT_ROOT / 'backend' / 'data' / 'walmart_pdf_parser.db'

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

def main():
    if not PARSED_FILE.exists():
        logger.error(f'未找到解析文件: {PARSED_FILE}')
        return 2

    with open(PARSED_FILE, 'r', encoding='utf-8') as f:
        parsed = json.load(f)

    # parse_pdf_direct 返回包含 left_section 和 right_section
    left = parsed.get('left_section') or {}
    right = parsed.get('right_section') or {}

    # jg_structured_data 期望顶层有 'sections' 和 'metadata'
    if 'sections' in left:
        jg_data = left
    else:
        # 容错：尝试转换旧格式
        jg_data = {'sections': {}, 'metadata': {}}

    # 将右侧数据加入 sections.right_section
    if right:
        jg_data.setdefault('sections', {})
        jg_data['sections']['right_section'] = []
        # 将 right 字典转换为 items 列表
        for k, v in right.items():
            jg_data['sections']['right_section'].append({'field': k, 'value': v, 'raw': str(v), 'line_no': 0})

    # 导入
    try:
        from backend.database.structured_importer import StructuredDataImporter
    except Exception as e:
        logger.error(f'导入 StructuredDataImporter 失败: {e}')
        return 3

    importer = StructuredDataImporter(str(DB_PATH))
    importer.connect()

    pdf_name = 'manual_run_parsed.pdf'
    logger.info(f'开始导入 {PARSED_FILE} -> {DB_PATH}（pdf_name={pdf_name}）')
    sid = importer.import_jg_data(pdf_name, jg_data)

    if sid:
        logger.info(f'导入成功, statement_id={sid}')
    else:
        logger.error('导入失败')

    # 打印计数
    cur = importer.conn.execute('SELECT COUNT(*) FROM statements')
    stmt_count = cur.fetchone()[0]
    cur = importer.conn.execute('SELECT COUNT(*) FROM section_data')
    sec_count = cur.fetchone()[0]
    logger.info(f'statements={stmt_count}, section_data={sec_count}')

    importer.disconnect()
    return 0

if __name__ == '__main__':
    sys.exit(main())
