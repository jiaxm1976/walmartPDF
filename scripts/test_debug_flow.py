#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试脚本：PDF 解析流程详细追踪
功能：
1. 配置详细日志输出（文件+控制台）
2. 调用 parse_pdf_direct() 处理 PDF
3. 保存所有中间结果（图片+JSON数据）
4. 生成步骤执行报告
"""

import sys
import os
import json
import logging
from pathlib import Path
from datetime import datetime
import cv2
import numpy as np

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent.parent))

# 设置环境变量，强制使用 Vision OCR 引擎（macOS系统）
os.environ['OCR_ENGINE'] = 'vision'

from backend.app.services.pdf_parser_service import PDFParserService
from backend.app.utils.image_utils import pdf_to_images


# ============================================================
# 日志配置
# ============================================================
def setup_logging(log_dir: str):
    """配置日志系统（文件+控制台两路输出）."""
    os.makedirs(log_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(log_dir, f"debug_flow_{timestamp}.log")
    
    # 清空已存在的handlers
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # 日志格式
    log_format = "%(asctime)s | %(levelname)-8s | %(name)-40s | %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"
    formatter = logging.Formatter(log_format, datefmt=date_format)
    
    # 文件handler（DEBUG级别，记录所有内容）
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    
    # 控制台handler（INFO级别，只显示重要信息）
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    
    # 配置根logger
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # 设置第三方库日志级别
    logging.getLogger('PIL').setLevel(logging.WARNING)
    logging.getLogger('pptx').setLevel(logging.WARNING)
    
    return log_file


# ============================================================
# 主调试函数
# ============================================================
def _make_serializable(obj):
    """将对象转换为可JSON序列化的形式.
    
    Args:
        obj: 待转换对象
        
    Returns:
        可序列化的对象
    """
    if obj is None:
        return None
    elif isinstance(obj, (str, int, float, bool)):
        return obj
    elif isinstance(obj, (np.ndarray, bytes)):
        return "<numpy.ndarray or bytes>"
    elif isinstance(obj, dict):
        return {k: _make_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [_make_serializable(item) for item in obj]
    else:
        return str(obj)
def debug_pdf_parse_flow(
    pdf_path: str,
    output_dir: str = "backend/tests/output",
    dpi: int = 800
):
    """调试 PDF 解析流程.
    
    Args:
        pdf_path: PDF 文件路径
        output_dir: 输出目录（保存日志和中间结果）
        dpi: PDF转图片的DPI
    """
    logger = logging.getLogger(__name__)
    
    # 设置输出目录
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    debug_output_dir = os.path.join(output_dir, f"debug_{timestamp}")
    os.makedirs(debug_output_dir, exist_ok=True)
    
    logger.info("=" * 80)
    logger.info("🚀 开始 PDF 解析流程调试")
    logger.info("=" * 80)
    logger.info(f"📄 PDF 文件: {pdf_path}")
    logger.info(f"📁 输出目录: {debug_output_dir}")
    logger.info(f"⚙️  DPI 设置: {dpi}")
    logger.info(f"🔧 OCR 引擎: Vision (Apple 原生)")
    logger.info("")
    
    # 检查 PDF 文件是否存在
    if not os.path.exists(pdf_path):
        logger.error(f"❌ PDF 文件不存在: {pdf_path}")
        return None
    
    try:
        # 第 0 步：文件信息
        logger.info("[Step 0] 获取文件信息")
        logger.info("-" * 80)
        file_size_mb = os.path.getsize(pdf_path) / (1024 * 1024)
        logger.info(f"  ✓ 文件大小: {file_size_mb:.2f} MB")
        
        # 创建 PDF 解析服务
        logger.info("")
        logger.info("[初始化] 创建 PDFParserService 实例")
        logger.info("-" * 80)
        parser = PDFParserService(dpi=dpi)
        logger.info(f"  ✓ PDFParserService 初始化完成 (DPI={dpi})")
        
        # 调用直接解析方法（主要流程）
        logger.info("")
        logger.info("[Step 1-3] 执行 parse_pdf_direct() 主流程")
        logger.info("-" * 80)
        result = parser.parse_pdf_direct(pdf_path, output_dir=debug_output_dir)
        
        # 处理结果
        logger.info("")
        logger.info("[结果] 解析完成")
        logger.info("-" * 80)
        logger.info(f"  成功: {result['success']}")
        logger.info(f"  耗时: {result['process_time']:.2f} 秒")
        if not result['success']:
            logger.error(f"  错误: {result['error']}")
            return result
        
        # 分析解析结果
        logger.info("")
        logger.info("[分析] 解析结果详情")
        logger.info("-" * 80)
        data = result['data']
        
        left_section = data.get('left_section', {})
        right_section = data.get('right_section', {})
        
        # 解析左侧数据结构（新的板块格式）
        if 'sections' in left_section:
            logger.info(f"  左侧板块信息:")
            sections = left_section.get('sections', {})
            section_order = left_section.get('metadata', {}).get('section_order', [])
            for section_name in section_order:
                section_items = sections.get(section_name, [])
                logger.info(f"    - {section_name}: {len(section_items)} 项")
                # 显示前3个明细
                for item in section_items[:3]:
                    if isinstance(item, dict):
                        field = item.get('field', '?')
                        value = item.get('value', '?')
                        logger.info(f"      • {field} = {value}")
                if len(section_items) > 3:
                    logger.info(f"      ... 还有 {len(section_items) - 3} 项")
            
            metadata = left_section.get('metadata', {})
            logger.info(f"  元数据: {metadata.get('section_count')} 个板块，{metadata.get('detail_count')} 个明细项")
        else:
            # 旧格式兼容
            logger.info(f"  左侧板块:")
            for key, value in left_section.items():
                if isinstance(value, dict):
                    logger.info(f"    - {key}: dict (包含 {len(value)} 项)")
                elif isinstance(value, list):
                    logger.info(f"    - {key}: list (共 {len(value)} 项)")
                else:
                    logger.info(f"    - {key}: {type(value).__name__}")
        
        logger.info(f"  右侧板块: {type(right_section).__name__} (包含 {len(right_section)} 项)")
        
        # 保存详细分析报告
        logger.info("")
        logger.info("[报告] 生成分析报告")
        logger.info("-" * 80)
        report_path = os.path.join(debug_output_dir, "analysis_report.json")
        analysis_report = {
            "pdf_file": pdf_path,
            "timestamp": datetime.now().isoformat(),
            "process_time_sec": result['process_time'],
            "success": result['success'],
            "left_section_keys": list(left_section.keys()),
            "right_section_keys": list(right_section.keys()),
            "left_section_summary": {
                key: {
                    "type": type(value).__name__,
                    "size": len(value) if isinstance(value, (list, dict)) else None
                }
                for key, value in left_section.items()
            }
        }
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(analysis_report, f, ensure_ascii=False, indent=2)
        
        logger.info(f"  ✓ 分析报告已保存: {report_path}")
        
        # 保存详细的解析结果
        logger.info("")
        logger.info("[数据] 保存解析结果")
        logger.info("-" * 80)
        result_path = os.path.join(debug_output_dir, "parse_result.json")
        with open(result_path, 'w', encoding='utf-8') as f:
            # 为了避免序列化错误，进行深度转换
            serializable_data = {
                "left_section": _make_serializable(left_section),
                "right_section": right_section
            }
            json.dump(serializable_data, f, ensure_ascii=False, indent=2, default=str)
        logger.info(f"  ✓ 解析结果已保存: {result_path}")
        
        # 汇总报告
        logger.info("")
        logger.info("=" * 80)
        logger.info("✅ 调试流程完成")
        logger.info("=" * 80)
        logger.info(f"📊 输出文件列表:")
        for root, dirs, files in os.walk(debug_output_dir):
            level = root.replace(debug_output_dir, '').count(os.sep)
            indent = ' ' * 2 * level
            logger.info(f"{indent}📁 {os.path.basename(root)}/")
            subindent = ' ' * 2 * (level + 1)
            for file in files:
                file_size = os.path.getsize(os.path.join(root, file)) / 1024
                logger.info(f"{subindent}📄 {file} ({file_size:.1f} KB)")
        
        logger.info("")
        logger.info(f"🎯 所有输出已保存到: {debug_output_dir}")
        
        return result
        
    except Exception as e:
        logger.error("=" * 80)
        logger.error(f"❌ 调试过程出错: {e}")
        logger.error("=" * 80)
        import traceback
        logger.error(traceback.format_exc())
        return None


# ============================================================
# 主程序
# ============================================================
if __name__ == "__main__":
    # 设置日志
    log_dir = "backend/tests/output"
    log_file = setup_logging(log_dir)
    logger = logging.getLogger(__name__)
    
    logger.info(f"日志文件: {log_file}")
    
    # PDF 文件路径
    pdf_path = "/Users/jiaxinming/JxmWork/walmart-a/PdfData/MP_01142025_statement_summary.pdf"
    
    # 执行调试
    result = debug_pdf_parse_flow(
        pdf_path=pdf_path,
        output_dir="backend/tests/output",
        dpi=800
    )
    
    # 返回状态码
    sys.exit(0 if result and result.get('success') else 1)
