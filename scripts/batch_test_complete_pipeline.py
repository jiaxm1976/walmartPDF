#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量测试所有PDF的完整流程 (Steps 1-6)
"""

import sys
import os
import logging
from pathlib import Path
import glob

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "backend"))

# 配置日志
logging.basicConfig(
    level=logging.WARNING,  # 只显示警告和错误信息
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 导入测试脚本
sys.path.insert(0, str(Path(__file__).parent))
from test_full_pipeline_complete import test_full_pipeline


def batch_test_all_pdfs(pdf_dir: str = "PdfData", output_base: str = "test_output_batch"):
    """批量测试所有PDF文件.

    Args:
        pdf_dir: PDF文件目录
        output_base: 批量测试输出根目录
    """
    print("=" * 80)
    print("批量测试所有PDF (Steps 1-6)")
    print("=" * 80)

    # 查找所有PDF文件
    pdf_pattern = os.path.join(pdf_dir, "MP_*.pdf")
    pdf_files = sorted(glob.glob(pdf_pattern))

    if not pdf_files:
        print(f"错误：未找到PDF文件 (模式: {pdf_pattern})")
        return

    print(f"\n找到 {len(pdf_files)} 个PDF文件：")
    for i, pdf_path in enumerate(pdf_files, 1):
        print(f"  {i}. {Path(pdf_path).name}")

    # 测试统计
    success_count = 0
    failure_count = 0
    results = []

    print("\n" + "=" * 80)
    print("开始批量测试...")
    print("=" * 80 + "\n")

    for i, pdf_path in enumerate(pdf_files, 1):
        pdf_name = Path(pdf_path).stem
        print(f"\n[{i}/{len(pdf_files)}] 测试: {pdf_name}")
        print("-" * 60)

        # 为每个PDF创建独立的输出目录
        pdf_output_dir = os.path.join(output_base, pdf_name)

        try:
            # 运行完整流水线测试
            test_full_pipeline(pdf_path, pdf_output_dir)

            # 检查输出文件是否存在
            complete_json = os.path.join(pdf_output_dir, "step7_final", f"{pdf_name}_complete_data.json")
            if os.path.exists(complete_json):
                success_count += 1
                print(f"✓ 成功: {pdf_name}")
                results.append({
                    "pdf": pdf_name,
                    "status": "success",
                    "json_path": complete_json
                })
            else:
                failure_count += 1
                print(f"✗ 失败: {pdf_name} (JSON未生成)")
                results.append({
                    "pdf": pdf_name,
                    "status": "failure",
                    "error": "JSON文件未生成"
                })

        except Exception as e:
            failure_count += 1
            error_msg = str(e)
            print(f"✗ 失败: {pdf_name}")
            print(f"  错误: {error_msg}")
            results.append({
                "pdf": pdf_name,
                "status": "failure",
                "error": error_msg
            })

    # 打印汇总报告
    print("\n" + "=" * 80)
    print("批量测试汇总报告")
    print("=" * 80)
    print(f"\n总计测试: {len(pdf_files)} 个PDF")
    print(f"  ✓ 成功: {success_count} 个 ({success_count/len(pdf_files)*100:.1f}%)")
    print(f"  ✗ 失败: {failure_count} 个 ({failure_count/len(pdf_files)*100:.1f}%)")

    print("\n详细结果：")
    print("-" * 80)
    for result in results:
        pdf = result['pdf']
        status = result['status']
        if status == "success":
            print(f"  ✓ {pdf}")
            print(f"     JSON: {result['json_path']}")
        else:
            print(f"  ✗ {pdf}")
            print(f"     错误: {result.get('error', '未知错误')}")

    print("\n" + "=" * 80)
    print(f"批量测试完成！输出目录: {output_base}")
    print("=" * 80)

    # 保存汇总报告到文件
    report_path = os.path.join(output_base, "batch_test_report.txt")
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("批量测试汇总报告\n")
        f.write("=" * 80 + "\n\n")
        f.write(f"总计测试: {len(pdf_files)} 个PDF\n")
        f.write(f"  ✓ 成功: {success_count} 个 ({success_count/len(pdf_files)*100:.1f}%)\n")
        f.write(f"  ✗ 失败: {failure_count} 个 ({failure_count/len(pdf_files)*100:.1f}%)\n\n")
        f.write("详细结果：\n")
        f.write("-" * 80 + "\n")
        for result in results:
            pdf = result['pdf']
            status = result['status']
            if status == "success":
                f.write(f"  ✓ {pdf}\n")
                f.write(f"     JSON: {result['json_path']}\n")
            else:
                f.write(f"  ✗ {pdf}\n")
                f.write(f"     错误: {result.get('error', '未知错误')}\n")

    print(f"\n汇总报告已保存: {report_path}")


if __name__ == "__main__":
    pdf_dir = "PdfData"
    output_base = "test_output_batch"

    if len(sys.argv) > 1:
        pdf_dir = sys.argv[1]
    if len(sys.argv) > 2:
        output_base = sys.argv[2]

    batch_test_all_pdfs(pdf_dir, output_base)
