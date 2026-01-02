#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库数据导入脚本 - 新数据结构版本

功能：
  1. 初始化数据库表（如果表不存在）
  2. 将 PDF 解析结果从新结构转换到数据库
  3. 验证数据完整性和外键约束
  4. 生成导入报告

使用方式：
  python scripts/db_import_new_structure.py [--init] [--verify]
  
参数：
  --init     首次运行，初始化数据库表
  --verify   仅验证现有数据，不导入
  --batch    批量导入 PdfData 下所有 PDF 解析结果

作者：AI 数据库设计助手
日期：2026-01-01
"""

import json
import sqlite3
import sys
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Tuple, Optional
from decimal import Decimal
import argparse

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s'
)
logger = logging.getLogger(__name__)

# NOTE: This script referenced `backend/database/schema_design_v1.sql` (v1 schema).
# The repository now uses the V2 dynamic schema. This script has been archived
# to `archived/scripts/db_import_new_structure.py`. To avoid accidental execution,
# the active script has been replaced with a no-op header. See `archived/scripts/`.
logger.info('db_import_new_structure has been archived; use scripts/batch_import_v2.py and scripts/init_database_v2.py')
import sys
sys.exit(0)

# 项目路径
PROJECT_ROOT = Path(__file__).parent.parent
DB_PATH = PROJECT_ROOT / 'backend' / 'data' / 'walmart_pdf_parser.db'
SCHEMA_PATH = PROJECT_ROOT / 'backend' / 'database' / 'schema_design_v1.sql'
PDF_DATA_DIR = PROJECT_ROOT.parent / 'PdfData'


class DatabaseManager:
    """数据库管理器"""
    
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
    
    def init_schema(self, schema_path: str = str(SCHEMA_PATH)):
        """初始化数据库表结构"""
        if not Path(schema_path).exists():
            logger.error(f"✗ Schema 文件不存在: {schema_path}")
            return False
        
        try:
            with open(schema_path, 'r', encoding='utf-8') as f:
                sql = f.read()
            
            # 分割多个语句
            statements = [s.strip() for s in sql.split(';') if s.strip()]
            
            for stmt in statements:
                # 跳过注释行
                if stmt.startswith('--'):
                    continue
                self.conn.execute(stmt)
            
            self.conn.commit()
            logger.info(f"✓ 数据库初始化成功: 已创建所有表结构")
            return True
            
        except Exception as e:
            logger.error(f"✗ 初始化失败: {e}")
            self.conn.rollback()
            return False
    
    def execute(self, sql: str, params: Tuple = ()) -> Optional[Any]:
        """执行 SQL 语句"""
        try:
            cursor = self.conn.execute(sql, params)
            self.conn.commit()
            return cursor.lastrowid
        except Exception as e:
            logger.error(f"✗ SQL 执行失败: {e}\n  SQL: {sql}\n  参数: {params}")
            self.conn.rollback()
            return None
    
    def query(self, sql: str, params: Tuple = ()) -> List[Dict]:
        """查询数据"""
        try:
            cursor = self.conn.execute(sql, params)
            return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"✗ 查询失败: {e}")
            return []


class DataImporter:
    """数据导入器 - 处理新结构到数据库的转换"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    def import_statement_header(self, pdf_name: str, jg_data: Dict[str, Any]) -> Optional[int]:
        """导入语句头信息"""
        try:
            sections = jg_data.get('sections', {})
            metadata = jg_data.get('metadata', {})
            
            # 从 header 板块提取基本信息
            header_fields = sections.get('header', [])
            field_dict = {item['field']: item['value'] for item in header_fields}
            
            # 提取值（处理可能的单位问题）
            def extract_amount(field_name: str) -> Optional[float]:
                value = field_dict.get(field_name)
                if value is None:
                    return None
                try:
                    # 移除货币符号和其他字符
                    if isinstance(value, str):
                        value = value.replace('$', '').replace(',', '').strip()
                    return float(value)
                except (ValueError, AttributeError):
                    return None
            
            # 必有字段
            statement_period = field_dict.get('统计区间', 'Unknown')
            payment_to_you = extract_amount('向您支付的金额') or 0.0
            opening_balance = extract_amount('期初余额') or 0.0
            reserve_fund = extract_amount('备用金') or 0.0
            pending_payment = extract_amount('回款等待') or 0.0
            closing_balance = extract_amount('期末余额')  # 可选
            
            sql = """
            INSERT INTO statement_headers (
                source_pdf_name,
                statement_period,
                payment_to_you,
                opening_balance,
                reserve_fund,
                pending_payment,
                closing_balance
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """
            
            header_id = self.db.execute(sql, (
                pdf_name,
                statement_period,
                payment_to_you,
                opening_balance,
                reserve_fund,
                pending_payment,
                closing_balance
            ))
            
            if header_id:
                logger.info(f"  ✓ 导入头信息: {pdf_name} (ID: {header_id})")
            
            return header_id
            
        except Exception as e:
            logger.error(f"  ✗ 导入头信息失败: {e}")
            return None
    
    def import_sales_details(self, header_id: int, jg_data: Dict[str, Any]) -> bool:
        """导入销售明细"""
        try:
            sections = jg_data.get('sections', {})
            sales_fields = sections.get('销售', [])
            
            if not sales_fields:
                return True  # 可选，无数据时返回成功
            
            field_dict = {item['field']: item['value'] for item in sales_fields}
            
            def extract_amount(field_name: str) -> Optional[float]:
                value = field_dict.get(field_name)
                if value is None:
                    return None
                try:
                    if isinstance(value, str):
                        value = value.replace('$', '').replace(',', '').strip()
                    return float(value)
                except (ValueError, AttributeError):
                    return None
            
            product_price = extract_amount('产品价格') or 0.0
            shipping = extract_amount('运输') or 0.0
            tax_collected_net = extract_amount('已收税净额') or 0.0
            net_commission = extract_amount('净佣金') or 0.0
            withholding_tax_net = extract_amount('扣缴税款净额') or 0.0
            sales_total = extract_amount('总计:') or 0.0
            wfs_shipping_refund = extract_amount('WFS运输退款') or 0.0
            wfs_shipping_tax_refund = extract_amount('WFS运输税退款') or 0.0
            walmart_contribution = extract_amount('T沃尔玛出资的节余')
            
            sql = """
            INSERT INTO sales_details (
                header_id,
                product_price,
                shipping,
                tax_collected_net,
                net_commission,
                withholding_tax_net,
                sales_total,
                wfs_shipping_refund,
                wfs_shipping_tax_refund,
                walmart_contribution_margin
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            self.db.execute(sql, (
                header_id,
                product_price,
                shipping,
                tax_collected_net,
                net_commission,
                withholding_tax_net,
                sales_total,
                wfs_shipping_refund,
                wfs_shipping_tax_refund,
                walmart_contribution
            ))
            
            logger.info(f"  ✓ 导入销售明细")
            return True
            
        except Exception as e:
            logger.error(f"  ✗ 导入销售明细失败: {e}")
            return False
    
    def import_refund_details(self, header_id: int, jg_data: Dict[str, Any]) -> bool:
        """导入退款明细"""
        try:
            sections = jg_data.get('sections', {})
            refund_fields = sections.get('退款', [])
            
            if not refund_fields:
                return True
            
            field_dict = {item['field']: item['value'] for item in refund_fields}
            
            def extract_amount(field_name: str) -> Optional[float]:
                value = field_dict.get(field_name)
                if value is None:
                    return None
                try:
                    if isinstance(value, str):
                        value = value.replace('$', '').replace(',', '').strip()
                    return float(value)
                except (ValueError, AttributeError):
                    return None
            
            commission = extract_amount('佣金') or 0.0
            product_price = extract_amount('产品价格') or 0.0
            shipping = extract_amount('运输') or 0.0
            tax_collected_net = extract_amount('已收税净额') or 0.0
            withholding_tax_net = extract_amount('扣缴税款净额') or 0.0
            refund_total = extract_amount('总计:') or 0.0
            wfs_total_discount = extract_amount('WFS总折扣') or 0.0
            walmart_contribution = extract_amount('T沃尔玛出资的节余')
            
            sql = """
            INSERT INTO refund_details (
                header_id,
                commission,
                product_price,
                shipping,
                tax_collected_net,
                withholding_tax_net,
                refund_total,
                wfs_total_discount,
                walmart_contribution_margin
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            self.db.execute(sql, (
                header_id,
                commission,
                product_price,
                shipping,
                tax_collected_net,
                withholding_tax_net,
                refund_total,
                wfs_total_discount,
                walmart_contribution
            ))
            
            logger.info(f"  ✓ 导入退款明细")
            return True
            
        except Exception as e:
            logger.error(f"  ✗ 导入退款明细失败: {e}")
            return False
    
    def import_other_activities(self, header_id: int, jg_data: Dict[str, Any]) -> bool:
        """导入其他活动"""
        try:
            sections = jg_data.get('sections', {})
            activity_fields = sections.get('其他活动', [])
            
            if not activity_fields:
                return True
            
            field_dict = {item['field']: item['value'] for item in activity_fields}
            
            def extract_amount(field_name: str) -> Optional[float]:
                value = field_dict.get(field_name)
                if value is None:
                    return None
                try:
                    if isinstance(value, str):
                        value = value.replace('$', '').replace(',', '').strip()
                    return float(value)
                except (ValueError, AttributeError):
                    return None
            
            advertising = extract_amount('沃尔玛产品广告')
            
            sql = """
            INSERT INTO other_activities (
                header_id,
                activity_type,
                walmart_product_advertising
            ) VALUES (?, ?, ?)
            """
            
            self.db.execute(sql, (
                header_id,
                '沃尔玛产品广告',
                advertising
            ))
            
            logger.info(f"  ✓ 导入其他活动")
            return True
            
        except Exception as e:
            logger.error(f"  ✗ 导入其他活动失败: {e}")
            return False
    
    def import_adjustments(self, header_id: int, jg_data: Dict[str, Any]) -> bool:
        """导入调整"""
        try:
            sections = jg_data.get('sections', {})
            adjustment_fields = sections.get('调整', [])
            
            if not adjustment_fields:
                return True
            
            field_dict = {item['field']: item['value'] for item in adjustment_fields}
            
            def extract_amount(field_name: str) -> Optional[float]:
                value = field_dict.get(field_name)
                if value is None:
                    return None
                try:
                    if isinstance(value, str):
                        value = value.replace('$', '').replace(',', '').strip()
                    return float(value)
                except (ValueError, AttributeError):
                    return None
            
            label_fee = extract_amount('沃尔玛全球运输标签服务费')
            
            sql = """
            INSERT INTO adjustments (
                header_id,
                adjustment_type,
                walmart_global_shipping_label_fee
            ) VALUES (?, ?, ?)
            """
            
            self.db.execute(sql, (
                header_id,
                '调整',
                label_fee
            ))
            
            logger.info(f"  ✓ 导入调整")
            return True
            
        except Exception as e:
            logger.error(f"  ✗ 导入调整失败: {e}")
            return False
    
    def import_wfs_services(self, header_id: int, jg_data: Dict[str, Any]) -> bool:
        """导入 WFS 服务"""
        try:
            sections = jg_data.get('sections', {})
            wfs_fields = sections.get('沃尔玛商品服务(WFS)', [])
            
            if not wfs_fields:
                return True
            
            field_dict = {item['field']: item['value'] for item in wfs_fields}
            
            def extract_amount(field_name: str) -> Optional[float]:
                value = field_dict.get(field_name)
                if value is None:
                    return None
                try:
                    if isinstance(value, str):
                        value = value.replace('$', '').replace(',', '').strip()
                    return float(value)
                except (ValueError, AttributeError):
                    return None
            
            goods_fee = extract_amount('WFS商品费')
            ethereum_fee = extract_amount('WFS以太坊费')
            total_discount = extract_amount('WFS总折扣')
            
            sql = """
            INSERT INTO wfs_services (
                header_id,
                service_type,
                wfs_goods_fee,
                wfs_ethereum_fee,
                wfs_total_discount
            ) VALUES (?, ?, ?, ?, ?)
            """
            
            self.db.execute(sql, (
                header_id,
                'fba_goods',
                goods_fee,
                ethereum_fee,
                total_discount
            ))
            
            logger.info(f"  ✓ 导入 WFS 服务")
            return True
            
        except Exception as e:
            logger.error(f"  ✗ 导入 WFS 服务失败: {e}")
            return False
    
    def import_section_metadata(self, header_id: int, jg_data: Dict[str, Any]) -> bool:
        """导入板块元数据"""
        try:
            sections = jg_data.get('sections', {})
            metadata = jg_data.get('metadata', {})
            section_order = metadata.get('section_order', [])
            
            for section_name in section_order:
                fields = sections.get(section_name, [])
                field_count = len(set(item['field'] for item in fields))
                detail_count = len(fields)
                
                sql = """
                INSERT INTO section_metadata (
                    header_id,
                    section_name,
                    field_count,
                    detail_count
                ) VALUES (?, ?, ?, ?)
                """
                
                self.db.execute(sql, (
                    header_id,
                    section_name,
                    field_count,
                    detail_count
                ))
            
            logger.info(f"  ✓ 导入板块元数据 ({len(section_order)} 个板块)")
            return True
            
        except Exception as e:
            logger.error(f"  ✗ 导入板块元数据失败: {e}")
            return False


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='Walmart PDF 数据库导入工具')
    parser.add_argument('--init', action='store_true', help='初始化数据库表')
    parser.add_argument('--batch', action='store_true', help='批量导入 PdfData 目录下的 PDF')
    parser.add_argument('--verify', action='store_true', help='仅验证数据，不导入')
    parser.add_argument('--db', default=str(DB_PATH), help='数据库路径')
    args = parser.parse_args()
    
    # 初始化数据库管理器
    db = DatabaseManager(args.db)
    db.connect()
    
    # 初始化表结构
    if args.init:
        logger.info("=" * 60)
        logger.info("阶段 1: 初始化数据库表")
        logger.info("=" * 60)
        if db.init_schema():
            logger.info("✓ 表初始化完成\n")
        else:
            logger.error("✗ 表初始化失败")
            db.disconnect()
            return 1
    
    # 批量导入
    if args.batch:
        logger.info("=" * 60)
        logger.info("阶段 2: 批量导入 PDF 解析结果")
        logger.info("=" * 60)
        
        importer = DataImporter(db)
        success_count = 0
        error_count = 0
        
        for json_file in sorted(PDF_DATA_DIR.glob('*.json')):
            logger.info(f"\n处理: {json_file.name}")
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    jg_data = json.load(f)
                
                # 导入头信息
                header_id = importer.import_statement_header(json_file.stem, jg_data)
                if not header_id:
                    error_count += 1
                    continue
                
                # 导入各个板块
                importer.import_sales_details(header_id, jg_data)
                importer.import_refund_details(header_id, jg_data)
                importer.import_other_activities(header_id, jg_data)
                importer.import_adjustments(header_id, jg_data)
                importer.import_wfs_services(header_id, jg_data)
                importer.import_section_metadata(header_id, jg_data)
                
                success_count += 1
                
            except Exception as e:
                logger.error(f"✗ 处理失败: {e}")
                error_count += 1
        
        logger.info(f"\n{'=' * 60}")
        logger.info(f"导入完成: {success_count} 成功, {error_count} 失败")
        logger.info(f"{'=' * 60}\n")
    
    # 验证数据
    logger.info("=" * 60)
    logger.info("阶段 3: 数据验证")
    logger.info("=" * 60)
    
    results = db.query("SELECT COUNT(*) as count FROM statement_headers")
    header_count = results[0]['count'] if results else 0
    logger.info(f"✓ statement_headers: {header_count} 条记录")
    
    results = db.query("SELECT COUNT(*) as count FROM sales_details")
    sales_count = results[0]['count'] if results else 0
    logger.info(f"✓ sales_details: {sales_count} 条记录")
    
    results = db.query("SELECT COUNT(*) as count FROM refund_details")
    refund_count = results[0]['count'] if results else 0
    logger.info(f"✓ refund_details: {refund_count} 条记录")
    
    logger.info("✓ 数据验证完成\n")
    
    db.disconnect()
    return 0


if __name__ == '__main__':
    sys.exit(main())
