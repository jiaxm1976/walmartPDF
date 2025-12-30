#!/usr/bin/env python3
# ============================================================
# 文件: scripts/test_api.py
# 功能: API接口测试脚本
# 作者: 开发团队
# 创建时间: 2025-12-18
# 说明: 测试PDF上传和数据修改接口
# ============================================================

import sys
from pathlib import Path
import requests
import json
from decimal import Decimal

# API基础URL
BASE_URL = "http://localhost:8000"
API_V1_URL = f"{BASE_URL}/api/v1"


def test_health_check():
    """测试健康检查接口."""
    print("=" * 60)
    print("1. 测试健康检查接口")
    print("=" * 60)

    # 根路径健康检查
    response = requests.get(f"{BASE_URL}/")
    print(f"GET {BASE_URL}/")
    print(f"状态码: {response.status_code}")
    print(f"响应: {response.json()}")
    print()

    # Health接口
    response = requests.get(f"{BASE_URL}/health")
    print(f"GET {BASE_URL}/health")
    print(f"状态码: {response.status_code}")
    print(f"响应: {response.json()}")
    print()

    # API v1健康检查
    response = requests.get(f"{API_V1_URL}/health")
    print(f"GET {API_V1_URL}/health")
    print(f"状态码: {response.status_code}")
    print(f"响应: {response.json()}")
    print()


def test_pdf_upload(pdf_path: str):
    """测试PDF上传接口.

    Args:
        pdf_path: PDF文件路径

    Returns:
        int: 上传成功的PDF ID，失败返回None
    """
    print("=" * 60)
    print("2. 测试PDF上传接口")
    print("=" * 60)

    if not Path(pdf_path).exists():
        print(f"❌ PDF文件不存在: {pdf_path}")
        return None

    # 上传PDF
    with open(pdf_path, "rb") as f:
        files = {"file": (Path(pdf_path).name, f, "application/pdf")}
        response = requests.post(f"{API_V1_URL}/pdfs/upload", files=files)

    print(f"POST {API_V1_URL}/pdfs/upload")
    print(f"状态码: {response.status_code}")

    if response.status_code == 201:
        data = response.json()
        print(f"✓ 上传成功!")
        print(f"  PDF ID: {data['id']}")
        print(f"  文件名: {data['filename']}")
        print(f"  大小: {data['file_size']} bytes")
        print(f"  哈希: {data['file_hash']}")
        print(f"  状态: {data['process_status']}")
        print()
        return data['id']
    else:
        print(f"❌ 上传失败: {response.text}")
        print()
        return None


