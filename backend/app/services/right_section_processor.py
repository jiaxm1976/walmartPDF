#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
右侧数据处理模块

功能：
  1. 专门处理 PDF 右侧数据识别
  2. 不涉及左侧（header、sales、refund等）数据处理
  3. 将所有右侧字段统一存储为 'right_section' 板块
  4. 支持独立导入到 section_data 表

使用方式：
  from backend.app.services.right_section_processor import RightSectionProcessor
  
  processor = RightSectionProcessor()
  right_data = processor.extract_right_section(pdf_path)
  # 返回: Dict[str, Any] 格式的右侧数据
  # 包含所有字段：支付状态、付款日期、周期付款、付款方式、设备方式等

作者：AI 助手
日期：2026-01-02
"""

import logging
from typing import Dict, Any, Optional, List
import re

logger = logging.getLogger(__name__)


class RightSectionProcessor:
    """右侧数据处理器"""
    
    # 右侧数据字段映射（通过 OCR 识别的中文字段名 -> 数据库字段名）
    PAYMENT_FIELD_MAP = {
        '状态': 'status',
        '付款日期': 'payment_date',
        '周期付款': 'payment_frequency',
        '付款方式': 'payment_method',
        '设备方式': 'device_method',
        '待付款金额': 'amount_to_be_paid',
        '等待回款金额': 'amount_waiting_return',
        '回款等待期': 'return_waiting_period',
        '警告信息': 'warning_message'
    }
    
    def __init__(self):
        """初始化右侧数据处理器"""
        self.logger = logger
    
    def extract_right_section(self, ocr_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        从 OCR 数据中提取右侧数据
        
        Args:
            ocr_data: PDF 处理后的 OCR 数据字典
                      通常包含 right_section / payment_details 等字段
        
        Returns:
            Dict[str, Any]: 右侧数据字典，所有字段都属于 'right_section' 板块
            {
                '状态': '...',
                '付款日期': '...',
                '周期付款': '...',
                ...
            }
        """
        try:
            right_data = {}
            
            # 尝试从不同的数据源中提取右侧字段
            # 优先级：payment_details > right_section > other_section
            
            # 方式1: 从 payment_details 提取（兼容旧数据结构）
            if 'payment_details' in ocr_data:
                payment_info = ocr_data['payment_details']
                if isinstance(payment_info, dict):
                    right_data.update(self._extract_payment_fields(payment_info))
            
            # 方式2: 从 right_section 提取
            if 'right_section' in ocr_data:
                right_section = ocr_data['right_section']
                if isinstance(right_section, dict):
                    right_data.update(right_section)
            
            # 方式3: 直接从 ocr_data 中寻找支付相关字段
            right_data.update(self._extract_payment_fields_direct(ocr_data))
            
            logger.info(f"✓ 右侧数据提取完成，共 {len(right_data)} 个字段")
            return right_data
        
        except Exception as e:
            logger.error(f"✗ 右侧数据提取失败: {e}")
            return {}
    
    def _extract_payment_fields(self, payment_info: Dict) -> Dict[str, Any]:
        """
        从支付信息中提取字段
        
        Args:
            payment_info: 支付信息字典
        
        Returns:
            提取后的字段字典
        """
        fields = {}
        
        # 标准字段映射
        field_mappings = {
            'status': ['status', '状态', 'payment_status'],
            'payment_date': ['payment_date', '付款日期', 'pay_date'],
            'payment_frequency': ['payment_frequency', '周期付款', 'frequency'],
            'payment_method': ['payment_method', '付款方式', 'method'],
            'device_method': ['device_method', '设备方式', 'device'],
            'amount_to_be_paid': ['amount_to_be_paid', '待付款金额', 'amount_pending'],
            'amount_waiting_return': ['amount_waiting_return', '等待回款金额', 'awaiting_return'],
            'return_waiting_period': ['return_waiting_period', '回款等待期', 'waiting_period'],
            'warning_message': ['warning_message', '警告信息', 'warning']
        }
        
        for output_key, input_keys in field_mappings.items():
            for input_key in input_keys:
                if input_key in payment_info:
                    # 使用中文字段名作为键
                    chinese_key = self._find_chinese_key(input_key)
                    fields[chinese_key] = payment_info[input_key]
                    break
        
        return fields
    
    def _extract_payment_fields_direct(self, ocr_data: Dict) -> Dict[str, Any]:
        """
        直接从 OCR 数据中寻找支付相关字段
        
        Args:
            ocr_data: OCR 数据字典
        
        Returns:
            提取后的字段字典
        """
        fields = {}
        
        # 支付相关字段的中文名称列表
        payment_keywords = [
            '状态', '付款日期', '周期付款', '付款方式', '设备方式',
            '待付款金额', '等待回款金额', '回款等待期', '警告信息'
        ]
        
        for key in payment_keywords:
            if key in ocr_data:
                fields[key] = ocr_data[key]
        
        return fields
    
    def _find_chinese_key(self, english_key: str) -> str:
        """
        根据英文字段名找到对应的中文字段名
        
        Args:
            english_key: 英文字段名
        
        Returns:
            对应的中文字段名，如未找到则返回英文名
        """
        reverse_map = {
            'status': '状态',
            'payment_status': '状态',
            'payment_date': '付款日期',
            'pay_date': '付款日期',
            'payment_frequency': '周期付款',
            'frequency': '周期付款',
            'payment_method': '付款方式',
            'method': '付款方式',
            'device_method': '设备方式',
            'device': '设备方式',
            'amount_to_be_paid': '待付款金额',
            'amount_pending': '待付款金额',
            'amount_waiting_return': '等待回款金额',
            'awaiting_return': '等待回款金额',
            'return_waiting_period': '回款等待期',
            'waiting_period': '回款等待期',
            'warning_message': '警告信息',
            'warning': '警告信息'
        }
        
        return reverse_map.get(english_key, english_key)
    
    def validate_right_section_data(self, right_data: Dict[str, Any]) -> bool:
        """
        验证右侧数据完整性
        
        Args:
            right_data: 右侧数据字典
        
        Returns:
            True 如果数据有效，False 否则
        """
        if not isinstance(right_data, dict):
            logger.warning(f"⚠ 右侧数据类型错误: {type(right_data)}")
            return False
        
        if len(right_data) == 0:
            logger.warning("⚠ 右侧数据为空")
            return False
        
        logger.info(f"✓ 右侧数据验证通过 ({len(right_data)} 个字段)")
        return True
    
    def format_right_section_for_db(self, right_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        格式化右侧数据以便存储到数据库
        
        Args:
            right_data: 原始右侧数据字典
        
        Returns:
            格式化后的字典，准备存储到 section_data 表
        """
        formatted = {}
        
        for key, value in right_data.items():
            # 清理和转换值
            if value is None:
                formatted[key] = None
            elif isinstance(value, str):
                formatted[key] = value.strip()
            elif isinstance(value, (int, float, bool)):
                formatted[key] = value
            else:
                formatted[key] = str(value)
        
        logger.info(f"✓ 右侧数据格式化完成 ({len(formatted)} 个字段)")
        return formatted


def merge_right_section_to_structured_data(
    structured_data: Dict[str, Any],
    right_section: Dict[str, Any]
) -> Dict[str, Any]:
    """
    将右侧数据合并到 jg_structured_data 格式中
    
    Args:
        structured_data: jg_structured_data() 的输出
        right_section: 右侧数据字典
    
    Returns:
        合并后的 structured_data，新增 'right_section' 板块
    """
    if 'sections' not in structured_data:
        structured_data['sections'] = {}
    
    # 将右侧数据转换为 sections 格式
    # sections 格式: {section_name: [{'field': key, 'value': value}, ...]}
    right_section_items = [
        {'field': key, 'value': value}
        for key, value in right_section.items()
    ]
    
    structured_data['sections']['right_section'] = right_section_items
    
    logger.info(f"✓ 右侧数据已合并到 structured_data (板块名: 'right_section')")
    return structured_data


if __name__ == '__main__':
    # 测试用例
    import logging
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s | %(levelname)s | %(message)s'
    )
    
    processor = RightSectionProcessor()
    
    # 测试数据
    test_data = {
        'payment_details': {
            'status': '待发送',
            'payment_date': '2025-01-08',
            'payment_frequency': '每两周一次',
            'payment_method': '直接存款',
            'device_method': 'FBA',
            'amount_to_be_paid': '$1234.56',
            'amount_waiting_return': '$567.89',
            'return_waiting_period': '14 天'
        }
    }
    
    right_section = processor.extract_right_section(test_data)
    print(f"提取结果: {right_section}")
    
    if processor.validate_right_section_data(right_section):
        formatted = processor.format_right_section_for_db(right_section)
        print(f"格式化结果: {formatted}")
