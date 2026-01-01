#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量测试脚本：处理 PdfData 下所有 PDF 文件，统计字段出现频率
功能：
1. 遍历 PdfData 目录下的所有 PDF 文件
2. 对每个 PDF 执行 parse_pdf_direct() 解析
3. 收集所有板块和字段信息
4. 统计字段出现频率
5. 生成频率统计报告和数据库设计建议
"""

import sys
import os
import json
import logging
from pathlib import Path
from collections import defaultdict
from datetime import datetime
import traceback

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent.parent))

# 设置环境变量，使用 Vision OCR
os.environ['OCR_ENGINE'] = 'vision'

from backend.app.services.pdf_parser_service import PDFParserService


# ============================================================
# 日志配置
# ============================================================
def setup_logging(log_dir: str):
    """配置日志系统（文件+控制台两路输出）."""
    os.makedirs(log_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(log_dir, f"batch_test_{timestamp}.log")
    
    # 清空已存在的handlers
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # 日志格式
    log_format = "%(asctime)s | %(levelname)-8s | %(name)-40s | %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"
    formatter = logging.Formatter(log_format, datefmt=date_format)
    
    # 文件handler
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    
    # 控制台handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    
    # 配置根logger
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # 设置第三方库日志级别
    logging.getLogger('PIL').setLevel(logging.WARNING)
    
    return log_file


# ============================================================
# 统计类
# ============================================================
class FieldStatistics:
    """字段统计收集器."""
    
    def __init__(self):
        # 字段 -> 出现次数（哪些 PDF 中出现过）
        self.field_frequency = defaultdict(set)  # field_name -> {pdf_names}
        # 板块 -> 字段列表
        self.section_fields = defaultdict(set)  # section_name -> {field_names}
        # 字段 -> 数据类型集合
        self.field_types = defaultdict(set)  # field_name -> {types}
        # 总 PDF 数
        self.total_pdfs = 0
        # PDF 处理结果
        self.pdf_results = {}  # pdf_name -> {success, sections, detail_count}
    
    def add_pdf_data(self, pdf_name: str, sections: dict):
        """添加一个 PDF 的解析数据.
        
        Args:
            pdf_name: PDF 文件名
            sections: 板块字典 {section_name -> [items]}
        """
        self.total_pdfs += 1
        total_details = 0
        
        for section_name, items in sections.items():
            self.section_fields[section_name].update()  # 标记该板块出现过
            
            for item in items:
                if isinstance(item, dict):
                    field_name = item.get('field', '未知字段')
                    value = item.get('value')
                    
                    # 记录字段出现
                    self.field_frequency[field_name].add(pdf_name)
                    # 记录字段类型
                    value_type = type(value).__name__
                    self.field_types[field_name].add(value_type)
                    # 记录字段属于哪个板块
                    self.section_fields[section_name].add(field_name)
                    
                    total_details += 1
        
        self.pdf_results[pdf_name] = {
            "success": True,
            "sections": list(sections.keys()),
            "detail_count": total_details
        }
    
    def add_pdf_error(self, pdf_name: str, error: str):
        """记录 PDF 处理失败."""
        self.pdf_results[pdf_name] = {
            "success": False,
            "error": error
        }
    
    def get_field_frequency_report(self) -> dict:
        """生成字段频率报告.
        
        Returns:
            dict: 频率统计报告
        """
        report = {
            "total_pdfs": self.total_pdfs,
            "total_unique_fields": len(self.field_frequency),
            "timestamp": datetime.now().isoformat(),
            "fields": []
        }
        
        # 排序：按出现次数从高到低
        sorted_fields = sorted(
            self.field_frequency.items(),
            key=lambda x: len(x[1]),
            reverse=True
        )
        
        for field_name, pdf_set in sorted_fields:
            frequency = len(pdf_set)
            frequency_percent = (frequency / self.total_pdfs * 100) if self.total_pdfs > 0 else 0
            
            # 确定该字段属于哪些板块
            section_names = []
            for section_name, fields in self.section_fields.items():
                if field_name in fields:
                    section_names.append(section_name)
            
            report["fields"].append({
                "field_name": field_name,
                "frequency": frequency,
                "frequency_percent": round(frequency_percent, 2),
                "appears_in_pdfs": sorted(list(pdf_set)),
                "sections": section_names,
                "data_types": sorted(list(self.field_types[field_name]))
            })
        
        return report
    
    def get_database_design_suggestions(self) -> dict:
        """生成数据库设计建议.
        
        Returns:
            dict: 数据库设计建议
        """
        suggestions = {
            "timestamp": datetime.now().isoformat(),
            "categories": {
                "必有字段": [],  # 出现 100% 的字段
                "常见字段": [],  # 出现 >= 90% 的字段
                "通用字段": [],  # 出现 >= 50% 的字段
                "可选字段": [],  # 出现 >= 10% 的字段
                "稀有字段": []   # 出现 < 10% 的字段
            },
            "field_merge_suggestions": [],
            "notes": []
        }
        
        if self.total_pdfs == 0:
            return suggestions
        
        # 分类字段
        for field_name, pdf_set in self.field_frequency.items():
            frequency_percent = (len(pdf_set) / self.total_pdfs * 100)
            
            field_info = {
                "field_name": field_name,
                "frequency": len(pdf_set),
                "frequency_percent": round(frequency_percent, 2),
                "count": len(pdf_set)
            }
            
            if frequency_percent == 100:
                suggestions["categories"]["必有字段"].append(field_info)
            elif frequency_percent >= 90:
                suggestions["categories"]["常见字段"].append(field_info)
            elif frequency_percent >= 50:
                suggestions["categories"]["通用字段"].append(field_info)
            elif frequency_percent >= 10:
                suggestions["categories"]["可选字段"].append(field_info)
            else:
                suggestions["categories"]["稀有字段"].append(field_info)
        
        # 生成合并建议
        rare_fields = suggestions["categories"]["稀有字段"]
        if rare_fields:
            suggestions["field_merge_suggestions"].append({
                "type": "合并稀有字段",
                "reason": "这些字段出现频率 < 10%，可考虑：1) 合并为通用字段；2) 归档为 JSON 对象；3) 弃用",
                "rare_fields": [f["field_name"] for f in rare_fields],
                "recommendation": "建议创建 'other_fields' JSON 字段或 'extra_attributes' 表来存储这些低频字段"
            })
        
        # 添加注释
        suggestions["notes"].append("必有字段：数据库设计为 NOT NULL")
        suggestions["notes"].append("常见字段：数据库设计为 NOT NULL 或提供默认值")
        suggestions["notes"].append("通用字段：数据库设计为可空字段")
        suggestions["notes"].append("可选字段：设为可空或使用 JSON 存储")
        suggestions["notes"].append("稀有字段：考虑合并、归档或使用 JSON/JSONB 存储")
        
        return suggestions


# ============================================================
# 主函数
# ============================================================
def batch_test_pdfs(pdf_dir: str, output_dir: str = "backend/tests/output"):
    """批量测试 PdfData 下的所有 PDF 文件.
    
    Args:
        pdf_dir: PDF 文件目录
        output_dir: 输出目录
    """
    logger = logging.getLogger(__name__)
    
    logger.info("=" * 80)
    logger.info("🚀 开始批量 PDF 测试和字段频率统计")
    logger.info("=" * 80)
    
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    batch_output_dir = os.path.join(output_dir, f"batch_analysis_{timestamp}")
    os.makedirs(batch_output_dir, exist_ok=True)
    
    # 获取所有 PDF 文件
    pdf_path = Path(pdf_dir)
    pdf_files = list(pdf_path.glob("*.pdf"))
    
    if not pdf_files:
        logger.error(f"❌ 未找到任何 PDF 文件：{pdf_dir}")
        return None
    
    logger.info(f"📄 找到 {len(pdf_files)} 个 PDF 文件")
    logger.info("")
    
    # 初始化统计器
    stats = FieldStatistics()
    parser = PDFParserService(dpi=800)
    
    # 处理每个 PDF
    for idx, pdf_file in enumerate(pdf_files, 1):
        pdf_name = pdf_file.name
        logger.info(f"[{idx}/{len(pdf_files)}] 处理：{pdf_name}")
        
        try:
            result = parser.parse_pdf_direct(str(pdf_file))
            
            if result["success"]:
                left_section = result["data"].get("left_section", {})
                sections = left_section.get("sections", {})
                
                stats.add_pdf_data(pdf_name, sections)
                section_count = left_section.get("metadata", {}).get("section_count", 0)
                detail_count = left_section.get("metadata", {}).get("detail_count", 0)
                logger.info(f"  ✓ 成功：{section_count} 个板块，{detail_count} 个明细项")
            else:
                error = result.get("error", "未知错误")
                stats.add_pdf_error(pdf_name, error)
                logger.error(f"  ✗ 失败：{error}")
        
        except Exception as e:
            stats.add_pdf_error(pdf_name, str(e))
            logger.error(f"  ✗ 异常：{e}")
            logger.debug(traceback.format_exc())
    
    logger.info("")
    logger.info("=" * 80)
    logger.info("📊 统计分析")
    logger.info("=" * 80)
    
    # 成功/失败统计
    successful = sum(1 for r in stats.pdf_results.values() if r.get("success", False))
    failed = len(stats.pdf_results) - successful
    logger.info(f"✓ 成功处理：{successful} 个 PDF")
    logger.info(f"✗ 失败：{failed} 个 PDF")
    logger.info(f"🎯 总字段数：{len(stats.field_frequency)} 个")
    logger.info(f"🎯 总板块类型：{len(stats.section_fields)} 个")
    
    # 生成报告
    logger.info("")
    logger.info("=" * 80)
    logger.info("📋 生成统计报告")
    logger.info("=" * 80)
    
    # 1. 字段频率报告
    frequency_report = stats.get_field_frequency_report()
    frequency_file = os.path.join(batch_output_dir, "field_frequency.json")
    with open(frequency_file, 'w', encoding='utf-8') as f:
        json.dump(frequency_report, f, ensure_ascii=False, indent=2)
    logger.info(f"  ✓ 字段频率报告：{frequency_file}")
    
    # 2. 数据库设计建议
    design_suggestions = stats.get_database_design_suggestions()
    design_file = os.path.join(batch_output_dir, "database_design_suggestions.json")
    with open(design_file, 'w', encoding='utf-8') as f:
        json.dump(design_suggestions, f, ensure_ascii=False, indent=2)
    logger.info(f"  ✓ 数据库设计建议：{design_file}")
    
    # 3. PDF 处理结果汇总
    results_file = os.path.join(batch_output_dir, "pdf_processing_results.json")
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(stats.pdf_results, f, ensure_ascii=False, indent=2)
    logger.info(f"  ✓ PDF 处理结果：{results_file}")
    
    # 4. 生成简化版统计表（CSV格式，便于查看）
    summary_file = os.path.join(batch_output_dir, "field_frequency_summary.txt")
    _generate_summary_txt(frequency_report, summary_file)
    logger.info(f"  ✓ 统计摘要：{summary_file}")
    
    # 5. 生成数据库设计建议文本
    suggestion_txt_file = os.path.join(batch_output_dir, "database_design_suggestions.txt")
    _generate_suggestion_txt(design_suggestions, suggestion_txt_file)
    logger.info(f"  ✓ 设计建议文本：{suggestion_txt_file}")
    
    logger.info("")
    logger.info("=" * 80)
    logger.info(f"✅ 批量分析完成！")
    logger.info(f"📁 所有报告已保存到：{batch_output_dir}")
    logger.info("=" * 80)
    
    return batch_output_dir


def _generate_summary_txt(frequency_report: dict, output_file: str):
    """生成字段频率统计摘要表（文本格式）."""
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("=" * 100 + "\n")
        f.write("字段出现频率统计表\n")
        f.write("=" * 100 + "\n\n")
        
        total_pdfs = frequency_report["total_pdfs"]
        f.write(f"总 PDF 数：{total_pdfs}\n")
        f.write(f"总字段数：{frequency_report['total_unique_fields']}\n\n")
        
        f.write("-" * 100 + "\n")
        f.write(f"{'字段名':<40} {'频率':<10} {'百分比':<10} {'所属板块':<30}\n")
        f.write("-" * 100 + "\n")
        
        for field_info in frequency_report["fields"]:
            field_name = field_info["field_name"][:40]
            frequency = field_info["frequency"]
            frequency_percent = field_info["frequency_percent"]
            sections = ", ".join(field_info["sections"][:2])  # 只显示前2个板块
            
            f.write(f"{field_name:<40} {frequency:<10} {frequency_percent:>6.1f}% {sections:<30}\n")
        
        f.write("\n" + "=" * 100 + "\n")
        f.write("说明：\n")
        f.write("  - 频率：该字段在多少个 PDF 中出现过\n")
        f.write("  - 百分比：出现频率占总 PDF 数的比例\n")
        f.write("  - 100%：必有字段（所有 PDF 都有）\n")
        f.write("  - >= 90%：常见字段\n")
        f.write("  - >= 50%：通用字段\n")
        f.write("  - >= 10%：可选字段\n")
        f.write("  - < 10%：稀有字段（考虑合并或归档）\n")


def _generate_suggestion_txt(design_suggestions: dict, output_file: str):
    """生成数据库设计建议文本."""
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("📊 数据库设计建议\n")
        f.write("=" * 80 + "\n\n")
        
        for category, fields in design_suggestions["categories"].items():
            f.write(f"\n【{category}】（{len(fields)} 个字段）\n")
            f.write("-" * 80 + "\n")
            for field in fields:
                f.write(f"  • {field['field_name']:<40} 频率: {field['frequency_percent']:>6.1f}%\n")
        
        f.write("\n\n【合并建议】\n")
        f.write("-" * 80 + "\n")
        for suggestion in design_suggestions["field_merge_suggestions"]:
            f.write(f"  类型：{suggestion['type']}\n")
            f.write(f"  原因：{suggestion['reason']}\n")
            f.write(f"  稀有字段：{', '.join(suggestion['rare_fields'][:5])}\n")
            if len(suggestion['rare_fields']) > 5:
                f.write(f"           ... 还有 {len(suggestion['rare_fields']) - 5} 个\n")
            f.write(f"  建议：{suggestion['recommendation']}\n\n")
        
        f.write("\n【设计原则】\n")
        f.write("-" * 80 + "\n")
        for note in design_suggestions["notes"]:
            f.write(f"  • {note}\n")


# ============================================================
# 主程序
# ============================================================
if __name__ == "__main__":
    # 设置日志
    log_dir = "backend/tests/output"
    log_file = setup_logging(log_dir)
    logger = logging.getLogger(__name__)
    
    logger.info(f"日志文件：{log_file}\n")
    
    # PDF 目录
    pdf_dir = "./PdfData"
    
    # 执行批量测试
    result_dir = batch_test_pdfs(pdf_dir)
    
    sys.exit(0 if result_dir else 1)
