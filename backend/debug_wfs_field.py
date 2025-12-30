#!/usr/bin/env python3
"""
调试wfs_shipping_tax_refund字段识别问题的脚本
"""

import sys
import os
import re
from decimal import Decimal

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入需要的模块
# 移除预处理函数导入
from app.services.left_section_ocr import LeftSectionOCR
from app.services.pdf_parser_service import PDFParserService

def simulate_wfs_field_extraction():
    """
    模拟WFS相关字段的提取过程，重点分析wfs_shipping_tax_refund字段
    """
    print("=== 调试wfs_shipping_tax_refund字段识别 ===\n")
    
    # 1. 测试文本预处理
    test_texts = [
        "WFS 运输税退款",
        "wfs 运输 税 退款",
        "WFS运输税退款",
        "WFS 运输税退款:",
        "wfs_shipping_tax_refund",
        "WFS运输税退款：",
        "沃尔玛运输税退款"
    ]
    
    print("1. 文本预处理测试：")
    for text in test_texts:
        processed = text
        print(f"   原始: '{text}' -> 预处理后: '{processed}'")
    
    print("\n2. 字段名匹配测试：")
    
    # 2. 检查字段名映射
    # 模拟PDFParserService中的字段名映射
    section_fields = {
        "sales": [
            "product_price", "shipping", "wfs_shipping_refund", 
            "net_tax_collected", "net_commission", "withholding_tax",
            "wfs_shipping_tax_refund", "walmart_funded_savings"
        ]
    }
    
    # 模拟SYNONYM_MAP
    SYNONYM_MAP = {
        "WFS运输税退款": "wfs_shipping_tax_refund",
        "WFS运输税退款:": "wfs_shipping_tax_refund",
        "WFS运输税退款：": "wfs_shipping_tax_refund",
        "WFS 运输税退款": "wfs_shipping_tax_refund",
        "运输税退款": "wfs_shipping_tax_refund",
        "WFS运输退款": "wfs_shipping_refund",
        "WFS调整": "wfs_adjustment",
        "世界FS调整": "wfs_adjustment"
    }
    
    # 测试字段匹配
    test_field_names = [
        "WFS运输税退款",
        "WFS 运输税退款: 123.45",
        "运输税退款 45.67",
        "WFS运输税退款： 78.90",
        "沃尔玛出资的节余 10.00"
    ]
    
    for field_text in test_field_names:
        processed = field_text
        
        # 提取金额的正则（与left_section_ocr.py中的保持一致）
        amount_pattern = r'[-−]?[$＄][,\d]*\.?\d*'
        amount_match = re.search(amount_pattern, field_text)
        amount = amount_match.group() if amount_match else None
        
        # 提取键名（去除金额部分）
        key_part = re.sub(amount_pattern, '', field_text).strip()
        processed_key = key_part
        
        # 查找同义词映射
        mapped_key = SYNONYM_MAP.get(processed_key)
        
        print(f"   原始文本: '{field_text}'")
        print(f"   预处理后: '{processed}'")
        print(f"   提取键名: '{key_part}' -> 预处理键名: '{processed_key}'")
        print(f"   映射结果: '{mapped_key}'")
        print(f"   提取金额: '{amount}'")
        print(f"   是否匹配wfs_shipping_tax_refund: {mapped_key == 'wfs_shipping_tax_refund'}")
        print()
    
    # 3. 测试金额提取正则
    print("3. 金额提取正则测试：")
    test_amounts = [
        "$123.45",
        "$1,234.56",
        "-$78.90",
        "＄10.00",  # 全角
        "-＄5.55",  # 全角带负号
        "$0.00",
        "123.45"
    ]
    
    amount_pattern = r'[-−]?[$＄][,d]*\.?\d*'
    for text in test_amounts:
        match = re.search(amount_pattern, text)
        if match:
            print(f"   '{text}' -> 匹配: '{match.group()}'")
        else:
            print(f"   '{text}' -> 不匹配")
    
    # 4. 测试板块标题识别
    print("\n4. 板块标题识别测试：")
    test_sections = [
        "销售",
        "销售 1161.46美元",
        "调整",
        "WFS",
        "WFS 调整",
        "其他活动"
    ]
    
    section_keywords = {
        "sales": [r"销售", r"SALES"],
        "adjustment": [r"调整", r"ADJUSTMENT"],
        "wfs": [r"WFS", r"世界FS"],
        "other_activity": [r"其他活动", r"OTHERACTIVITY"]
    }
    
    for section in test_sections:
        processed = section
        matched = False
        matched_section = None
        
        for section_name, keywords in section_keywords.items():
            for keyword in keywords:
                if re.search(keyword, processed, re.IGNORECASE):
                    matched = True
                    matched_section = section_name
                    break
            if matched:
                break
        
        print(f"   '{section}' -> 预处理: '{processed}' -> 匹配板块: '{matched_section}'")
    
    print("\n=== 调试结束 ===")

def debug_with_actual_data():
    """
    使用实际的PDF解析数据进行调试
    """
    print("\n=== 使用实际PDF数据调试 ===\n")
    
    try:
        # 尝试加载一个实际的PDF文件进行测试
        pdf_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "test_data", "MP_04222025_statement_summary.pdf"
        )
        
        if not os.path.exists(pdf_path):
            print(f"测试PDF文件不存在: {pdf_path}")
            print("请确保测试文件存在于正确位置")
            return
        
        print(f"正在解析PDF: {pdf_path}")
        
        # 创建解析器实例
        parser = PDFParserService(pdf_path)
        
        # 解析PDF
        result = parser.parse()
        
        # 打印解析结果
        print("\n解析结果:")
        print(f"总页数: {result.get('total_pages', 0)}")
        
        # 查看销售模块数据
        sales_data = result.get('sections', {}).get('sales', {})
        print(f"\n销售模块数据:")
        print(sales_data)
        
        # 检查wfs_shipping_tax_refund字段
        wfs_shipping_tax_refund = sales_data.get('wfs_shipping_tax_refund')
        print(f"\nwfs_shipping_tax_refund字段值: {wfs_shipping_tax_refund}")
        
        # 检查其他WFS相关字段
        wfs_fields = [
            'wfs_shipping_refund',
            'wfs_shipping_tax_refund',
            'walmart_funded_savings'
        ]
        
        print("\nWFS相关字段:")
        for field in wfs_fields:
            value = sales_data.get(field)
            print(f"  {field}: {value}")
            
    except Exception as e:
        print(f"解析过程中发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    simulate_wfs_field_extraction()
    debug_with_actual_data()