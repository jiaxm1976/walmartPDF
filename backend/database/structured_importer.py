#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
结构化数据数据库导入模块

功能：
  1. 直接将 jg_structured_data() 的输出导入到数据库
  2. 自动识别并合并低频字段（频率 < 2）到 {section_name}_其他
  3. 支持独立导入和批量导入

使用方式（集成到 PDF 解析流程中）：
  from scripts.db_structured_import import StructuredDataImporter
  
  importer = StructuredDataImporter('backend/data/walmart_pdf_parser.db')
  importer.import_jg_data(pdf_name, jg_structured_data)

作者：AI 数据库设计助手
日期：2026-01-01
"""

import json
import sqlite3
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from decimal import Decimal

logger = logging.getLogger(__name__)


class StructuredDataImporter:
    """结构化数据导入器"""
    
    def __init__(self, db_path: str = 'backend/data/walmart_pdf_parser.db'):
        self.db_path = Path(db_path)
        self.conn = None
        self._frequency_cache = {}
    
    def connect(self):
        """连接数据库"""
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        logger.info(f"✓ 已连接到数据库: {self.db_path}")
    
    def disconnect(self):
        """断开连接"""
        if self.conn:
            self.conn.close()
            logger.info("✓ 已断开数据库连接")
    
    def _load_frequency_map(self) -> Dict[str, set]:
        """
        加载字段频率映射，用于识别低频字段
        返回: {section_name: {high_freq_fields}}
        """
        if self._frequency_cache:
            return self._frequency_cache
        
        try:
            cursor = self.conn.execute(
                "SELECT section_name, field_name, frequency FROM field_frequency WHERE frequency >= 2"
            )
            
            freq_map = {}
            for row in cursor:
                section = row['section_name']
                field = row['field_name']
                if section not in freq_map:
                    freq_map[section] = set()
                freq_map[section].add(field)
            
            self._frequency_cache = freq_map
            return freq_map
        
        except Exception as e:
            logger.warning(f"⚠ 无法加载频率映射: {e}，将使用默认逻辑")
            return {}
    
    def _convert_value(self, value: Any) -> Any:
        """转换值为 JSON 兼容格式"""
        if value is None:
            return None
        if isinstance(value, (int, float, str, bool)):
            return value
        if isinstance(value, Decimal):
            return float(value)
        return str(value)
    
    def _merge_low_frequency_fields(
        self,
        section_name: str,
        fields_dict: Dict[str, Any],
        freq_map: Dict[str, set]
    ) -> Dict[str, Any]:
        """
        识别并合并低频字段到 {section_name}_其他
        
        Args:
            section_name: 板块名称
            fields_dict: 该板块的字段字典
            freq_map: 频率映射表
        
        Returns:
            合并后的字段字典
        """
        if section_name not in freq_map:
            # 如果频率表中没有该板块信息，保守起见，所有字段都保留
            return fields_dict
        
        high_freq_fields = freq_map[section_name]
        other_fields = {}
        merged_dict = {}
        
        for field_name, field_value in fields_dict.items():
            if field_name in high_freq_fields:
                # 高频字段，直接保留
                merged_dict[field_name] = self._convert_value(field_value)
            else:
                # 低频字段，收集到 other_fields
                other_fields[field_name] = self._convert_value(field_value)
        
        # 如果有低频字段，添加到 {section_name}_其他
        if other_fields:
            other_key = f'{section_name}_其他'
            merged_dict[other_key] = other_fields
            logger.debug(f"  合并 {section_name} 的 {len(other_fields)} 个低频字段")
        
        return merged_dict
    
    def import_jg_data(
        self,
        pdf_name: str,
        jg_structured_data: Dict[str, Any]
    ) -> Optional[int]:
        """
        导入 jg_structured_data() 的输出到数据库
        
        Args:
            pdf_name: PDF 文件名
            jg_structured_data: jg_structured_data() 的返回值
        
        Returns:
            statement_id (成功) 或 None (失败)
        """
        try:
            logger.info(f"开始导入: {pdf_name}")
            
            sections = jg_structured_data.get('sections', {})
            metadata = jg_structured_data.get('metadata', {})
            
            if not sections:
                logger.warning(f"⚠ {pdf_name}: 没有板块数据")
                return None
            
            # 加载频率映射
            freq_map = self._load_frequency_map()
            
            # Step 1: 提取 header 板块数据
            header_fields = sections.get('header', [])
            header_dict = {item['field']: item['value'] for item in header_fields}
            
            # Step 2: 创建 statement 记录
            statement_id = self._insert_statement(pdf_name, header_dict)
            if not statement_id:
                logger.error(f"✗ {pdf_name}: 创建 statement 记录失败")
                return None
            
            logger.info(f"  ✓ 创建 statement 记录 (ID: {statement_id})")
            
            # Step 3: 为每个板块创建 section_data 记录
            for section_name, items in sections.items():
                # 将 items (list) 转换为 dict
                section_dict = {item['field']: item['value'] for item in items}
                
                # 合并低频字段
                merged_dict = self._merge_low_frequency_fields(
                    section_name, section_dict, freq_map
                )
                
                # 写入 section_data 表
                success = self._insert_section_data(
                    statement_id, section_name, merged_dict
                )
                
                if success:
                    logger.info(f"  ✓ 板块'{section_name}': {len(merged_dict)} 个字段")
                else:
                    logger.warning(f"  ⚠ 板块'{section_name}': 导入失败")
            
            self.conn.commit()
            logger.info(f"✓ {pdf_name} 导入完成\n")
            return statement_id
        
        except Exception as e:
            logger.error(f"✗ {pdf_name} 导入失败: {e}")
            self.conn.rollback()
            return None
    
    def _insert_statement(self, pdf_name: str, header_dict: Dict) -> Optional[int]:
        """插入 statement 记录"""
        try:
            def safe_float(key):
                val = header_dict.get(key)
                if val is None:
                    return None
                try:
                    if isinstance(val, str):
                        val = val.replace('$', '').replace(',', '').strip()
                    return float(val)
                except (ValueError, AttributeError):
                    return None
            
            sql = """
            INSERT INTO statements (
                pdf_name,
                statement_period,
                payment_to_you,
                opening_balance,
                reserve_fund,
                pending_payment
            ) VALUES (?, ?, ?, ?, ?, ?)
            """
            
            cursor = self.conn.execute(sql, (
                pdf_name,
                header_dict.get('统计区间'),
                safe_float('向您支付的金额'),
                safe_float('期初余额'),
                safe_float('备用金'),
                safe_float('回款等待')
            ))
            
            return cursor.lastrowid
        
        except Exception as e:
            logger.error(f"✗ 插入 statement 失败: {e}")
            return None
    
    def _insert_section_data(
        self,
        statement_id: int,
        section_name: str,
        data_dict: Dict
    ) -> bool:
        """插入 section_data 记录"""
        try:
            sql = """
            INSERT OR REPLACE INTO section_data (
                statement_id,
                section_name,
                data
            ) VALUES (?, ?, ?)
            """
            
            self.conn.execute(sql, (
                statement_id,
                section_name,
                json.dumps(data_dict, ensure_ascii=False)
            ))
            
            return True
        
        except Exception as e:
            logger.error(f"✗ 插入 section_data 失败: {e}")
            return False


def batch_import_from_dir(
    db_path: str,
    json_dir: str
) -> tuple:
    """
    批量导入目录中的 JSON 文件
    
    Args:
        db_path: 数据库路径
        json_dir: 包含 JSON 文件的目录（每个文件是一个 jg_structured_data 的 JSON 输出）
    
    Returns:
        (success_count, error_count)
    """
    importer = StructuredDataImporter(db_path)
    importer.connect()
    
    json_path = Path(json_dir)
    success_count = 0
    error_count = 0
    
    for json_file in sorted(json_path.glob('*.json')):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                jg_data = json.load(f)
            
            pdf_name = json_file.stem.replace('_structured', '') + '.pdf'
            result = importer.import_jg_data(pdf_name, jg_data)
            
            if result:
                success_count += 1
            else:
                error_count += 1
        
        except Exception as e:
            logger.error(f"处理失败 {json_file.name}: {e}")
            error_count += 1
    
    importer.disconnect()
    return success_count, error_count


if __name__ == '__main__':
    # 测试用途
    import sys
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s | %(levelname)s | %(message)s'
    )
    
    if len(sys.argv) > 1:
        db_path = sys.argv[1]
    else:
        db_path = 'backend/data/walmart_pdf_parser.db'
    
    importer = StructuredDataImporter(db_path)
    importer.connect()
    
    # 测试查询
    cursor = importer.conn.execute(
        "SELECT COUNT(*) FROM statements"
    )
    count = cursor.fetchone()[0]
    print(f"当前 statements 表中有 {count} 条记录")
    
    importer.disconnect()
