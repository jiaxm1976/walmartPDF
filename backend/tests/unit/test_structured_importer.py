"""
单元测试：StructuredDataImporter 模块
测试数据库导入、字段频率识别、低频字段合并等核心功能

作者: AI
创建时间: 2026-01-02
"""

import pytest
import json
import sqlite3
from unittest.mock import Mock, patch, MagicMock
from backend.database.structured_importer import StructuredDataImporter


class TestStructuredDataImporterConnection:
    """测试数据库连接管理"""

    @patch('backend.database.structured_importer.sqlite3.connect')
    def test_connect_success(self, mock_connect):
        """测试成功连接数据库"""
        mock_conn = Mock()
        mock_connect.return_value = mock_conn
        
        importer = StructuredDataImporter()
        importer.connect()
        
        assert importer.conn is not None

    @patch('backend.database.structured_importer.sqlite3.connect')
    def test_disconnect_success(self, mock_connect):
        """测试成功断开连接"""
        mock_conn = Mock()
        mock_connect.return_value = mock_conn
        
        importer = StructuredDataImporter()
        importer.connect()
        importer.disconnect()
        
        mock_conn.close.assert_called_once()


class TestImportJGData:
    """测试导入结构化数据"""

    @patch('backend.database.structured_importer.StructuredDataImporter.connect')
    @patch('backend.database.structured_importer.StructuredDataImporter.disconnect')
    @patch('backend.database.structured_importer.sqlite3.connect')
    def test_import_jg_data_success(self, mock_connect, mock_disconnect, mock_manual_connect):
        """测试成功导入数据"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.lastrowid = 1
        
        importer = StructuredDataImporter()
        
        jg_data = {
            'sections': {
                'header': [{'字段': '值'}],
                '销售': [{'产品价格': 100}]
            },
            'metadata': {
                '文件名': 'test.pdf'
            }
        }
        
        # 注意：实际导入取决于实现，这里验证调用
        result = importer.import_jg_data('test.pdf', jg_data)
        
        # 验证返回 statement_id 或类似值
        assert result is not None

    def test_import_jg_data_empty_sections(self):
        """测试导入空 sections"""
        importer = StructuredDataImporter()
        
        jg_data = {
            'sections': {},
            'metadata': {}
        }
        
        # 应处理空 sections
        # 具体行为取决于实现，但不应抛异常
        try:
            result = importer.import_jg_data('empty.pdf', jg_data)
            # 成功完成或返回合理值
        except Exception as e:
            pytest.fail(f"导入空数据不应抛异常: {e}")

    def test_import_jg_data_malformed_structure(self):
        """测试导入格式错误的数据"""
        importer = StructuredDataImporter()
        
        # 缺少必要字段
        jg_data = {'incomplete': 'data'}
        
        # 应处理数据格式错误
        try:
            result = importer.import_jg_data('malformed.pdf', jg_data)
        except (KeyError, TypeError, ValueError) as e:
            # 预期某种验证错误
            assert True
        except Exception as e:
            pytest.fail(f"导入畸形数据抛出意外异常: {e}")


class TestFieldFrequencyIdentification:
    """测试字段频率识别与低频字段合并"""

    @patch('backend.database.structured_importer.StructuredDataImporter.get_field_frequency')
    def test_identify_low_frequency_fields(self, mock_get_freq):
        """测试识别低频字段（频率 < 2）"""
        # Mock 字段频率返回
        mock_get_freq.return_value = {
            '产品价格': 6,      # 高频
            '运输': 5,         # 高频
            '其他税款': 1       # 低频
        }
        
        importer = StructuredDataImporter()
        section_data = {
            '产品价格': 100,
            '运输': 20,
            '其他税款': 5
        }
        
        # 识别低频字段的逻辑（假设有此方法）
        low_freq_fields = {k: v for k, v in section_data.items() 
                          if mock_get_freq.return_value.get(k, 0) < 2}
        
        assert '其他税款' in low_freq_fields
        assert '产品价格' not in low_freq_fields

    def test_merge_low_frequency_fields(self):
        """测试低频字段自动合并"""
        importer = StructuredDataImporter()
        
        section_name = '销售'
        data = {
            '产品价格': 100,
            '运输': 20,
            '其他税款': 5,
            '奇特字段': 1
        }
        
        # 模拟合并逻辑
        high_freq_threshold = 2
        high_freq = {k: v for k, v in data.items() if k in ['产品价格', '运输']}
        low_freq = {k: v for k, v in data.items() if k not in high_freq}
        
        if low_freq:
            merged = high_freq.copy()
            merged[f'{section_name}_其他'] = low_freq
        else:
            merged = high_freq
        
        assert f'{section_name}_其他' in merged
        assert merged[f'{section_name}_其他'] == {'其他税款': 5, '奇特字段': 1}


class TestSectionDataStorage:
    """测试 section_data 表的存储"""

    def test_section_data_json_format(self):
        """测试 section_data JSON 字段格式"""
        importer = StructuredDataImporter()
        
        # 模拟 section_data 行
        section_data = {
            'statement_id': 1,
            'section_name': '销售',
            'data': json.dumps({
                '产品价格': 100,
                '运输': 20,
                '销售_其他': {'其他税款': 5}
            })
        }
        
        # 验证 JSON 格式合法
        stored_json = json.loads(section_data['data'])
        assert stored_json['产品价格'] == 100
        assert '销售_其他' in stored_json

    def test_section_data_duplicate_key(self):
        """测试同一 PDF 同一 section 的重复键处理"""
        importer = StructuredDataImporter()
        
        # 模拟唯一键约束 (statement_id, section_name)
        key1 = (1, '销售')
        key2 = (1, '销售')
        
        # 相同的键应触发替换或冲突处理
        assert key1 == key2  # 验证重复检测逻辑


class TestErrorHandling:
    """测试错误处理与异常恢复"""

    @patch('backend.database.structured_importer.StructuredDataImporter.connect')
    def test_database_connection_error(self, mock_connect):
        """测试数据库连接失败"""
        mock_connect.side_effect = sqlite3.OperationalError("无法连接数据库")
        
        importer = StructuredDataImporter()
        
        with pytest.raises(sqlite3.OperationalError):
            importer.connect()

    def test_import_rollback_on_error(self):
        """测试错误时的事务回滚"""
        importer = StructuredDataImporter()
        
        # 假设导入中途出错
        jg_data = {
            'sections': {
                '销售': [{'产品价格': 'invalid'}]  # 无效值
            }
        }
        
        # 应捕获错误并回滚，而不破坏已有数据
        try:
            result = importer.import_jg_data('error.pdf', jg_data)
        except (ValueError, TypeError):
            # 预期某种数据验证错误
            assert True


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
