#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
为数据库创建演示数据

基于字段频率分析结果，生成 6 个虚拟 PDF 的数据库导入数据
"""

import json
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).parent.parent
DB_PATH = PROJECT_ROOT / 'backend' / 'data' / 'walmart_pdf_parser.db'

# 虚拟数据模板（基于 6 个 PDF 的字段频率）
SAMPLE_DATA = [
    {
        'pdf_name': 'MP_01142025_statement_summary.pdf',
        'period': '2025年1月1日至2025年1月31日',
        'payment': 1234.56,
        'opening': 500.00,
        'reserve': 100.00,
        'pending': 50.00,
        'closing': 1284.56,
        'sales_price': 2000.00,
        'sales_shipping': 50.00,
        'sales_commission': 100.00,
        'sales_tax': 25.00,
        'sales_total': 2050.00,
        'refund_commission': 50.00,
        'refund_price': 100.00,
        'refund_shipping': 10.00,
        'refund_tax': 2.50,
        'refund_total': 110.00,
        'wfs_refund': 20.00,
        'advertising': 25.00,
    },
    {
        'pdf_name': 'MP_02112025_statement_summary.pdf',
        'period': '2025年2月1日至2025年2月28日',
        'payment': 1456.78,
        'opening': 1284.56,
        'reserve': 100.00,
        'pending': 60.00,
        'closing': 1394.56,
        'sales_price': 2200.00,
        'sales_shipping': 55.00,
        'sales_commission': 120.00,
        'sales_tax': 27.50,
        'sales_total': 2200.00,
        'refund_commission': 60.00,
        'refund_price': 120.00,
        'refund_shipping': 12.00,
        'refund_tax': 3.00,
        'refund_total': 132.00,
        'wfs_refund': 22.00,
        'advertising': 30.00,
    },
    {
        'pdf_name': 'MP_04222025_statement_summary.pdf',
        'period': '2025年4月22日至2025年5月22日',
        'payment': 2100.00,
        'opening': 1394.56,
        'reserve': 100.00,
        'pending': 75.00,
        'closing': 2175.00,
        'sales_price': 3000.00,
        'sales_shipping': 75.00,
        'sales_commission': 150.00,
        'sales_tax': 37.50,
        'sales_total': 3000.00,
        'refund_commission': 75.00,
        'refund_price': 150.00,
        'refund_shipping': 15.00,
        'refund_tax': 3.75,
        'refund_total': 165.00,
        'wfs_refund': 30.00,
        'advertising': 40.00,
    },
    {
        'pdf_name': 'MP_06032025_statement_summary.pdf',
        'period': '2025年6月3日至2025年7月3日',
        'payment': 1890.00,
        'opening': 2175.00,
        'reserve': 100.00,
        'pending': 80.00,
        'closing': 1970.00,
        'sales_price': 2800.00,
        'sales_shipping': 70.00,
        'sales_commission': 140.00,
        'sales_tax': 35.00,
        'sales_total': 2800.00,
        'refund_commission': 70.00,
        'refund_price': 140.00,
        'refund_shipping': 14.00,
        'refund_tax': 3.50,
        'refund_total': 154.00,
        'wfs_refund': 28.00,
        'advertising': 35.00,
    },
    {
        'pdf_name': 'MP_08262025_statement_summary.pdf',
        'period': '2025年8月26日至2025年9月26日',
        'payment': 2345.67,
        'opening': 1970.00,
        'reserve': 100.00,
        'pending': 90.00,
        'closing': 2435.67,
        'sales_price': 3200.00,
        'sales_shipping': 80.00,
        'sales_commission': 160.00,
        'sales_tax': 40.00,
        'sales_total': 3200.00,
        'refund_commission': 80.00,
        'refund_price': 160.00,
        'refund_shipping': 16.00,
        'refund_tax': 4.00,
        'refund_total': 176.00,
        'wfs_refund': 32.00,
        'advertising': 45.00,
    },
    {
        'pdf_name': 'MP_12032024_statement_summary.pdf',
        'period': '2024年12月3日至2025年1月3日',
        'payment': 1567.89,
        'opening': 400.00,
        'reserve': 100.00,
        'pending': 40.00,
        'closing': 1567.89,
        'sales_price': 2100.00,
        'sales_shipping': 52.50,
        'sales_commission': 105.00,
        'sales_tax': 26.25,
        'sales_total': 2100.00,
        'refund_commission': 52.50,
        'refund_price': 105.00,
        'refund_shipping': 10.50,
        'refund_tax': 2.63,
        'refund_total': 117.50,
        'wfs_refund': 21.00,
        'advertising': 28.00,
    },
]

def main():
    """主函数"""
    logger.info("=" * 70)
    logger.info("插入演示数据到数据库")
    logger.info("=" * 70)
    
    try:
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        
        inserted_count = 0
        
        for data in SAMPLE_DATA:
            try:
                # 插入 statement_headers
                cursor.execute("""
                    INSERT INTO statement_headers (
                        source_pdf_name,
                        statement_period,
                        payment_to_you,
                        opening_balance,
                        reserve_fund,
                        pending_payment,
                        closing_balance
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    data['pdf_name'],
                    data['period'],
                    data['payment'],
                    data['opening'],
                    data['reserve'],
                    data['pending'],
                    data['closing']
                ))
                
                header_id = cursor.lastrowid
                
                # 插入 sales_details
                cursor.execute("""
                    INSERT INTO sales_details (
                        header_id,
                        product_price,
                        shipping,
                        tax_collected_net,
                        net_commission,
                        withholding_tax_net,
                        sales_total,
                        wfs_shipping_refund
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    header_id,
                    data['sales_price'],
                    data['sales_shipping'],
                    data['sales_tax'],
                    data['sales_commission'],
                    data['sales_tax'],
                    data['sales_total'],
                    data['wfs_refund']
                ))
                
                # 插入 refund_details
                cursor.execute("""
                    INSERT INTO refund_details (
                        header_id,
                        commission,
                        product_price,
                        shipping,
                        tax_collected_net,
                        withholding_tax_net,
                        refund_total,
                        wfs_total_discount
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    header_id,
                    data['refund_commission'],
                    data['refund_price'],
                    data['refund_shipping'],
                    data['refund_tax'],
                    data['refund_tax'],
                    data['refund_total'],
                    2.50
                ))
                
                # 插入 other_activities
                cursor.execute("""
                    INSERT INTO other_activities (
                        header_id,
                        activity_type,
                        walmart_product_advertising
                    ) VALUES (?, ?, ?)
                """, (
                    header_id,
                    '沃尔玛产品广告',
                    data['advertising']
                ))
                
                # 插入 section_metadata
                sections = ['header', '销售', '退款', '其他活动']
                for section in sections:
                    cursor.execute("""
                        INSERT INTO section_metadata (
                            header_id,
                            section_name,
                            field_count,
                            detail_count
                        ) VALUES (?, ?, ?, ?)
                    """, (header_id, section, 5, 5))
                
                logger.info(f"✓ {data['pdf_name']}")
                inserted_count += 1
                
            except Exception as e:
                logger.error(f"✗ {data['pdf_name']}: {e}")
        
        conn.commit()
        conn.close()
        
        logger.info("=" * 70)
        logger.info(f"✓ 成功插入 {inserted_count} 个 PDF 的数据")
        logger.info("=" * 70)
        
        # 验证数据
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM statement_headers")
        header_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM sales_details")
        sales_count = cursor.fetchone()[0]
        
        logger.info(f"\n数据统计：")
        logger.info(f"  statement_headers: {header_count} 条")
        logger.info(f"  sales_details:     {sales_count} 条")
        
        # 查询财务汇总
        cursor.execute("SELECT * FROM financial_summary ORDER BY statement_period")
        results = cursor.fetchall()
        
        if results:
            logger.info(f"\n财务汇总：")
            for row in results:
                logger.info(f"  期间: {row[0]}, 平均支付: ${row[2]:.2f}, 总支付: ${row[3]:.2f}")
        
        conn.close()
        return 0
        
    except Exception as e:
        logger.error(f"✗ 错误: {e}")
        return 1

if __name__ == '__main__':
    main()
