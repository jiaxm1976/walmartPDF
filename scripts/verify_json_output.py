#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JSON输出验证脚本 - 结构化展示提取的数据.

功能：
1. 读取JSON文件
2. 对照原始板块图片
3. 结构化展示数据便于核对

使用方法：
    python scripts/verify_json_output.py test_output/step5/MP_01142025_left_data.json
"""

import sys
import json
from pathlib import Path

def verify_json_output(json_path: str):
    """结构化验证JSON输出."""

    # 读取JSON
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    print("=" * 80)
    print("JSON数据结构化验证")
    print("=" * 80)
    print()

    # Header板块
    if 'header' in data:
        print("【1. 头部信息 (Header)】")
        print("-" * 60)
        header = data['header']
        if '开始日期' in header:
            print(f"  对账单期间: {header['开始日期']} ~ {header.get('结束日期', '')}")
        print(f"  期初余额:    {header.get('期初余额', 'N/A')} 美元")
        print(f"  备用金:      {header.get('备用金', 'N/A')} 美元")
        print(f"  回款等待:    {header.get('回款等待', 'N/A')} 美元")
        print()

    # Sales板块
    if 'sales' in data:
        print("【2. 销售 (Sales)】")
        print("-" * 60)
        sales = data['sales']
        for key, value in sales.items():
            # 识别总计（包括带冒号和不带冒号）
            if key in ['总计', '总计:', '总计：']:
                print(f"  {'':20s} {'─' * 20}")
                print(f"  总计{' ' * 16} {value:>15s} 美元 ★")
            else:
                print(f"  {key:20s} {value:>15s} 美元")
        print()

    # Refund板块
    if 'refund' in data:
        print("【3. 退款 (Refund)】")
        print("-" * 60)
        refund = data['refund']
        has_total = False
        for key, value in refund.items():
            if key in ['总计', '总计:', '总计：']:
                print(f"  {'':20s} {'─' * 20}")
                print(f"  总计{' ' * 16} {value:>15s} 美元 ★")
                has_total = True
            else:
                print(f"  {key:20s} {value:>15s} 美元")
        if not has_total:
            print(f"  ⚠️  警告: 缺少【总计】字段")
        print()

    # Adjustment板块
    if 'adjustment' in data:
        print("【4. 调整 (Adjustment)】")
        print("-" * 60)
        adjustment = data['adjustment']
        has_total = False
        for key, value in adjustment.items():
            if key in ['总计', '总计:', '总计：']:
                print(f"  {'':20s} {'─' * 20}")
                print(f"  总计{' ' * 16} {value:>15s} 美元 ★")
                has_total = True
            else:
                print(f"  {key:20s} {value:>15s} 美元")
        if not has_total:
            print(f"  ⚠️  警告: 缺少【总计】字段")
        print()

    # WFS板块
    if 'wfs' in data:
        print("【5. 沃尔玛商品服务 (WFS)】")
        print("-" * 60)
        wfs = data['wfs']
        has_total = False
        for key, value in wfs.items():
            if key in ['总计', '总计:', '总计：']:
                print(f"  {'':20s} {'─' * 20}")
                print(f"  总计{' ' * 16} {value:>15s} 美元 ★")
                has_total = True
            else:
                print(f"  {key:20s} {value:>15s} 美元")
        if not has_total:
            print(f"  ⚠️  警告: 缺少【总计】字段")
        print()

    # Other板块
    if 'other' in data:
        print("【6. 其他活动 (Other)】")
        print("-" * 60)
        other = data['other']
        has_total = False
        for key, value in other.items():
            if key in ['总计', '总计:', '总计：']:
                print(f"  {'':20s} {'─' * 20}")
                print(f"  总计{' ' * 16} {value:>15s} 美元 ★")
                has_total = True
            else:
                print(f"  {key:20s} {value:>15s} 美元")
        if not has_total:
            print(f"  ⚠️  警告: 缺少【总计】字段")
        print()

    # Footer板块
    if 'footer' in data:
        print("【7. 尾部信息 (Footer)】")
        print("-" * 60)
        footer = data['footer']
        print(f"  向您支付的金额:  {footer.get('向您支付的金额', 'N/A')} 美元")
        print(f"  期末余额:        {footer.get('期末余额', 'N/A')} 美元")
        print()

    print("=" * 80)
    print("验证完成")
    print("=" * 80)
    print()
    print("说明：")
    print("  ★ = 板块总计")
    print("  ⚠️  = 缺少必需字段")
    print()


def main():
    """主函数."""
    if len(sys.argv) < 2:
        print("用法: python scripts/verify_json_output.py <JSON文件路径>")
        print("示例: python scripts/verify_json_output.py test_output/step5/MP_01142025_left_data.json")
        sys.exit(1)

    json_path = sys.argv[1]

    if not Path(json_path).exists():
        print(f"错误: 文件不存在: {json_path}")
        sys.exit(1)

    verify_json_output(json_path)


if __name__ == "__main__":
    main()