def test_pdf_list():
    """测试PDF列表查询接口."""
    print("=" * 60)
    print("3. 测试PDF列表查询接口")
    print("=" * 60)

    response = requests.get(f"{API_V1_URL}/pdfs/", params={"page": 1, "page_size": 10})
    print(f"GET {API_V1_URL}/pdfs/?page=1&page_size=10")
    print(f"状态码: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"✓ 查询成功!")
        print(f"  总记录数: {data['total']}")
        print(f"  当前页: {data['page']}")
        print(f"  每页数量: {data['page_size']}")
        print(f"  总页数: {data['total_pages']}")
        print(f"  记录数: {len(data['items'])}")
        if data['items']:
            print(f"  第一条记录ID: {data['items'][0]['id']}")
    else:
        print(f"❌ 查询失败: {response.text}")
    print()


def test_pdf_detail(pdf_id: int):
    """测试PDF详情查询接口.

    Args:
        pdf_id: PDF文件ID
    """
    print("=" * 60)
    print("4. 测试PDF详情查询接口")
    print("=" * 60)

    response = requests.get(f"{API_V1_URL}/pdfs/{pdf_id}")
    print(f"GET {API_V1_URL}/pdfs/{pdf_id}")
    print(f"状态码: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"✓ 查询成功!")
        print(f"  ID: {data['id']}")
        print(f"  文件名: {data['filename']}")
        print(f"  原始文件名: {data['original_filename']}")
        print(f"  状态: {data['process_status']}")
    else:
        print(f"❌ 查询失败: {response.text}")
    print()


def test_statement_data_update(pdf_id: int):
    """测试对账单数据更新接口.

    Args:
        pdf_id: PDF文件ID
    """
    print("=" * 60)
    print("5. 测试对账单数据更新接口")
    print("=" * 60)

    # 构造更新数据（示例）
    update_data = {
        "header": {
            "opening_balance": "1500.00",
            "reserve_funds": "300.00"
        },
        "sales": {
            "product_price": "2000.00",
            "shipping": "100.00",
            "total": "2100.00"
        }
    }

    response = requests.put(
        f"{API_V1_URL}/statements/{pdf_id}/data",
        json=update_data
    )
    print(f"PUT {API_V1_URL}/statements/{pdf_id}/data")
    print(f"更新数据: {json.dumps(update_data, indent=2)}")
    print(f"状态码: {response.status_code}")

    if response.status_code == 200:
        print(f"✓ 更新成功!")
        data = response.json()
        if data.get('header'):
            print(f"  头部 - 期初余额: {data['header']['opening_balance']}")
            print(f"  头部 - 备用金: {data['header']['reserve_funds']}")
        if data.get('sales'):
            print(f"  销售 - 产品价格: {data['sales']['product_price']}")
            print(f"  销售 - 运输: {data['sales']['shipping']}")
            print(f"  销售 - 总计: {data['sales']['total']}")
    else:
        print(f"❌ 更新失败: {response.text}")
    print()


def test_statement_validate(pdf_id: int):
    """测试数据验证接口.

    Args:
        pdf_id: PDF文件ID
    """
    print("=" * 60)
    print("6. 测试数据验证接口")
    print("=" * 60)

    response = requests.post(f"{API_V1_URL}/statements/{pdf_id}/validate")
    print(f"POST {API_V1_URL}/statements/{pdf_id}/validate")
    print(f"状态码: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"✓ 验证完成!")
        print(f"  消息: {data['message']}")
        if data.get('detail'):
            print(f"  详情: {data['detail']}")
    else:
        print(f"❌ 验证失败: {response.text}")
    print()


def main():
    """主测试流程."""
    print("\n")
    print("=" * 60)
    print("Walmart PDF解析系统 - API接口测试")
    print("=" * 60)
    print(f"API地址: {BASE_URL}")
    print("=" * 60)
    print("\n")

    try:
        # 1. 健康检查
        test_health_check()

        # 2. 测试PDF上传（使用项目中的测试PDF）
        test_pdf_path = Path(__file__).parent.parent / "PdfData" / "MP_01142025_statement_summary.pdf"
        pdf_id = test_pdf_upload(str(test_pdf_path))

        if pdf_id:
            # 3. 查询PDF列表
            test_pdf_list()

            # 4. 查询PDF详情
            test_pdf_detail(pdf_id)

            # 5. 更新对账单数据（需要先有数据）
            # 注意：实际使用中需要先通过解析流程生成数据
            print("⚠️  跳过数据更新测试（需要先解析PDF生成数据）")
            # test_statement_data_update(pdf_id)

            # 6. 数据验证
            print("⚠️  跳过数据验证测试（需要先解析PDF生成数据）")
            # test_statement_validate(pdf_id)

        print("=" * 60)
        print("✅ API测试完成!")
        print("=" * 60)
        print("\n可以访问以下地址查看API文档:")
        print(f"  Swagger UI: {BASE_URL}/api/docs")
        print(f"  ReDoc: {BASE_URL}/api/redoc")
        print()

    except requests.exceptions.ConnectionError:
        print("\n❌ 无法连接到API服务器!")
        print(f"请先启动API服务: ./scripts/run_api.sh")
        print(f"或者运行: cd backend && uvicorn main:app --reload")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()


# ============================================================
# END OF test_api.py
# ============================================================
