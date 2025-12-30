#!/usr/bin/env python3
# ============================================================
# 文件: scripts/test_parse_pipeline.py
# 功能: 测试完整的PDF解析流程（API集成）
# 作者: 开发团队
# 创建时间: 2025-12-18
# ============================================================

import sys
import requests
import json
import time
from pathlib import Path

BASE_URL = "http://localhost:8000/api/v1"


def test_complete_pipeline():
    """测试完整的PDF解析流程.

    流程:
    1. 上传PDF文件
    2. 触发解析
    3. 查询解析结果
    4. 验证数据
    """
    print("=" * 70)
    print("测试完整PDF解析流程（API集成）")
    print("=" * 70)
    print()

    # 1. 上传PDF
    print("步骤1: 上传PDF文件")
    print("-" * 70)

    pdf_path = Path(__file__).parent.parent / "PdfData" / "MP_01142025_statement_summary.pdf"

    if not pdf_path.exists():
        print(f"❌ PDF文件不存在: {pdf_path}")
        return

    with open(pdf_path, "rb") as f:
        files = {"file": (pdf_path.name, f, "application/pdf")}
        response = requests.post(f"{BASE_URL}/pdfs/upload", files=files)

    if response.status_code != 201:
        print(f"❌ 上传失败: {response.text}")
        return

    pdf_data = response.json()
    pdf_id = pdf_data["id"]

    print(f"✓ 上传成功")
    print(f"  PDF ID: {pdf_id}")
    print(f"  文件名: {pdf_data['filename']}")
    print(f"  状态: {pdf_data['process_status']}")
    print()

    # 2. 触发解析
    print("步骤2: 触发PDF解析")
    print("-" * 70)

    response = requests.post(f"{BASE_URL}/pdfs/{pdf_id}/parse")

    if response.status_code != 200:
        print(f"❌ 解析失败: {response.text}")
        return

    parsed_pdf = response.json()

    print(f"✓ 解析成功")
    print(f"  状态: {parsed_pdf['process_status']}")
    print(f"  处理时间: {parsed_pdf['process_time']}")
    print()

    # 3. 等待一秒（确保数据已写入）
    time.sleep(1)

    # 4. 查询解析结果
    print("步骤3: 查询解析结果")
    print("-" * 70)

    response = requests.get(f"{BASE_URL}/statements/{pdf_id}/data")

    if response.status_code != 200:
        print(f"❌ 查询失败: {response.text}")
        return

    data = response.json()

    print(f"✓ 查询成功")
    print()

    # 显示header数据
    if data.get("header"):
        print("【对账单头部】")
        header = data["header"]
        print(f"  开始日期: {header['start_date']}")
        print(f"  结束日期: {header['end_date']}")
        print(f"  期初余额: {header['opening_balance']}")
        print(f"  备用金: {header['reserve_funds']}")
        print(f"  回款等待: {header['awaiting_payment']}")
        print()

    # 显示sales数据
    if data.get("sales"):
        print("【销售明细】")
        sales = data["sales"]
        print(f"  产品价格: {sales['product_price']}")
        print(f"  运输: {sales['shipping']}")
        print(f"  净佣金: {sales['net_commission']}")
        print(f"  总计: {sales['total']}")
        print()

    # 显示refund数据
    if data.get("refund"):
        print("【退款明细】")
        refund = data["refund"]
        print(f"  产品价格: {refund['product_price']}")
        print(f"  运输: {refund['shipping']}")
        print(f"  总计: {refund['total']}")
        print()

    # 5. 验证数据
    print("步骤4: 验证数据完整性")
    print("-" * 70)

    response = requests.post(f"{BASE_URL}/statements/{pdf_id}/validate")

    if response.status_code == 200:
        result = response.json()
        print(f"✓ {result['message']}")
        if result.get("detail"):
            print(f"  详情: {result['detail']}")
    else:
        print(f"⚠️  验证失败: {response.text}")

    print()

    # 6. 保存完整JSON（用于检查）
    output_dir = Path(__file__).parent.parent / "test_output_api"
    output_dir.mkdir(exist_ok=True)
    output_file = output_dir / f"parsed_data_{pdf_id}.json"

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"完整数据已保存到: {output_file}")
    print()

    # 7. 测试数据修改
    print("步骤5: 测试数据修改")
    print("-" * 70)

    update_data = {
        "sales": {
            "product_price": "1500.00",
            "total": "1450.00"
        }
    }

    response = requests.put(
        f"{BASE_URL}/statements/{pdf_id}/data",
        json=update_data
    )

    if response.status_code == 200:
        updated_data = response.json()
        print(f"✓ 数据修改成功")
        if updated_data.get("sales"):
            print(f"  新产品价格: {updated_data['sales']['product_price']}")
            print(f"  新总计: {updated_data['sales']['total']}")
    else:
        print(f"⚠️  数据修改失败: {response.text}")

    print()
    print("=" * 70)
    print("✅ 完整流程测试完成！")
    print("=" * 70)


def test_batch_parse():
    """测试批量解析功能."""
    print("\n")
    print("=" * 70)
    print("测试批量解析功能")
    print("=" * 70)
    print()

    # 1. 上传多个PDF
    print("步骤1: 上传多个PDF文件")
    print("-" * 70)

    pdf_dir = Path(__file__).parent.parent / "PdfData"
    pdf_files = list(pdf_dir.glob("*.pdf"))[:3]  # 只测试前3个

    pdf_ids = []

    for pdf_path in pdf_files:
        with open(pdf_path, "rb") as f:
            files = {"file": (pdf_path.name, f, "application/pdf")}
            response = requests.post(f"{BASE_URL}/pdfs/upload", files=files)

        if response.status_code == 201:
            pdf_data = response.json()
            pdf_ids.append(pdf_data["id"])
            print(f"✓ 上传成功: {pdf_path.name} (ID: {pdf_data['id']})")
        else:
            print(f"❌ 上传失败: {pdf_path.name}")

    print()

    if not pdf_ids:
        print("❌ 没有可解析的PDF")
        return

    # 2. 批量解析
    print("步骤2: 批量解析PDF")
    print("-" * 70)

    response = requests.post(
        f"{BASE_URL}/pdfs/batch-parse",
        json=pdf_ids
    )

    if response.status_code == 200:
        result = response.json()
        print(f"✓ 批量解析完成")
        print(f"  {result['message']}")
        if result.get("detail"):
            print(f"  {result['detail']}")
    else:
        print(f"❌ 批量解析失败: {response.text}")

    print()
    print("=" * 70)
    print("✅ 批量解析测试完成！")
    print("=" * 70)


def main():
    """主测试函数."""
    try:
        # 测试完整流程
        test_complete_pipeline()

        # 测试批量解析（可选）
        # test_batch_parse()

    except requests.exceptions.ConnectionError:
        print("\n❌ 无法连接到API服务器!")
        print(f"请先启动API服务: ./scripts/run_api.sh")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()


# ============================================================
# END OF test_parse_pipeline.py
# ============================================================
