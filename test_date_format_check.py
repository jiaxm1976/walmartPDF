#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日期格式处理测试脚本
验证新日期格式 "Sep 6, 2025 - Sep 20, 2025" 是否被正确处理
"""

import sys
from pathlib import Path
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from backend.database.structured_importer import StructuredDataImporter

def test_date_format():
    """测试日期格式解析"""
    
    importer = StructuredDataImporter()
    
    # 测试用例集合
    test_cases = [
        # (输入, 预期输出, 说明)
        ("Sep 6, 2025 - Sep 20, 2025", "2025-09-06 - 2025-09-20", "新格式：短月份"),
        ("September 6, 2025 - September 20, 2025", "2025-09-06 - 2025-09-20", "新格式：完整月份"),
        ("Oct 1, 2024 - Oct 31, 2024", "2024-10-01 - 2024-10-31", "新格式：十月"),
        ("Dec 1, 2024 - Dec 31, 2024", "2024-12-01 - 2024-12-31", "新格式：十二月"),
        
        # 中文格式
        ("2024年10月8日 - 2024年11月10日", "2024-10-08 - 2024-11-10", "中文格式"),
        
        # 斜杠格式
        ("2024/10/08 - 2024/11/10", "2024-10-08 - 2024-11-10", "斜杠格式"),
        
        # ISO 格式
        ("2024-10-08 - 2024-11-10", "2024-10-08 - 2024-11-10", "ISO 格式"),
        
        # 带时区后缀（可能出现）
        ("Sep 6, 2025 UTC - Sep 20, 2025 UTC", "2025-09-06 - 2025-09-20", "新格式：带时区"),
    ]
    
    print("=" * 80)
    print("📅 日期格式处理测试")
    print("=" * 80)
    
    passed = 0
    failed = 0
    
    for input_val, expected, description in test_cases:
        try:
            result = importer._normalize_period(input_val)
            status = "✅ PASS" if result == expected else "❌ FAIL"
            
            if result == expected:
                passed += 1
            else:
                failed += 1
            
            print(f"\n{status} {description}")
            print(f"  输入:   {input_val}")
            print(f"  预期:   {expected}")
            print(f"  实际:   {result}")
            
        except Exception as e:
            failed += 1
            print(f"\n❌ FAIL {description}")
            print(f"  输入:   {input_val}")
            print(f"  错误:   {e}")
    
    print("\n" + "=" * 80)
    print(f"📊 测试结果: {passed} 通过，{failed} 失败（共 {len(test_cases)} 个）")
    print("=" * 80)
    
    return failed == 0


if __name__ == "__main__":
    success = test_date_format()
    sys.exit(0 if success else 1)
