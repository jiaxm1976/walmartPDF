#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 5 查询验证脚本

功能：
  1. 验证 4 种常见查询模式
  2. 输出查询结果
  3. 验证数据完整性

查询模式：
  1. 获取单 PDF 的完整数据
  2. 按板块聚合字段
  3. 对比退款率
  4. 检查低频字段

使用方式：
  python scripts/verify_queries.py

前置条件：
  - Phase 4 已完成（所有 PDF 已导入）

"""

import sys
import json
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))


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


class QueryVerifier:
    """查询验证器"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = None
        self.cursor = None
    
    def connect(self):
        """连接数据库"""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
        log(f'已连接数据库: {self.db_path}', 'INFO')
    
    def disconnect(self):
        """断开连接"""
        if self.conn:
            self.conn.close()
    
    def query_1_single_pdf(self):
        """查询 1: 获取单 PDF 的完整数据"""
        print('\n' + '='*60)
        print('查询 1: 获取单 PDF 的完整数据')
        print('='*60)
        
        try:
            # 获取第一个 PDF
            self.cursor.execute("SELECT id, pdf_name FROM statements LIMIT 1;")
            result = self.cursor.fetchone()
            
            if not result:
                log('没有找到 statement 记录', 'WARN')
                return False
            
            statement_id, pdf_name = result['id'], result['pdf_name']
            log(f'已选择: {pdf_name} (statement_id={statement_id})', 'INFO')
            
            # 查询 statement 记录
            self.cursor.execute("""
                SELECT * FROM statements WHERE id = ?
            """, (statement_id,))
            statement = self.cursor.fetchone()
            
            print(f'\n📄 Statement 记录:')
            print(f'  ID: {statement["id"]}')
            print(f'  PDF 名: {statement["pdf_name"]}')
            print(f'  统计区间: {statement["statement_period"]}')
            print(f'  应付金额: {statement["payment_to_you"]}')
            
            # 查询 section_data 记录
            self.cursor.execute("""
                SELECT id, section_name, json_keys(data) as keys_count
                FROM section_data 
                WHERE statement_id = ?
                ORDER BY section_name
            """, (statement_id,))
            
            print(f'\n📊 板块数据:')
            for section in self.cursor.fetchall():
                print(f'  • {section["section_name"]}: {section["id"]}')
            
            log('✓ 查询 1 完成', 'INFO')
            return True
            
        except Exception as e:
            log(f'查询 1 失败: {e}', 'ERROR')
            return False
    
    def query_2_aggregate_by_section(self):
        """查询 2: 按板块统计"""
        print('\n' + '='*60)
        print('查询 2: 按板块统计记录')
        print('='*60)
        
        try:
            self.cursor.execute("""
                SELECT section_name, COUNT(*) as record_count
                FROM section_data
                GROUP BY section_name
                ORDER BY record_count DESC
            """)
            
            results = self.cursor.fetchall()
            
            if not results:
                log('没有找到 section_data 记录', 'WARN')
                return False
            
            print(f'\n📊 板块分布:')
            total = sum(r['record_count'] for r in results)
            for result in results:
                section_name = result['section_name']
                count = result['record_count']
                percentage = f'{count/total*100:.1f}%'
                print(f'  • {section_name}: {count} ({percentage})')
            
            print(f'\n  总计: {total} 条记录')
            
            log('✓ 查询 2 完成', 'INFO')
            return True
            
        except Exception as e:
            log(f'查询 2 失败: {e}', 'ERROR')
            return False
    
    def query_3_field_extraction(self):
        """查询 3: 提取关键字段"""
        print('\n' + '='*60)
        print('查询 3: 提取关键字段（产品价格）')
        print('='*60)
        
        try:
            self.cursor.execute("""
                SELECT 
                  s.pdf_name,
                  sd.section_name,
                  json_extract(sd.data, '$.产品价格') as 产品价格
                FROM statements s
                LEFT JOIN section_data sd ON s.id = sd.statement_id
                WHERE sd.section_name IN ('销售', '退款')
                ORDER BY s.pdf_name, sd.section_name
                LIMIT 10
            """)
            
            results = self.cursor.fetchall()
            
            if not results:
                log('没有找到相关数据', 'WARN')
                return False
            
            print(f'\n💰 产品价格提取:')
            for result in results:
                pdf_name = result['pdf_name']
                section_name = result['section_name']
                price = result['产品价格']
                print(f'  • {pdf_name} - {section_name}: {price}')
            
            log('✓ 查询 3 完成', 'INFO')
            return True
            
        except Exception as e:
            log(f'查询 3 失败: {e}', 'ERROR')
            return False
    
    def query_4_other_fields(self):
        """查询 4: 检查低频字段合并"""
        print('\n' + '='*60)
        print('查询 4: 检查低频字段合并')
        print('='*60)
        
        try:
            self.cursor.execute("""
                SELECT 
                  section_name,
                  COUNT(*) as total_records,
                  SUM(CASE WHEN json_extract(data, '$.' || section_name || '_其他') IS NOT NULL THEN 1 ELSE 0 END) as with_other_fields
                FROM section_data
                GROUP BY section_name
                ORDER BY with_other_fields DESC
            """)
            
            results = self.cursor.fetchall()
            
            print(f'\n📌 低频字段合并统计:')
            total_with_other = 0
            for result in results:
                section_name = result['section_name']
                total = result['total_records']
                with_other = result['with_other_fields'] or 0
                total_with_other += with_other
                percentage = f'{with_other/total*100:.1f}%' if total > 0 else 'N/A'
                print(f'  • {section_name}: {with_other}/{total} ({percentage})')
            
            # 显示低频字段示例
            self.cursor.execute("""
                SELECT 
                  section_name,
                  json_extract(data, '$.' || section_name || '_其他') as 其他字段
                FROM section_data
                WHERE json_extract(data, '$.' || section_name || '_其他') IS NOT NULL
                LIMIT 1
            """)
            
            result = self.cursor.fetchone()
            if result:
                section_name = result['section_name']
                other_fields = json.loads(result['其他字段'])
                print(f'\n📝 {section_name}_其他 字段示例:')
                for field_name, field_value in list(other_fields.items())[:5]:
                    print(f'  • {field_name}: {field_value}')
            
            log('✓ 查询 4 完成', 'INFO')
            return True
            
        except Exception as e:
            log(f'查询 4 失败: {e}', 'ERROR')
            return False
    
    def verify_data_integrity(self):
        """验证数据完整性"""
        print('\n' + '='*60)
        print('数据完整性检查')
        print('='*60)
        
        try:
            # 检查 statements 表
            self.cursor.execute("SELECT COUNT(*) FROM statements;")
            statement_count = self.cursor.fetchone()[0]
            
            # 检查 section_data 表
            self.cursor.execute("SELECT COUNT(*) FROM section_data;")
            section_data_count = self.cursor.fetchone()[0]
            
            # 检查孤立的 section_data（没有关联的 statement）
            self.cursor.execute("""
                SELECT COUNT(*) FROM section_data sd
                WHERE NOT EXISTS (SELECT 1 FROM statements s WHERE s.id = sd.statement_id)
            """)
            orphaned_count = self.cursor.fetchone()[0]
            
            # 检查 PDF 名唯一性
            self.cursor.execute("""
                SELECT COUNT(*) FROM (
                    SELECT pdf_name, COUNT(*) as count FROM statements GROUP BY pdf_name HAVING count > 1
                )
            """)
            duplicate_count = self.cursor.fetchone()[0]
            
            print(f'\n✅ 数据完整性检查:')
            print(f'  • statements 表: {statement_count} 条记录')
            print(f'  • section_data 表: {section_data_count} 条记录')
            print(f'  • 孤立 section_data: {orphaned_count} 条')
            print(f'  • 重复 PDF 名: {duplicate_count} 条')
            
            if orphaned_count == 0 and duplicate_count == 0:
                log('✓ 数据完整性检查通过', 'INFO')
                return True
            else:
                if orphaned_count > 0:
                    log(f'⚠️  发现 {orphaned_count} 条孤立 section_data', 'WARN')
                if duplicate_count > 0:
                    log(f'⚠️  发现 {duplicate_count} 个重复 PDF 名', 'WARN')
                return False
            
        except Exception as e:
            log(f'完整性检查失败: {e}', 'ERROR')
            return False


