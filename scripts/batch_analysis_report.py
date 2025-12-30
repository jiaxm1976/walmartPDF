#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量PDF测试汇总报告生成脚本.

功能：
1. 读取所有JSON文件
2. 统计"总计"字段识别情况
3. 生成详细的对比分析报告

使用方法：
    python scripts/batch_analysis_report.py test_output_grayscale/step5
"""

import sys
import json
from pathlib import Path
from collections import defaultdict


def analyze_json_file(json_path):
    """分析单个JSON文件.

    Returns:
        dict: 分析结果
            {
                'filename': 文件名,
                'sections': {section_name: has_total},
                'total_sections': 板块总数,
                'sections_with_total': 有总计的板块数,
                'success_rate': 成功率
            }
    """
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 统计板块和总计
    sections_info = {}
    for section_name, section_data in data.items():
        if section_name in ['header', 'footer']:
            continue

        # 检查是否有总计字段（支持多种格式）
        has_total = any(k in section_data for k in ['总计', '总计:', '总计：'])
        sections_info[section_name] = {
            'has_total': has_total,
            'field_count': len(section_data)
        }

    total_sections = len(sections_info)
    sections_with_total = sum(1 for s in sections_info.values() if s['has_total'])
    success_rate = (sections_with_total / total_sections * 100) if total_sections > 0 else 0

    return {
        'filename': Path(json_path).name,
        'pdf_name': Path(json_path).stem.replace('_statement_summary_left_data', ''),
        'sections': sections_info,
        'total_sections': total_sections,
        'sections_with_total': sections_with_total,
        'success_rate': success_rate
    }


def generate_batch_report(json_dir):
    """生成批量测试报告."""

    print("=" * 80)
    print("批量PDF测试汇总报告")
    print("=" * 80)
    print()

    # 收集所有JSON文件
    json_dir_path = Path(json_dir)
    json_files = sorted(json_dir_path.glob("*.json"))

    if not json_files:
        print(f"错误: 在 {json_dir} 中未找到JSON文件")
        return

    print(f"找到 {len(json_files)} 个JSON文件\n")

    # 分析每个文件
    all_results = []
    section_totals = defaultdict(lambda: {'count': 0, 'success': 0})

    for json_file in json_files:
        result = analyze_json_file(json_file)
        all_results.append(result)

        # 统计各板块总计
        for section_name, section_info in result['sections'].items():
            section_totals[section_name]['count'] += 1
            if section_info['has_total']:
                section_totals[section_name]['success'] += 1

    # 按成功率排序
    all_results_sorted = sorted(all_results, key=lambda x: x['success_rate'], reverse=True)

    # 打印详细结果
    print("【按PDF文件统计】")
    print("-" * 80)
    print(f"{'PDF文件':<20} {'板块数':<8} {'成功数':<8} {'成功率':<10} {'状态'}")
    print("-" * 80)

    for result in all_results_sorted:
        pdf_name = result['pdf_name']
        total = result['total_sections']
        success = result['sections_with_total']
        rate = result['success_rate']

        # 状态标记
        if rate == 100:
            status = "✅ 完美"
        elif rate >= 50:
            status = "⚠️  部分成功"
        else:
            status = "❌ 失败"

        print(f"{pdf_name:<20} {total:<8} {success:<8} {rate:>6.1f}%    {status}")

    print()

    # 打印按板块统计
    print("【按板块类型统计】")
    print("-" * 80)
    print(f"{'板块类型':<20} {'出现次数':<10} {'成功次数':<10} {'成功率'}")
    print("-" * 80)

    section_names = ['sales', 'refund', 'adjustment', 'wfs', 'other']
    for section_name in section_names:
        if section_name in section_totals:
            stats = section_totals[section_name]
            count = stats['count']
            success = stats['success']
            rate = (success / count * 100) if count > 0 else 0

            # 中文名称映射
            cn_names = {
                'sales': '销售',
                'refund': '退款',
                'adjustment': '调整',
                'wfs': '沃尔玛商品服务',
                'other': '其他活动'
            }
            display_name = cn_names.get(section_name, section_name)

            print(f"{display_name:<20} {count:<10} {success:<10} {rate:>6.1f}%")

    print()

    # 打印详细问题分析
    print("【详细问题分析】")
    print("-" * 80)

    for result in all_results_sorted:
        if result['success_rate'] < 100:
            print(f"\n{result['pdf_name']}:")
            for section_name, section_info in result['sections'].items():
                if not section_info['has_total']:
                    cn_names = {
                        'sales': '销售',
                        'refund': '退款',
                        'adjustment': '调整',
                        'wfs': '沃尔玛商品服务',
                        'other': '其他活动'
                    }
                    display_name = cn_names.get(section_name, section_name)
                    print(f"  ❌ {display_name} - 缺少总计字段 ({section_info['field_count']}个字段)")

    print()

    # 总体统计
    total_pdfs = len(all_results)
    perfect_pdfs = sum(1 for r in all_results if r['success_rate'] == 100)
    partial_pdfs = sum(1 for r in all_results if 0 < r['success_rate'] < 100)
    failed_pdfs = sum(1 for r in all_results if r['success_rate'] == 0)

    total_sections_all = sum(r['total_sections'] for r in all_results)
    total_success_all = sum(r['sections_with_total'] for r in all_results)
    overall_rate = (total_success_all / total_sections_all * 100) if total_sections_all > 0 else 0

    print("【总体统计】")
    print("-" * 80)
    print(f"测试PDF总数:     {total_pdfs}")
    print(f"  完美识别:      {perfect_pdfs} ({perfect_pdfs/total_pdfs*100:.1f}%)")
    print(f"  部分成功:      {partial_pdfs} ({partial_pdfs/total_pdfs*100:.1f}%)")
    print(f"  完全失败:      {failed_pdfs} ({failed_pdfs/total_pdfs*100:.1f}%)")
    print()
    print(f"板块总数:        {total_sections_all}")
    print(f"成功识别总计:    {total_success_all}")
    print(f"总体成功率:      {overall_rate:.1f}%")
    print()

    # 结论与建议
    print("【结论与建议】")
    print("-" * 80)

    if overall_rate >= 80:
        print("✅ 整体识别效果良好 (≥80%)")
    elif overall_rate >= 60:
        print("⚠️  识别效果中等 (60-80%)，建议优化")
    else:
        print("❌ 识别效果较差 (<60%)，需要重大改进")

    print()

    # 分析问题板块
    problem_sections = []
    for section_name, stats in section_totals.items():
        rate = (stats['success'] / stats['count'] * 100) if stats['count'] > 0 else 0
        if rate < 80:
            problem_sections.append((section_name, rate, stats))

    if problem_sections:
        print("问题板块：")
        for section_name, rate, stats in problem_sections:
            cn_names = {
                'sales': '销售',
                'refund': '退款',
                'adjustment': '调整',
                'wfs': '沃尔玛商品服务',
                'other': '其他活动'
            }
            display_name = cn_names.get(section_name, section_name)
            print(f"  - {display_name}: {stats['success']}/{stats['count']} ({rate:.1f}%)")

    print()
    print("建议措施：")

    if problem_sections:
        print("  1. 针对问题板块实施方案A（智能后处理）")
        print("  2. 调整Y_THRESHOLD阈值，提高文本行合并准确率")
        print("  3. 增强对负数金额的OCR识别")
    else:
        print("  1. 当前配置已优化，继续使用80px+300DPI+灰度方案")
        print("  2. 可以进入下一步：实现右侧图片识别（Step 6）")

    print()
    print("=" * 80)
    print("报告生成完成")
    print("=" * 80)


def main():
    """主函数."""
    if len(sys.argv) < 2:
        print("用法: python scripts/batch_analysis_report.py <JSON目录>")
        print("示例: python scripts/batch_analysis_report.py test_output_grayscale/step5")
        sys.exit(1)

    json_dir = sys.argv[1]

    if not Path(json_dir).exists():
        print(f"错误: 目录不存在: {json_dir}")
        sys.exit(1)

    generate_batch_report(json_dir)


if __name__ == "__main__":
    main()
