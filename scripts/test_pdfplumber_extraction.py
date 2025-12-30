#!/usr/bin/env python3
# ============================================================
# 文件: scripts/test_pdfplumber_extraction.py
# 功能: 测试pdfplumber对沃尔玛PDF的文本提取效果
# 创建时间: 2025-12-19
# 说明: 对比pdfplumber和OCR两种方案的效果
# ============================================================

import sys
from pathlib import Path

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

try:
    import pdfplumber
except ImportError:
    print("❌ pdfplumber未安装，正在安装...")
    import subprocess
    subprocess.run([sys.executable, "-m", "pip", "install", "pdfplumber"])
    import pdfplumber

def test_pdfplumber_extraction(pdf_path: str):
    """测试pdfplumber文本提取效果."""

    print("=" * 70)
    print("  pdfplumber文本提取测试")
    print("=" * 70)
    print()

    pdf_file = Path(pdf_path)

    if not pdf_file.exists():
        print(f"❌ PDF文件不存在: {pdf_path}")
        return

    print(f"📄 测试PDF: {pdf_file.name}")
    print(f"📊 文件大小: {pdf_file.stat().st_size / 1024:.1f} KB")
    print()

    try:
        with pdfplumber.open(pdf_file) as pdf:
            total_pages = len(pdf.pages)
            print(f"📖 总页数: {total_pages}")
            print()

            # 测试第1页
            print("-" * 70)
            print("第1页提取结果:")
            print("-" * 70)

            page = pdf.pages[0]

            # 方法1: 默认提取
            text_default = page.extract_text()

            if text_default:
                print(f"✅ 默认提取成功，提取了 {len(text_default)} 个字符")
                print()
                print("前500个字符预览:")
                print("-" * 70)
                print(text_default[:500])
                print("-" * 70)
                print()

                # 检查关键词
                keywords = ['销售', '退款', '调整', 'WFS', '沃尔玛', '产品价格', '美元', '$']
                found_keywords = [kw for kw in keywords if kw in text_default]

                if found_keywords:
                    print(f"✅ 找到关键词: {', '.join(found_keywords)}")
                else:
                    print("⚠️  未找到任何关键词")

                print()

                # 保存完整文本到文件
                output_file = PROJECT_ROOT / f"pdfplumber_output_{pdf_file.stem}.txt"
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(text_default)
                print(f"💾 完整文本已保存: {output_file}")

            else:
                print("❌ 默认提取失败，未提取到文本")
                print()

                # 尝试layout模式
                print("尝试layout模式提取...")
                text_layout = page.extract_text(layout=True)

                if text_layout:
                    print(f"✅ layout模式成功，提取了 {len(text_layout)} 个字符")
                    print()
                    print("前500个字符预览:")
                    print("-" * 70)
                    print(text_layout[:500])
                    print("-" * 70)
                else:
                    print("❌ layout模式也失败")
                    print()

                    # 尝试提取表格
                    print("尝试提取表格...")
                    tables = page.extract_tables()

                    if tables:
                        print(f"✅ 找到 {len(tables)} 个表格")
                        print()
                        print("第一个表格预览（前5行）:")
                        print("-" * 70)
                        for i, row in enumerate(tables[0][:5]):
                            print(f"行{i+1}: {row}")
                        print("-" * 70)
                    else:
                        print("❌ 未找到表格")
                        print()
                        print("⚠️  结论: 这是一个扫描版PDF或纯图片PDF")
                        print("         pdfplumber无法提取文本，必须使用OCR方案！")

            print()

            # 测试第2页（如果存在）
            if total_pages > 1:
                print("-" * 70)
                print("第2页提取结果:")
                print("-" * 70)

                page2 = pdf.pages[1]
                text2 = page2.extract_text()

                if text2:
                    print(f"✅ 提取了 {len(text2)} 个字符")
                    print()
                    print("前300个字符预览:")
                    print("-" * 70)
                    print(text2[:300])
                    print("-" * 70)
                else:
                    print("❌ 未提取到文本")

    except Exception as e:
        print(f"❌ 提取过程出错: {e}")
        import traceback
        traceback.print_exc()

    print()
    print("=" * 70)
    print("  测试完成")
    print("=" * 70)


if __name__ == "__main__":
    # 使用项目中的测试PDF
    test_pdf = PROJECT_ROOT / "PdfData" / "MP_01142025_statement_summary.pdf"

    if len(sys.argv) > 1:
        test_pdf = Path(sys.argv[1])

    test_pdfplumber_extraction(str(test_pdf))
