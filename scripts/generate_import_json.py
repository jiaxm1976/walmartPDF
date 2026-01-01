#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从 PDF 解析结果生成数据库导入格式的 JSON 文件

功能：
  1. 读取已解析的 PDF 数据（步长 5 结构化数据）
  2. 转换为新的板块结构 (jg_structured_data 格式)
  3. 输出到 PdfData 目录供数据库导入脚本使用

使用：
  python scripts/generate_import_json.py

"""

import json
import sys
from pathlib import Path
from typing import Dict, Any, List
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).parent.parent
PDF_DATA_DIR = PROJECT_ROOT.parent / 'PdfData'
TEST_OUTPUT_DIR = PROJECT_ROOT / 'backend' / 'tests' / 'output'

# 确保 PdfData 目录存在
PDF_DATA_DIR.mkdir(parents=True, exist_ok=True)

def convert_to_jg_structure(parsed_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    将原始解析数据转换为 jg_structured_data 格式
    
    原始格式 (classdata):
    {
        'header': {field1: value1, field2: value2, ...},
        'sales': {...},
        ...
    }
    
    新格式 (jg_structured_data):
    {
        'sections': {
            'header': [
                {'field': 'field1', 'value': 'value1', 'raw': 'raw_text', 'line_no': 0},
                ...
            ],
            ...
        },
        'metadata': {
            'section_order': ['header', 'sales', ...],
            'section_count': N,
            'detail_count': M,
            'processed_at': 'ISO timestamp'
        }
    }
    """
    
    classdata = parsed_data.get('classdata', {})
    if not classdata:
        return {'sections': {}, 'metadata': {'section_order': [], 'section_count': 0, 'detail_count': 0}}
    
    sections = {}
    section_order = []
    total_details = 0
    
    for section_name, fields_dict in classdata.items():
        if not isinstance(fields_dict, dict):
            continue
            
        section_items = []
        for field_name, field_value in fields_dict.items():
            item = {
                'field': str(field_name),
                'value': str(field_value) if field_value is not None else None,
                'raw': str(field_value) if field_value is not None else None,
                'line_no': 0  # 原始数据中没有行号信息
            }
            section_items.append(item)
        
        if section_items:
            sections[section_name] = section_items
            section_order.append(section_name)
            total_details += len(section_items)
    
    return {
        'sections': sections,
        'metadata': {
            'section_order': section_order,
            'section_count': len(sections),
            'detail_count': total_details,
            'processed_at': ''
        }
    }

def main():
    """主函数"""
    logger.info("=" * 70)
    logger.info("生成数据库导入 JSON 文件")
    logger.info("=" * 70)
    
    # 查找所有调试输出目录
    debug_dirs = sorted([d for d in TEST_OUTPUT_DIR.iterdir() if d.is_dir() and d.name.startswith('debug_')])
    
    if not debug_dirs:
        logger.error("✗ 未找到调试输出目录，请先运行 test_debug_flow.py")
        return 1
    
    success_count = 0
    error_count = 0
    
    for debug_dir in debug_dirs:
        parsed_file = debug_dir / 'parsed_data.json'
        
        if not parsed_file.exists():
            continue
        
        try:
            # 读取解析数据
            with open(parsed_file, 'r', encoding='utf-8') as f:
                parsed_data = json.load(f)
            
            # 获取 PDF 文件名
            pdf_name = parsed_data.get('pdf_file_path', '').split('/')[-1]
            if not pdf_name:
                logger.warning(f"⚠ 跳过 {debug_dir.name}：无法提取 PDF 文件名")
                continue
            
            # 转换格式
            jg_data = convert_to_jg_structure(parsed_data)
            
            # 输出到 PdfData
            output_file = PDF_DATA_DIR / f"{pdf_name.replace('.pdf', '')}.json"
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(jg_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"✓ {pdf_name:45} → {output_file.name}")
            success_count += 1
            
        except Exception as e:
            logger.error(f"✗ 处理失败 {debug_dir.name}: {e}")
            error_count += 1
    
    logger.info("=" * 70)
    logger.info(f"完成: {success_count} 成功，{error_count} 失败")
    logger.info(f"JSON 文件位置: {PDF_DATA_DIR}")
    logger.info("=" * 70)
    
    if success_count == 0:
        logger.error("✗ 未生成任何文件，请检查输入数据")
        return 1
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
