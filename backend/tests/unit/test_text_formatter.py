# -*- coding: utf-8 -*-
"""
单元测试：backend/app/utils/text_formatter.py
覆盖目标：merge_text_blocks, jg_structured_data, parse_category_data
"""
import pytest
from backend.app.utils.text_formatter import (
    TextInfo, merge_text_blocks, jg_structured_data, parse_category_data
)

# 构造最简 OCR 结果（header文本+金额文本）
def make_ocr_result(text, box=None, confidence=0.99):
    if box is None:
        box = [[0,0],[10,0],[10,10],[0,10]]
    return (box, (text, confidence))

class TestTextFormatter:
    def test_merge_text_blocks_basic(self):
        # header文本+金额文本
        ocr_results = [
            make_ocr_result('销售'),
            make_ocr_result('$100.50'),
        ]
        result_text, result_struct = merge_text_blocks(ocr_results)
        # 断言文本输出格式
        assert "'销售'" in result_text
        assert "$100.50" in result_text
        # 断言结构化数据返回类型
        assert isinstance(result_struct, dict)
        assert "classdata" in result_struct
        assert "metadata" in result_struct

    def test_merge_text_blocks_type_guard(self):
        # 构造触发 class_id 类型错误的输入
        ocr_results = [make_ocr_result('header')]
        # 直接调用，断言不抛异常
        try:
            merge_text_blocks(ocr_results)
        except Exception:
            pytest.fail("merge_text_blocks 应不抛异常")

    def test_jg_structured_data_structure(self):
        # 输入示例行，含类别名和“字段,金额”格式
        text_lines = [
            "销售",
            "'商品A',100.0",
            "'商品B',200.0",
            "退款",
            "'退货A',50.0"
        ]
        result = jg_structured_data(text_lines)
        assert isinstance(result, dict)
        assert "classdata" in result
        assert "metadata" in result
        assert result["metadata"]["category_count"] == 2
        assert result["metadata"]["detail_count"] == 3

    def test_parse_category_data_normal(self):
        data = ["销售", ("商品A", "100"), ("商品B", "200"), "退款", ("退货A", "50")]
        result = parse_category_data(data)
        assert result == [
            ["销售", "商品A", "100"],
            ["销售", "商品B", "200"],
            ["退款", "退货A", "50"]
        ]

    def test_parse_category_data_no_category(self):
        # 明细前无分类，预期抛 ValueError
        data = [("商品A", "100")]
        with pytest.raises(ValueError):
            parse_category_data(data, default_category=None)
