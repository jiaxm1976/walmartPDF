#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库查询演示脚本

展示如何使用新的数据库结构进行常见查询
"""

import sqlite3
from pathlib import Path
from tabulate import tabulate

DB_PATH = Path(__file__).parent.parent / 'backend' / 'data' / 'walmart_pdf_parser.db'

def print_section(title):
    """打印章节标题"""
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}\n")

def execute_query(title, sql, headers=None):
    """执行查询并打印结果"""
    try:
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        cursor = conn.execute(sql)
        results = cursor.fetchall()
        
        if not results:
            print(f"✓ {title}")
            print("  （无数据）\n")
            return
        
        # 转换为列表格式
        rows = [list(row) for row in results]
        if headers is None:
            headers = list(results[0].keys())
        
        print(f"✓ {title}")
        print(tabulate(rows, headers=headers, tablefmt='grid'))
        print()
        
        conn.close()
    except Exception as e:
        print(f"✗ {title}")
        print(f"  错误: {e}\n")

def main():
    """主函数"""
    
    print("\n")
    print("╔" + "="*78 + "╗")
    print("║" + " "*20 + "Walmart PDF 数据库查询演示" + " "*33 + "║")
    print("╚" + "="*78 + "╝")
    
    # 查询 1: 数据库概览
    print_section("1. 数据库概览")
    
    execute_query(
        "表记录数统计",
        """
        SELECT 
            'statement_headers' as table_name,
            COUNT(*) as record_count
        FROM statement_headers
        UNION ALL
        SELECT 'sales_details', COUNT(*) FROM sales_details
        UNION ALL
        SELECT 'refund_details', COUNT(*) FROM refund_details
        UNION ALL
        SELECT 'other_activities', COUNT(*) FROM other_activities
        ORDER BY table_name;
        """,
        headers=['表名', '记录数']
    )
    
    # 查询 2: 财务汇总
    print_section("2. 财务汇总（按时间段）")
    
    execute_query(
        "各时间段的财务数据",
        """
        SELECT 
            h.statement_period as '时间段',
            ROUND(h.payment_to_you, 2) as '应付金额',
            ROUND(h.opening_balance, 2) as '期初余额',
            ROUND(h.closing_balance, 2) as '期末余额',
            COUNT(DISTINCT s.id) as '销售笔数',
            COUNT(DISTINCT r.id) as '退款笔数'
        FROM statement_headers h
        LEFT JOIN sales_details s ON h.id = s.header_id
        LEFT JOIN refund_details r ON h.id = r.header_id
        GROUP BY h.id, h.statement_period
        ORDER BY h.statement_period;
        """
    )
    
    # 查询 3: 销售明细
    print_section("3. 销售明细汇总")
    
    execute_query(
        "销售总额和佣金统计",
        """
        SELECT 
            h.statement_period as '时间段',
            ROUND(SUM(s.product_price), 2) as '总销售额',
            ROUND(SUM(s.net_commission), 2) as '总佣金',
            ROUND(SUM(s.sales_total), 2) as '销售合计',
            ROUND(SUM(s.wfs_shipping_refund), 2) as 'WFS运输退款'
        FROM statement_headers h
        LEFT JOIN sales_details s ON h.id = s.header_id
        WHERE s.id IS NOT NULL
        GROUP BY h.statement_period
        ORDER BY h.statement_period;
        """
    )
    
    # 查询 4: 退款明细
    print_section("4. 退款明细汇总")
    
    execute_query(
        "退款总额和折扣统计",
        """
        SELECT 
            h.statement_period as '时间段',
            ROUND(SUM(r.commission), 2) as '退款佣金',
            ROUND(SUM(r.refund_total), 2) as '退款总额',
            ROUND(SUM(r.wfs_total_discount), 2) as 'WFS折扣'
        FROM statement_headers h
        LEFT JOIN refund_details r ON h.id = r.header_id
        WHERE r.id IS NOT NULL
        GROUP BY h.statement_period
        ORDER BY h.statement_period;
        """
    )
    
    # 查询 5: 活动与调整
    print_section("5. 其他活动与调整")
    
    execute_query(
        "广告费和调整费用",
        """
        SELECT 
            h.statement_period as '时间段',
            ROUND(SUM(oa.walmart_product_advertising), 2) as '广告费',
            COUNT(DISTINCT aj.id) as '调整笔数'
        FROM statement_headers h
        LEFT JOIN other_activities oa ON h.id = oa.header_id
        LEFT JOIN adjustments aj ON h.id = aj.header_id
        GROUP BY h.statement_period
        ORDER BY h.statement_period;
        """
    )
    
    # 查询 6: 完整语句视图
    print_section("6. 完整语句（联接所有表）")
    
    execute_query(
        "样本 PDF 的完整数据",
        """
        SELECT 
            h.source_pdf_name as 'PDF文件',
            h.statement_period as '时间段',
            ROUND(h.payment_to_you, 2) as '应付',
            ROUND(s.sales_total, 2) as '销售',
            ROUND(r.refund_total, 2) as '退款',
            ROUND(oa.walmart_product_advertising, 2) as '广告'
        FROM statement_complete
        WHERE statement_id IN (
            SELECT id FROM statement_headers LIMIT 3
        );
        """
    )
    
    # 查询 7: 板块元数据
    print_section("7. 板块元数据（审计信息）")
    
    execute_query(
        "每个 PDF 的板块统计",
        """
        SELECT 
            h.source_pdf_name as 'PDF文件',
            sm.section_name as '板块',
            sm.field_count as '字段数',
            sm.detail_count as '明细数'
        FROM statement_headers h
        LEFT JOIN section_metadata sm ON h.id = sm.header_id
        ORDER BY h.source_pdf_name, sm.section_name
        LIMIT 10;
        """
    )
    
    # 查询 8: 数据验证
    print_section("8. 数据验证")
    
    print("✓ 外键约束检查")
    conn = sqlite3.connect(str(DB_PATH))
    
    # 检查孤立记录
    cursor = conn.execute(
        "SELECT COUNT(*) as orphaned FROM sales_details WHERE header_id NOT IN (SELECT id FROM statement_headers)"
    )
    orphaned = cursor.fetchone()[0]
    print(f"  - sales_details 中的孤立记录: {orphaned} ✓\n")
    
    # 检查必有字段
    cursor = conn.execute(
        "SELECT COUNT(*) as null_count FROM statement_headers WHERE payment_to_you IS NULL OR opening_balance IS NULL"
    )
    null_count = cursor.fetchone()[0]
    print(f"✓ 必有字段非空检查")
    print(f"  - statement_headers 中的 NULL 值: {null_count} ✓\n")
    
    # 检查负数
    cursor = conn.execute(
        "SELECT COUNT(*) as negative FROM sales_details WHERE product_price < 0 OR sales_total < 0"
    )
    negative = cursor.fetchone()[0]
    print(f"✓ 数值范围检查")
    print(f"  - sales_details 中的负数: {negative} ✓\n")
    
    conn.close()
    
    # 查询 9: 索引信息
    print_section("9. 索引信息")
    
    execute_query(
        "已创建的索引",
        """
        SELECT 
            name as '索引名',
            tbl_name as '表名'
        FROM sqlite_master
        WHERE type='index' AND name LIKE 'idx_%'
        ORDER BY tbl_name, name;
        """
    )
    
    # 查询 10: 配置表
    print_section("10. 数据库配置")
    
    execute_query(
        "配置信息",
        """
        SELECT 
            key as '配置项',
            value as '值'
        FROM db_config
        ORDER BY key;
        """
    )
    
    print("\n" + "="*80)
    print("  查询演示完成！")
    print("="*80 + "\n")
    
    print("💡 提示:")
    print("  - 使用 'sqlite3 backend/data/walmart_pdf_parser.db' 进入交互模式")
    print("  - 所有查询都可以在数据库管理工具中使用")
    print("  - JSON 字段中存储了低频字段（频率 = 1）的数据")
    print()

if __name__ == '__main__':
    main()
