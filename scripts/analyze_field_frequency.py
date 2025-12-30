#!/usr/bin/env python3
# ============================================================
# 文件: scripts/analyze_field_frequency.py
# 功能: 分析PDF解析结果中各板块字段的出现频率
# 作者: 开发团队
# 创建时间: 2025-12-19
# ============================================================

import json
import sys
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Tuple

# 添加项目路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def analyze_field_frequency(output_dir: Path) -> Dict[str, Dict[str, int]]:
    """分析字段出现频率.

    Args:
        output_dir: 解析结果JSON文件目录

    Returns:
        Dict[板块名, Dict[字段名, 出现次数]]
    """
    # 统计数据结构
    field_stats = defaultdict(lambda: defaultdict(int))
    pdf_count = 0

    # 遍历所有JSON文件
    json_files = list(output_dir.glob("parsed_*.json"))

    for json_file in json_files:
        pdf_count += 1
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # 只分析成功的解析结果
        if not data.get('success'):
            continue

        left_section = data.get('data', {}).get('left_section', {})
        right_section = data.get('data', {}).get('right_section', {})

        # 统计左侧板块字段
        for section_name, section_data in left_section.items():
            if isinstance(section_data, dict):
                for field_name in section_data.keys():
                    field_stats[section_name][field_name] += 1

        # 统计右侧板块字段
        for section_name, section_data in right_section.items():
            if isinstance(section_data, dict):
                for field_name in section_data.keys():
                    field_stats[section_name][field_name] += 1

    return dict(field_stats), pdf_count


def categorize_fields(field_stats: Dict[str, Dict[str, int]],
                      pdf_count: int,
                      threshold_ratio: float = 0.5) -> Tuple[Dict, Dict]:
    """将字段分类为核心字段和低频字段.

    Args:
        field_stats: 字段统计数据
        pdf_count: PDF总数
        threshold_ratio: 频率阈值（低于此比例的为低频字段）

    Returns:
        (核心字段字典, 低频字段字典)
    """
    core_fields = defaultdict(list)
    rare_fields = defaultdict(list)

    threshold_count = pdf_count * threshold_ratio

    for section_name, fields in field_stats.items():
        for field_name, count in fields.items():
            field_info = {
                'name': field_name,
                'count': count,
                'ratio': count / pdf_count,
                'percentage': f"{count / pdf_count * 100:.1f}%"
            }

            if count >= threshold_count:
                core_fields[section_name].append(field_info)
            else:
                rare_fields[section_name].append(field_info)

    return dict(core_fields), dict(rare_fields)


def print_analysis_report(field_stats: Dict[str, Dict[str, int]],
                         pdf_count: int,
                         threshold_ratio: float = 0.5):
    """打印分析报告."""

    print("=" * 80)
    print("PDF字段频率分析报告")
    print("=" * 80)
    print(f"分析PDF数量: {pdf_count} 个")
    print(f"频率阈值: {threshold_ratio * 100}% (出现次数 >= {int(pdf_count * threshold_ratio)})")
    print()

    core_fields, rare_fields = categorize_fields(field_stats, pdf_count, threshold_ratio)

    # 按板块打印分析结果
    section_order = ['header', 'sales', 'refund', 'adjustment', 'wfs',
                     'other', 'footer', 'payment_details']

    for section_name in section_order:
        if section_name not in field_stats:
            continue

        print("=" * 80)
        print(f"📋 板块: {section_name}")
        print("=" * 80)

        # 打印核心字段
        if section_name in core_fields:
            print(f"\n✅ 核心字段（高频 >= {threshold_ratio * 100}%）- 建议独立存储:")
            print("-" * 80)
            for field in sorted(core_fields[section_name],
                              key=lambda x: x['count'], reverse=True):
                print(f"  • {field['name']:40} | 出现: {field['count']}/{pdf_count} ({field['percentage']})")

        # 打印低频字段
        if section_name in rare_fields:
            print(f"\n⚠️  低频字段（< {threshold_ratio * 100}%）- 建议合并到'其他'字段:")
            print("-" * 80)
            for field in sorted(rare_fields[section_name],
                              key=lambda x: x['count'], reverse=True):
                print(f"  • {field['name']:40} | 出现: {field['count']}/{pdf_count} ({field['percentage']})")

        print()

    # 打印建议
    print("=" * 80)
    print("💡 优化建议")
    print("=" * 80)
    print()
    print("1. 【核心字段】- 创建独立数据库列")
    print("   - 出现频率 >= 50% 的字段")
    print("   - 需要进行查询、统计、分析的字段")
    print()
    print("2. 【低频字段】- 存储到dynamic_fields表或JSON字段")
    print("   - 出现频率 < 50% 的字段")
    print("   - 不规则字段、偶尔出现的字段")
    print()
    print("3. 【数据库设计原则】")
    print("   - 避免过多NULL值列（降低存储效率）")
    print("   - 保持表结构简洁（提高查询性能）")
    print("   - 使用扩展表存储动态字段（保持灵活性）")
    print()
    print("=" * 80)


