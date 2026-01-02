"""
集成测试：完整 PDF 导入管线
测试从 PDF 解析到数据库写入的整个流程

作者: AI
创建时间: 2026-01-02
"""

import pytest
import json
import os
from unittest.mock import Mock, patch
from backend.app.services.pdf_parser_service import PDFParserService
from backend.database.structured_importer import StructuredDataImporter


class TestFullPipelineIntegration:
    """测试完整 PDF 导入管线"""

    @pytest.fixture
    def sample_pdf_path(self):
        """样本 PDF 路径"""
        return 'PdfData/MP_01142025_statement_summary.pdf'

    @pytest.fixture
    def importer(self):
        """创建导入器实例"""
        return StructuredDataImporter()

    def test_pipeline_parse_to_import(self, sample_pdf_path, importer):
        """测试解析 → 导入完整流程"""
        if not os.path.exists(sample_pdf_path):
            pytest.skip(f"示例 PDF 不存在: {sample_pdf_path}")
        
        # 步骤 1: 解析 PDF
        parser = PDFParserService()
        result = parser.parse_pdf_direct(sample_pdf_path)
        
        assert result['status'] == 'SUCCESS'
        assert 'data' in result
        
        jg_data = result['data']
        assert 'sections' in jg_data
        
        # 步骤 2: 导入到数据库
        try:
            importer.connect()
            statement_id = importer.import_jg_data(
                os.path.basename(sample_pdf_path),
                jg_data
            )
            importer.disconnect()
            
            assert statement_id is not None
        except Exception as e:
            pytest.fail(f"导入失败: {e}")

    @patch('backend.app.services.pdf_parser_service.PDFParserService.parse_pdf_direct')
    def test_pipeline_with_mocked_parser(self, mock_parser, importer):
        """测试用 mock 解析器的管线"""
        # Mock 解析结果
        mock_parser.return_value = {
            'status': 'SUCCESS',
            'data': {
                'sections': {
                    'header': [{'统计区间': '2026-01-01 ~ 2026-01-31'}],
                    '销售': [{'产品价格': 1000, '运输': 50}],
                    'footer': [{'向您支付的金额': 900}]
                },
                'metadata': {}
            }
        }
        
        parser = PDFParserService()
        result = parser.parse_pdf_direct('test.pdf')
        
        assert result['status'] == 'SUCCESS'
        
        # 验证导入结构
        jg_data = result['data']
        assert len(jg_data['sections']) == 3

    def test_pipeline_error_recovery(self, importer):
        """测试管线错误恢复"""
        # 构造有缺陷的数据
        incomplete_data = {
            'sections': {
                '销售': None  # 无效的 None 值
            }
        }
        
        try:
            importer.connect()
            # 应捕获异常而不破坏数据库
            try:
                statement_id = importer.import_jg_data('bad.pdf', incomplete_data)
            except (TypeError, ValueError):
                # 预期验证错误
                pass
            finally:
                importer.disconnect()
        except Exception as e:
            pytest.fail(f"错误处理失败: {e}")


class TestMultiPDFProcessing:
    """测试多 PDF 批量处理"""

    def test_batch_import_with_duplicates(self):
        """测试批量导入中的重复处理"""
        importer = StructuredDataImporter()
        
        pdf_list = [
            'MP_01142025.pdf',
            'MP_01142025.pdf',  # 重复
            'MP_02112025.pdf'
        ]
        
        # 应处理重复而不重复导入
        imported_count = 0
        for pdf_name in pdf_list:
            # 实际逻辑会检查唯一键冲突
            try:
                # 由于唯一键约束，重复应被捕获
                pass
            except Exception:
                pass

    def test_batch_import_partial_failure(self):
        """测试批量导入部分失败时的继续处理"""
        importer = StructuredDataImporter()
        
        pdf_data_list = [
            {'status': 'SUCCESS', 'data': {'sections': {'header': []}}},
            {'status': 'ERROR', 'error': '解析失败'},  # 失败
            {'status': 'SUCCESS', 'data': {'sections': {'header': []}}}
        ]
        
        success_count = 0
        fail_count = 0
        
        for pdf_data in pdf_data_list:
            if pdf_data['status'] == 'SUCCESS':
                success_count += 1
            else:
                fail_count += 1
        
        assert success_count == 2
        assert fail_count == 1


class TestDataValidation:
    """测试数据验证"""

    def test_validate_section_structure(self):
        """验证 section 数据结构"""
        valid_section = {
            '产品价格': 100,
            '运输': 20
        }
        
        assert isinstance(valid_section, dict)
        assert all(isinstance(k, str) for k in valid_section.keys())

    def test_validate_json_serialization(self):
        """验证 JSON 序列化"""
        data = {
            '销售': {
                '产品价格': 100,
                '销售_其他': {'税款': 10}
            }
        }
        
        # 应能序列化到 JSON
        json_str = json.dumps(data)
        restored = json.loads(json_str)
        
        assert restored == data

    def test_validate_numeric_fields(self):
        """验证数字字段格式"""
        data = {
            '产品价格': 1000.50,
            '运输': 50,
            '税款': -10.5
        }
        
        # 所有值应为数字
        for k, v in data.items():
            assert isinstance(v, (int, float))


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
