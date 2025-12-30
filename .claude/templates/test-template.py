# ============================================================
# 文件: 测试模板示例
# 用途: 展示标准的单元测试格式
# 说明: 复制此模板编写新测试
# ============================================================

import pytest
from typing import List, Dict, Any

# 假设我们要测试的函数（实际应从被测模块导入）
# from backend.app.services.example import process_data


# ============================================================
# Test Fixtures（测试夹具）
# ============================================================

@pytest.fixture
def sample_valid_data():
    """提供有效的测试数据."""
    return [
        {"key": "item1", "score": 0.95, "name": "Item 1"},
        {"key": "item2", "score": 0.85, "name": "Item 2"},
        {"key": "item3", "score": 0.75, "name": "Item 3"},
    ]


@pytest.fixture
def sample_invalid_data():
    """提供无效的测试数据."""
    return [
        {"score": 0.95},  # 缺少key字段
        {"key": "item2", "name": "Item 2"},  # 缺少score字段
    ]


# ============================================================
# 正常情况测试（Happy Path Tests）
# ============================================================

class TestProcessDataNormal:
    """测试process_data函数的正常情况."""

    def test_process_valid_data_default_threshold(self, sample_valid_data):
        """测试：使用默认阈值处理有效数据.

        场景：
        - 输入3条有效数据
        - 使用默认threshold=0.8
        - 预期：2条数据通过（score >= 0.8）

        验证：
        - valid_count应为2
        - filtered_count应为1
        - 返回的数据应被标准化（小写）
        """
        result = process_data(sample_valid_data, threshold=0.8)

        assert result["valid_count"] == 2, "应有2条数据通过过滤"
        assert result["filtered_count"] == 1, "应有1条数据被过滤"
        assert len(result["data"]) == 2, "返回数据应包含2条记录"

        # 验证数据标准化
        first_item = result["data"][0]
        assert "key" in first_item, "应包含key字段"
        assert first_item["name"] == "item 1", "名称应被转为小写"

    def test_process_all_data_low_threshold(self, sample_valid_data):
        """测试：使用低阈值应通过所有数据.

        场景：
        - 输入3条数据（最低score=0.75）
        - 使用threshold=0.5
        - 预期：所有数据通过

        验证：
        - valid_count应为3
        - filtered_count应为0
        """
        result = process_data(sample_valid_data, threshold=0.5)

        assert result["valid_count"] == 3, "低阈值应通过所有数据"
        assert result["filtered_count"] == 0, "不应有数据被过滤"

    def test_process_data_returns_standardized_format(self, sample_valid_data):
        """测试：返回数据格式应被标准化.

        场景：
        - 输入包含大写字母的数据
        - 预期：输出字段名和值都转为小写

        验证：
        - 键名应为小写
        - 字符串值应为小写
        """
        result = process_data(sample_valid_data, threshold=0.7)

        for item in result["data"]:
            # 验证所有键都是小写
            for key in item.keys():
                assert key.islower(), f"键{key}应为小写"

            # 验证字符串值是小写
            if "name" in item:
                assert item["name"].islower(), f"名称{item['name']}应为小写"


# ============================================================
# 边界情况测试（Edge Case Tests）
# ============================================================

class TestProcessDataEdgeCases:
    """测试process_data函数的边界情况."""

    def test_process_empty_list(self):
        """测试：空输入列表.

        场景：input_data = []
        预期：返回空结果，不抛出异常（宽松模式）

        验证：
        - valid_count应为0
        - data应为空列表
        """
        result = process_data([], threshold=0.8)

        assert result["valid_count"] == 0, "空输入应返回0条有效数据"
        assert result["data"] == [], "空输入应返回空数据列表"

    def test_process_single_item(self):
        """测试：单条数据.

        场景：只输入一条数据
        预期：正常处理

        验证：
        - 应成功处理单条数据
        """
        single_data = [{"key": "test", "score": 0.9}]
        result = process_data(single_data, threshold=0.8)

        assert result["valid_count"] == 1, "单条数据应被正常处理"
        assert result["data"][0]["key"] == "test"

    def test_process_threshold_boundary_value(self):
        """测试：阈值边界值.

        场景：
        - 数据score = 0.8
        - threshold = 0.8
        - 预期：score >= threshold，应通过

        验证：
        - 边界值数据应通过过滤
        """
        boundary_data = [{"key": "test", "score": 0.8}]
        result = process_data(boundary_data, threshold=0.8)

        assert result["valid_count"] == 1, "边界值应通过过滤（>=）"

    def test_process_threshold_zero(self):
        """测试：阈值为0（最小值）.

        场景：threshold = 0.0
        预期：所有数据通过

        验证：
        - 不应过滤任何数据
        """
        data = [{"key": "test", "score": 0.1}]
        result = process_data(data, threshold=0.0)

        assert result["valid_count"] == 1, "阈值为0应通过所有数据"

    def test_process_threshold_one(self):
        """测试：阈值为1（最大值）.

        场景：threshold = 1.0
        预期：只有score=1.0的数据通过

        验证：
        - 只有完美数据通过
        """
        data = [
            {"key": "perfect", "score": 1.0},
            {"key": "almost", "score": 0.99}
        ]
        result = process_data(data, threshold=1.0)

        assert result["valid_count"] == 1, "阈值为1只应通过完美数据"
        assert result["data"][0]["key"] == "perfect"

    def test_process_missing_optional_score_field(self):
        """测试：缺少可选的score字段.

        场景：数据缺少score字段（可选字段）
        预期：使用默认值1.0

        验证：
        - 应使用默认score=1.0
        - 数据应通过过滤
        """
        data_no_score = [{"key": "test"}]
        result = process_data(data_no_score, threshold=0.8)

        assert result["valid_count"] == 1, "缺少score应使用默认值1.0"