def compare_with_current_schema(core_fields: Dict[str, List],
                                field_stats: Dict[str, Dict[str, int]],
                                pdf_count: int):
    """对比当前数据库schema和实际数据."""

    print("=" * 80)
    print("🔍 当前Schema对比分析")
    print("=" * 80)
    print()

    # 读取当前的models.py，分析已定义的字段
    models_path = PROJECT_ROOT / "backend" / "database" / "models.py"

    # 这里简化处理，直接列出当前schema的核心字段
    current_schema = {
        'header': [
            'start_date', 'end_date', 'opening_balance',
            'reserve_funds', 'awaiting_payment'
        ],
        'sales': [
            'product_price', 'shipping', 'wfs_shipping_refund',
            'net_tax_collected', 'other_tax_fees', 'net_commission',
            'withholding_tax', 'wfs_shipping_tax_refund',
            'walmart_funded_savings', 'total'
        ],
        'refund': [
            'product_price', 'shipping', 'net_tax_collected',
            'commission', 'withholding_tax', 'walmart_funded_savings', 'total'
        ],
        'adjustment': [
            'return_shipping_fee', 'global_shipping_label_fee', 'total'
        ],
        'wfs': [
            'wfs_fee', 'wfs_return_fee', 'wfs_disposal_fee',
            'wfs_adjustment', 'wfs_rc_inventory_fee', 'total'
        ],
        'other': [
            'walmart_product_ads', 'total'
        ],
        'footer': [
            'amount_paid_to_you', 'closing_balance', 'savings', 'cost_savings'
        ],
        'payment_details': [
            'status', 'payment_date', 'payment_frequency', 'payment_method',
            'device_method', 'amount_to_be_paid', 'amount_waiting_return',
            'return_waiting_period', 'warning_message'
        ]
    }

    # 字段名映射（PDF字段 -> 数据库字段）
    field_mapping = {
        'header': {
            '开始日期': 'start_date',
            '结束日期': 'end_date',
            '期初余额': 'opening_balance',
            '备用金': 'reserve_funds',
            '回款等待': 'awaiting_payment'
        },
        'sales': {
            '产品价格': 'product_price',
            '运输': 'shipping',
            'WFS运输退款': 'wfs_shipping_refund',
            '已收税净额': 'net_tax_collected',
            '其他税款（费用）': 'other_tax_fees',
            '净佣金': 'net_commission',
            '扣缴税款净额': 'withholding_tax',
            'WFS 运输税退款': 'wfs_shipping_tax_refund',
            'WFS运输税退款': 'wfs_shipping_tax_refund',
            'T沃尔玛出资的节余': 'walmart_funded_savings',
            'T沃尔玛出资的节余总额': 'walmart_funded_savings',
            '总计': 'total',
            '总计：': 'total'
        }
    }

    for section_name, fields_dict in field_stats.items():
        if section_name not in current_schema:
            continue

        print(f"📋 {section_name} 板块")
        print("-" * 80)

        # 获取实际出现的字段
        actual_fields = list(fields_dict.keys())
        schema_fields = current_schema[section_name]

        # 映射字段名
        mapped_fields = []
        unmapped_fields = []

        for field in actual_fields:
            if section_name in field_mapping and field in field_mapping[section_name]:
                mapped_fields.append(field_mapping[section_name][field])
            else:
                unmapped_fields.append(field)

        # 检查缺失字段
        missing_in_actual = set(schema_fields) - set(mapped_fields)
        extra_in_actual = unmapped_fields

        print(f"  Schema定义字段: {len(schema_fields)} 个")
        print(f"  实际出现字段: {len(actual_fields)} 个")

        if missing_in_actual:
            print(f"\n  ⚠️  Schema中有但实际未出现的字段:")
            for field in missing_in_actual:
                print(f"     - {field}")

        if extra_in_actual:
            print(f"\n  ℹ️  实际出现但Schema中未定义的字段:")
            for field in extra_in_actual:
                count = fields_dict[field]
                ratio = count / pdf_count
                print(f"     - {field:40} ({count}/{pdf_count}, {ratio*100:.1f}%)")

        print()


if __name__ == "__main__":
    # 输出目录
    output_dir = PROJECT_ROOT / "backend" / "tests" / "output"

    if not output_dir.exists():
        print(f"❌ 输出目录不存在: {output_dir}")
        sys.exit(1)

    # 分析字段频率
    field_stats, pdf_count = analyze_field_frequency(output_dir)

    if pdf_count == 0:
        print("❌ 未找到任何解析结果JSON文件")
        sys.exit(1)

    # 打印分析报告（使用不同阈值）
    print("\n")
    print_analysis_report(field_stats, pdf_count, threshold_ratio=0.5)

    print("\n\n")
    print("=" * 80)
    print("🔄 尝试不同阈值的分析")
    print("=" * 80)
    print()

    for threshold in [0.3, 0.5, 0.7]:
        core_fields, rare_fields = categorize_fields(field_stats, pdf_count, threshold)
        print(f"阈值 {threshold*100}%: ", end="")
        total_core = sum(len(fields) for fields in core_fields.values())
        total_rare = sum(len(fields) for fields in rare_fields.values())
        print(f"核心字段 {total_core} 个, 低频字段 {total_rare} 个")

    print()

    # 对比当前schema
    core_fields, _ = categorize_fields(field_stats, pdf_count, 0.5)
    compare_with_current_schema(core_fields, field_stats, pdf_count)


# ============================================================
# END OF analyze_field_frequency.py
# ============================================================
