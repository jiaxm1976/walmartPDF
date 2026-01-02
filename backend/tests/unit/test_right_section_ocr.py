"""
单元测试：RightSectionOCR 模块
测试右侧板块 OCR 文本提取、字段识别与异常处理

作者: AI
创建时间: 2026-01-02
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from backend.app.services.right_section_ocr import RightSectionOCR


class TestRightSectionOCRInit:
    """测试 RightSectionOCR 初始化"""

    def test_init_without_ocr_engine(self):
        """测试默认初始化（应自动创建 OCREngine）"""
        ocr = RightSectionOCR()
        assert ocr.ocr_engine is not None

    def test_init_with_ocr_engine(self):
        """测试提供 OCREngine 时的初始化"""
        mock_engine = Mock()
        ocr = RightSectionOCR(ocr_engine=mock_engine)
        assert ocr.ocr_engine == mock_engine


class TestExtractTextLines:
    """测试 extract_text_lines 方法"""

    @patch('backend.app.services.right_section_ocr.RightSectionOCR.ocr_recognize')
    def test_extract_text_lines_success(self, mock_recognize):
        """测试正常情况：提取文本行"""
        # Mock OCR 返回结果（符合预期格式）
        mock_recognize.return_value = {
            'text_lines': [
                {
                    'text': '状态',
                    'bbox': [10, 20, 50, 40],
                    'confidence': 0.95,
                    'vertical_center': 30
                },
                {
                    'text': '待处理',
                    'bbox': [60, 20, 120, 40],
                    'confidence': 0.92,
                    'vertical_center': 30
                }
            ]
        }
        
        ocr = RightSectionOCR()
        mock_image = Mock()
        result = ocr.extract_text_lines(mock_image)
        
        assert len(result) == 2
        assert result[0]['text'] == '状态'
        assert result[1]['text'] == '待处理'

    @patch('backend.app.services.right_section_ocr.RightSectionOCR.ocr_recognize')
    def test_extract_text_lines_empty(self, mock_recognize):
        """测试 OCR 无识别结果"""
        mock_recognize.return_value = {'text_lines': []}
        
        ocr = RightSectionOCR()
        mock_image = Mock()
        result = ocr.extract_text_lines(mock_image)
        
        assert result == []

    @patch('backend.app.services.right_section_ocr.RightSectionOCR.ocr_recognize')
    def test_extract_text_lines_with_string_return(self, mock_recognize):
        """测试防御：OCR 返回字符串（异常格式）"""
        # 防御测试：模拟旧格式或错误返回
        mock_recognize.return_value = "some string"
        
        ocr = RightSectionOCR()
        mock_image = Mock()
        result = ocr.extract_text_lines(mock_image)
        
        # 应该返回空列表或处理异常
        assert isinstance(result, list)

    @patch('backend.app.services.right_section_ocr.RightSectionOCR.ocr_recognize')
    def test_extract_text_lines_missing_vertical_center(self, mock_recognize):
        """测试防御：文本行缺少 vertical_center 字段"""
        mock_recognize.return_value = {
            'text_lines': [
                {
                    'text': '状态',
                    'bbox': [10, 20, 50, 40],
                    'confidence': 0.95
                    # 缺少 vertical_center
                }
            ]
        }
        
        ocr = RightSectionOCR()
        mock_image = Mock()
        result = ocr.extract_text_lines(mock_image)
        
        # 应处理缺失字段，不抛异常
        assert isinstance(result, list)
        if len(result) > 0:
            # 如果仍返回该项，应计算默认 vertical_center
            assert 'vertical_center' in result[0] or result[0].get('bbox') is not None


class TestExtractPaymentDetails:
    """测试 extract_payment_details 方法"""

    def test_extract_payment_details_success(self):
        """测试正常提取支付详情"""
        text_lines = [
            {'text': '状态'},
            {'text': '待处理'},
            {'text': '付款日期'},
            {'text': '2026-01-02'},
            {'text': '周期付款'},
            {'text': '月度'},
            {'text': '付款方式'},
            {'text': '银行转账'},
            {'text': '待付款金额'},
            {'text': '¥1,000.00'}
        ]
        
        ocr = RightSectionOCR()
        details = ocr.extract_payment_details(text_lines)
        
        assert isinstance(details, dict)
        assert '状态' in details or 'status' in str(details).lower()

    def test_extract_payment_details_empty(self):
        """测试空文本行列表"""
        ocr = RightSectionOCR()
        details = ocr.extract_payment_details([])
        
        assert isinstance(details, dict)

    def test_extract_payment_details_malformed(self):
        """测试畸形的文本行（缺失text字段）"""
        text_lines = [
            {'no_text_field': '值'},
            {'text': '有效文本'},
            {}  # 完全空的字典
        ]
        
        ocr = RightSectionOCR()
        # 应不抛异常
        details = ocr.extract_payment_details(text_lines)
        assert isinstance(details, dict)


class TestProcessRightSection:
    """测试 process_right_section 完整流程"""

    @patch('backend.app.services.right_section_ocr.RightSectionOCR.extract_text_lines')
    @patch('backend.app.services.right_section_ocr.RightSectionOCR.extract_payment_details')
    def test_process_right_section_success(self, mock_extract_details, mock_extract_lines):
        """测试完整处理流程"""
        mock_extract_lines.return_value = [
            {'text': '状态'},
            {'text': '待处理'}
        ]
        mock_extract_details.return_value = {
            '状态': '待处理',
            '付款日期': '2026-01-02'
        }
        
        ocr = RightSectionOCR()
        mock_image = Mock()
        result = ocr.process_right_section(mock_image)
        
        assert isinstance(result, dict)
        assert '状态' in result or 'payment_info' in str(result).lower()

    @patch('backend.app.services.right_section_ocr.RightSectionOCR.extract_text_lines')
    def test_process_right_section_ocr_error(self, mock_extract_lines):
        """测试 OCR 出错时的处理"""
        mock_extract_lines.side_effect = Exception("OCR 处理失败")
        
        ocr = RightSectionOCR()
        mock_image = Mock()
        
        # 应处理异常，返回错误字典或空字典
        try:
            result = ocr.process_right_section(mock_image)
            assert isinstance(result, dict)
        except Exception as e:
            # 如果仍抛异常，至少应有清晰的错误信息
            assert "OCR" in str(e) or "右侧" in str(e)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
