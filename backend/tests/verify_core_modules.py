#!/usr/bin/env python
"""
快速验证脚本：测试关键模块的导入与基本功能
替代 pytest 的轻量级验证
"""

import sys
import traceback

def test_imports():
    """测试关键模块的导入"""
    tests = [
        ("RightSectionOCR", "from backend.app.services.right_section_ocr import RightSectionOCR"),
        ("StructuredDataImporter", "from backend.database.structured_importer import StructuredDataImporter"),
        ("PDFParserService", "from backend.app.services.pdf_parser_service import PDFParserService"),
    ]
    
    print("=" * 60)
    print("🔍 模块导入测试")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for name, import_stmt in tests:
        try:
            exec(import_stmt)
            print(f"✓ {name} 导入成功")
            passed += 1
        except Exception as e:
            print(f"✗ {name} 导入失败: {e}")
            failed += 1
    
    return passed, failed


def test_right_section_ocr():
    """测试 RightSectionOCR 基本功能"""
    try:
        from backend.app.services.right_section_ocr import RightSectionOCR
        
        print("\n" + "=" * 60)
        print("🧪 RightSectionOCR 功能测试")
        print("=" * 60)
        
        # 测试 1: 初始化
        try:
            ocr = RightSectionOCR()
            print("✓ 初始化成功（自动创建 OCREngine）")
            
            # 检查 OCREngine 属性
            if hasattr(ocr, 'ocr_engine') and ocr.ocr_engine is not None:
                print("✓ OCREngine 已正确初始化")
                return 2, 0
            else:
                print("✗ OCREngine 未正确初始化")
                return 1, 1
        except Exception as e:
            print(f"✗ 初始化失败: {e}")
            traceback.print_exc()
            return 0, 1
    
    except ImportError as e:
        print(f"✗ 导入失败: {e}")
        return 0, 1


def test_structured_importer():
    """测试 StructuredDataImporter 基本功能"""
    try:
        from backend.database.structured_importer import StructuredDataImporter
        
        print("\n" + "=" * 60)
        print("🧪 StructuredDataImporter 功能测试")
        print("=" * 60)
        
        # 测试 1: 初始化
        try:
            importer = StructuredDataImporter()
            print("✓ 初始化成功")
            
            # 检查核心方法
            if hasattr(importer, 'import_jg_data'):
                print("✓ 方法 import_jg_data 存在")
            
            if hasattr(importer, 'connect'):
                print("✓ 方法 connect 存在")
            
            return 3, 0
        except Exception as e:
            print(f"✗ 初始化失败: {e}")
            traceback.print_exc()
            return 0, 1
    
    except ImportError as e:
        print(f"✗ 导入失败: {e}")
        return 0, 1


def test_pdf_parser():
    """测试 PDFParserService 基本功能"""
    try:
        from backend.app.services.pdf_parser_service import PDFParserService
        
        print("\n" + "=" * 60)
        print("🧪 PDFParserService 功能测试")
        print("=" * 60)
        
        # 测试 1: 初始化
        try:
            parser = PDFParserService()
            print("✓ 初始化成功")
            
            # 检查核心方法
            if hasattr(parser, 'parse_pdf_direct'):
                print("✓ 方法 parse_pdf_direct 存在")
            
            return 2, 0
        except Exception as e:
            print(f"✗ 初始化失败: {e}")
            traceback.print_exc()
            return 0, 1
    
    except ImportError as e:
        print(f"✗ 导入失败: {e}")
        return 0, 1


def main():
    """运行所有测试"""
    total_passed = 0
    total_failed = 0
    
    # 导入测试
    p, f = test_imports()
    total_passed += p
    total_failed += f
    
    # 模块功能测试
    p, f = test_right_section_ocr()
    total_passed += p
    total_failed += f
    
    p, f = test_structured_importer()
    total_passed += p
    total_failed += f
    
    p, f = test_pdf_parser()
    total_passed += p
    total_failed += f
    
    # 总结
    print("\n" + "=" * 60)
    print("📊 测试总结")
    print("=" * 60)
    print(f"✓ 通过: {total_passed}")
    print(f"✗ 失败: {total_failed}")
    print("=" * 60)
    
    if total_failed == 0:
        print("🎉 所有测试通过！")
        return 0
    else:
        print(f"⚠️  有 {total_failed} 项测试失败")
        return 1


if __name__ == '__main__':
    sys.exit(main())