# ============================================================
# 异常情况测试（Exception Tests）
# ============================================================

class TestProcessDataExceptions:
    """测试process_data函数的异常情况."""

    def test_invalid_input_type_string(self):
        """测试：输入类型错误（字符串）.

        场景：input_data = "invalid"
        预期：抛出TypeError

        验证：
        - 应抛出TypeError
        - 错误信息应说明期望list类型
        """
        with pytest.raises(TypeError, match="must be a list"):
            process_data("invalid", threshold=0.8)

    def test_invalid_input_type_dict(self):
        """测试：输入类型错误（字典）.

        场景：input_data = {"key": "value"}
        预期：抛出TypeError
        """
        with pytest.raises(TypeError, match="must be a list"):
            process_data({"key": "value"}, threshold=0.8)

    def test_invalid_threshold_type_string(self):
        """测试：阈值类型错误.

        场景：threshold = "0.8" (字符串)
        预期：抛出TypeError
        """
        data = [{"key": "test", "score": 0.9}]
        with pytest.raises(TypeError, match="must be a number"):
            process_data(data, threshold="0.8")

    def test_invalid_threshold_out_of_range_high(self):
        """测试：阈值超出范围（过高）.

        场景：threshold = 1.5
        预期：抛出ValueError
        """
        data = [{"key": "test", "score": 0.9}]
        with pytest.raises(ValueError, match="between 0.0 and 1.0"):
            process_data(data, threshold=1.5)

    def test_invalid_threshold_out_of_range_low(self):
        """测试：阈值超出范围（过低）.

        场景：threshold = -0.1
        预期：抛出ValueError
        """
        data = [{"key": "test", "score": 0.9}]
        with pytest.raises(ValueError, match="between 0.0 and 1.0"):
            process_data(data, threshold=-0.1)

    def test_missing_required_field_strict_mode(self, sample_invalid_data):
        """测试：缺少必需字段（严格模式）.

        场景：
        - 数据缺少key字段
        - strict_mode=True
        - 预期：抛出ValueError

        验证：
        - 应抛出ValueError
        - 错误信息应说明缺少key字段
        """
        with pytest.raises(ValueError, match="Missing required field"):
            process_data(sample_invalid_data, threshold=0.8, strict_mode=True)

    def test_empty_input_strict_mode(self):
        """测试：空输入（严格模式）.

        场景：
        - input_data = []
        - strict_mode=True
        - 预期：抛出ValueError

        验证：
        - 空输入在严格模式下应抛出异常
        """
        with pytest.raises(ValueError, match="cannot be empty"):
            process_data([], threshold=0.8, strict_mode=True)


# ============================================================
# 严格模式测试
# ============================================================

class TestProcessDataStrictMode:
    """测试process_data函数的严格模式行为."""

    def test_strict_mode_rejects_invalid_data(self, sample_invalid_data):
        """测试：严格模式拒绝无效数据.

        场景：输入无效数据 + strict_mode=True
        预期：抛出ValueError
        """
        with pytest.raises(ValueError):
            process_data(sample_invalid_data, threshold=0.8, strict_mode=True)

    def test_loose_mode_accepts_invalid_data(self, sample_invalid_data):
        """测试：宽松模式接受无效数据并记录错误.

        场景：输入无效数据 + strict_mode=False
        预期：不抛出异常，记录错误到errors列表

        验证：
        - 不应抛出异常
        - error_count > 0
        - errors列表包含错误详情
        """
        result = process_data(sample_invalid_data, threshold=0.8, strict_mode=False)

        assert result["error_count"] > 0, "应记录错误"
        assert len(result["errors"]) > 0, "errors列表应包含错误详情"
        assert "error" in result["errors"][0], "错误应包含描述"


# ============================================================
# 参数化测试（Parametrized Tests）
# ============================================================

@pytest.mark.parametrize("threshold,expected_count", [
    (0.7, 3),  # 低阈值，全部通过
    (0.8, 2),  # 中等阈值，2条通过
    (0.9, 1),  # 高阈值，1条通过
    (1.0, 0),  # 最高阈值，0条通过（没有完美数据）
])
def test_different_thresholds(threshold, expected_count):
    """测试：不同阈值的过滤效果.

    使用参数化测试验证不同阈值的行为.
    """
    data = [
        {"key": "item1", "score": 0.95},
        {"key": "item2", "score": 0.85},
        {"key": "item3", "score": 0.75},
    ]
    result = process_data(data, threshold=threshold)

    assert result["valid_count"] == expected_count, \
        f"阈值{threshold}应有{expected_count}条数据通过"


# ============================================================
# 性能测试（Performance Tests）
# ============================================================

@pytest.mark.slow
def test_process_large_dataset_performance():
    """测试：处理大数据集的性能.

    场景：处理10000条数据
    预期：在合理时间内完成（<1秒）

    验证：
    - 应成功处理大数据集
    - 性能应在可接受范围内
    """
    import time

    # 生成10000条测试数据
    large_data = [
        {"key": f"item{i}", "score": 0.5 + (i % 50) / 100}
        for i in range(10000)
    ]

    start_time = time.time()
    result = process_data(large_data, threshold=0.8)
    elapsed_time = time.time() - start_time

    assert result["valid_count"] > 0, "应处理部分数据"
    assert elapsed_time < 1.0, f"处理时间应<1秒，实际{elapsed_time:.2f}秒"


# ============================================================
# 运行测试
# ============================================================

if __name__ == "__main__":
    # 运行所有测试
    pytest.main([__file__, "-v", "--tb=short"])