def main():
    """主流程"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║       Walmart PDF 数据库 V2 - Phase 5 查询验证           ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    db_path = 'backend/data/walmart_pdf_parser.db'
    
    if not Path(db_path).exists():
        log(f'数据库不存在: {db_path}', 'ERROR')
        return 1
    
    verifier = QueryVerifier(db_path)
    
    try:
        verifier.connect()
        
        # 执行查询
        results = [
            verifier.query_1_single_pdf(),
            verifier.query_2_aggregate_by_section(),
            verifier.query_3_field_extraction(),
            verifier.query_4_other_fields(),
            verifier.verify_data_integrity()
        ]
        
        verifier.disconnect()
        
        # 总结
        print(f"""
╔══════════════════════════════════════════════════════════════╗
║                    ✓ Phase 5 完成！                         ║
╚══════════════════════════════════════════════════════════════╝

📊 查询验证结果：
  {'✓ 所有查询验证通过！' if all(results) else '⚠️  部分查询失败'}

✨ 数据库设计 V2 已完全实施！

📋 下一步建议：
  1. 集成 StructuredDataImporter 到 PDF 处理流程
  2. 实施自动化测试
  3. 考虑添加更多查询优化

""")
        
        return 0 if all(results) else 1
        
    except Exception as e:
        log(f'验证失败: {e}', 'ERROR')
        return 1


if __name__ == '__main__':
    sys.exit(main())
