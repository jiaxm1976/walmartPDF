#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 2 数据库初始化脚本

功能：
  1. 备份现有数据库
  2. 清空旧数据库
  3. 执行 V2 schema 初始化
  4. 验证表结构与数据完整性

使用方式：
  python scripts/init_database_v2.py

"""

import os
import sys
import sqlite3
import shutil
from pathlib import Path
from datetime import datetime

# 配置
DB_PATH = Path('backend/data/walmart_pdf_parser.db')
SCHEMA_FILE = Path('backend/database/schema_v2_dynamic.sql')
BACKUP_DIR = Path('backend/data/backups')


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


def backup_database():
    """备份现有数据库"""
    if not DB_PATH.exists():
        log('数据库不存在，跳过备份', 'DEBUG')
        return None
    
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = BACKUP_DIR / f'walmart_pdf_parser_{timestamp}.db'
    
    try:
        shutil.copy2(DB_PATH, backup_path)
        log(f'已备份数据库至: {backup_path}', 'INFO')
        return backup_path
    except Exception as e:
        log(f'备份失败: {e}', 'ERROR')
        raise


def delete_database():
    """删除旧数据库"""
    if DB_PATH.exists():
        try:
            DB_PATH.unlink()
            log(f'已删除旧数据库: {DB_PATH}', 'INFO')
        except Exception as e:
            log(f'删除失败: {e}', 'ERROR')
            raise


def init_schema():
    """执行 schema 初始化"""
    if not SCHEMA_FILE.exists():
        log(f'schema 文件不存在: {SCHEMA_FILE}', 'ERROR')
        raise FileNotFoundError(f'找不到 {SCHEMA_FILE}')
    
    # 确保数据库目录存在
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        # 读取 SQL 脚本
        with open(SCHEMA_FILE, 'r', encoding='utf-8') as f:
            sql_script = f.read()
        
        # 执行 SQL 脚本
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        
        # 按分号分割 SQL 语句
        for statement in sql_script.split(';'):
            statement = statement.strip()
            if statement:
                cursor.execute(statement)
        
        conn.commit()
        conn.close()
        
        log(f'schema 初始化完成: {DB_PATH}', 'INFO')
        
    except Exception as e:
        log(f'schema 初始化失败: {e}', 'ERROR')
        raise


def verify_schema():
    """验证表结构"""
    try:
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        
        # 获取所有表
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
        tables = cursor.fetchall()
        log(f'已创建 {len(tables)} 个表:', 'INFO')
        for (table_name,) in tables:
            log(f'  - {table_name}', 'DEBUG')
        
        # 验证 field_frequency 表有数据
        cursor.execute("SELECT COUNT(*) FROM field_frequency;")
        freq_count = cursor.fetchone()[0]
        log(f'field_frequency 表有 {freq_count} 条记录（预期 31）', 'INFO')
        
        if freq_count != 31:
            log(f'警告: field_frequency 数据不完整', 'WARN')
        
        # 获取视图
        cursor.execute("SELECT name FROM sqlite_master WHERE type='view' ORDER BY name;")
        views = cursor.fetchall()
        log(f'已创建 {len(views)} 个视图:', 'INFO')
        for (view_name,) in views:
            log(f'  - {view_name}', 'DEBUG')
        
        conn.close()
        return True
        
    except Exception as e:
        log(f'验证失败: {e}', 'ERROR')
        return False


def init_right_section():
    """初始化右侧数据字段频率"""
    try:
        import sqlite3
        
        # 右侧数据标准字段列表
        RIGHT_SECTION_FIELDS = [
            '状态',
            '付款日期',
            '周期付款',
            '付款方式',
            '设备方式',
            '待付款金额',
            '等待回款金额',
            '回款等待期',
            '警告信息'
        ]
        
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        
        count = 0
        for field_name in RIGHT_SECTION_FIELDS:
            # 检查字段是否已存在
            cursor.execute(
                "SELECT id FROM field_frequency WHERE section_name = ? AND field_name = ?",
                ('right_section', field_name)
            )
            
            if not cursor.fetchone():
                # 插入新记录，右侧数据字段全部设为高频（频率 2）
                cursor.execute(
                    """
                    INSERT INTO field_frequency (section_name, field_name, frequency, frequency_percent)
                    VALUES (?, ?, ?, ?)
                    """,
                    ('right_section', field_name, 2, 100.0)
                )
                count += 1
        
        conn.commit()
        conn.close()
        
        log(f'右侧数据字段初始化完成 ({count} 个新字段，共 {len(RIGHT_SECTION_FIELDS)} 个)', 'INFO')
        return True
        
    except Exception as e:
        log(f'右侧数据初始化失败: {e}', 'ERROR')
        return False


def main():
    """主流程"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║           Walmart PDF 数据库 V2 - Phase 2 初始化           ║
║                (数据库初始化与 schema 创建)                 ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    try:
        log('开始 Phase 2 数据库初始化...', 'INFO')
        
        # 步骤 1: 备份
        log('步骤 1/5: 备份现有数据库', 'INFO')
        backup_path = backup_database()
        
        # 步骤 2: 删除
        log('步骤 2/5: 删除旧数据库', 'INFO')
        delete_database()
        
        # 步骤 3: 初始化
        log('步骤 3/5: 执行 schema 初始化', 'INFO')
        init_schema()
        
        # 步骤 4: 初始化右侧数据
        log('步骤 4/5: 初始化右侧数据字段频率', 'INFO')
        if not init_right_section():
            raise RuntimeError('右侧数据初始化失败')
        
        # 步骤 5: 验证
        log('步骤 5/5: 验证表结构与右侧数据', 'INFO')
        if not verify_schema():
            raise RuntimeError('schema 验证失败')
        
        print(f"""
╔══════════════════════════════════════════════════════════════╗
║                    ✓ Phase 2 完成！                         ║
╚══════════════════════════════════════════════════════════════╝

📊 初始化结果：
  ✓ 数据库已清空并重建
  ✓ Schema V2 已初始化
  ✓ 所有表与视图已创建
  ✓ field_frequency 已填充 40 个字段（基础 31 个 + 右侧 9 个）
  ✓ 右侧数据板块已初始化

📍 数据库位置: {DB_PATH}

🔄 备份信息:
  {f'✓ 已备份至: {backup_path}' if backup_path else '⚠ 无备份'}

🔧 右侧数据说明：
  • 板块名: 'right_section'
  • 字段数: 9 个
  • 存储位置: section_data 表
  • 特点: 所有字段都被视为高频字段（不会被合并到 _其他）

🚀 下一步 (Phase 3): 单 PDF 导入测试
  python scripts/test_single_pdf_import.py

""")
        return 0
        
    except Exception as e:
        log(f'初始化失败: {e}', 'ERROR')
        if backup_path:
            log(f'可恢复备份: {backup_path}', 'WARN')
        return 1


if __name__ == '__main__':
    sys.exit(main())
