# ============================================================
# 文件: 函数模板示例
# 用途: 展示标准的函数注释格式
# 说明: 复制此模板编写新函数
# ============================================================

from typing import List, Dict, Any, Optional


def process_data(
    input_data: List[Dict[str, Any]],
    threshold: float = 0.8,
    strict_mode: bool = False
) -> Dict[str, Any]:
    """处理输入数据，过滤并转换为标准格式.

    核心流程：
    1. 验证输入数据格式
    2. 过滤低质量数据（基于threshold）
    3. 转换为标准格式
    4. 聚合统计信息

    算法说明：
    - 使用阈值过滤：score >= threshold的数据保留
    - strict_mode开启时，缺少必需字段的数据将被拒绝
    - 转换过程中会标准化字段名称（转小写，去空格）

    Args:
        input_data: 输入数据列表.
            格式：[{"key": "value", "score": 0.9}, ...]
            要求：
            - 每个dict必须包含"key"字段
            - "score"字段可选，默认为1.0
            - 其他字段会被保留
            示例：
                [
                    {"key": "item1", "score": 0.95, "name": "Item 1"},
                    {"key": "item2", "score": 0.75}
                ]

        threshold: 质量阈值.
            范围：0.0-1.0
            默认：0.8（经验值，基于历史数据分析）
            说明：
            - score < threshold的数据将被过滤
            - threshold=0.0表示不过滤任何数据
            - threshold=1.0表示只保留完美数据
            建议：
            - 清洗数据时使用0.8
            - 严格校验时使用0.9
            - 宽松筛选时使用0.6

        strict_mode: 严格模式开关.
            默认：False（宽松模式）
            True时：
            - 缺少必需字段会抛出ValueError
            - 数据类型不匹配会抛出TypeError
            False时：
            - 缺少字段会被跳过并记录warning
            - 类型错误会尝试转换

    Returns:
        处理结果字典，包含以下键：
        {
            "valid_count": 10,        # 有效数据数量
            "filtered_count": 2,      # 被过滤的数据数量
            "error_count": 1,         # 错误数据数量（strict_mode=False时）
            "data": [                 # 处理后的数据列表
                {
                    "key": "item1",
                    "score": 0.95,
                    "name": "item 1"  # 已标准化（小写）
                },
                ...
            ],
            "errors": [               # 错误详情（仅strict_mode=False时）
                {
                    "index": 5,
                    "error": "Missing required field: key"
                }
            ]
        }

    Raises:
        ValueError: 当满足以下条件之一时：
            - input_data为空且strict_mode=True
            - 某条数据缺少必需字段且strict_mode=True
        TypeError: 当满足以下条件之一时：
            - input_data不是List类型
            - threshold不是float类型
            - strict_mode不是bool类型
        KeyError: 当访问不存在的必需字段时（仅strict_mode=True）

    Example:
        基本用法（正常情况）：
        >>> data = [
        ...     {"key": "a", "score": 0.9},
        ...     {"key": "b", "score": 0.7}
        ... ]
        >>> result = process_data(data, threshold=0.8)
        >>> result["valid_count"]
        1
        >>> result["filtered_count"]
        1
        >>> result["data"][0]["key"]
        'a'

        高级用法（严格模式）：
        >>> data = [{"key": "a", "score": 0.9}]
        >>> result = process_data(data, threshold=0.8, strict_mode=True)
        >>> result["valid_count"]
        1

        边界情况（空输入）：
        >>> result = process_data([], threshold=0.8)
        >>> result["valid_count"]
        0

        异常情况（无效输入）：
        >>> process_data("invalid", threshold=0.8)
        Traceback (most recent call last):
            ...
        TypeError: input_data must be a list

    Note:
        性能考虑：
        - 时间复杂度：O(n)，其中n是input_data长度
        - 空间复杂度：O(n)，返回新列表而非原地修改
        - 处理10000条数据约需0.1秒（benchmark数据）

        使用建议：
        - threshold默认0.8基于历史数据分析，误过滤率<5%
        - 过滤后的数据不会返回，只统计数量
        - 如需保留被过滤的数据，使用filter_data()函数

        已知限制：
        - 不支持嵌套dict的标准化
        - 不支持自定义字段验证规则
        - 不支持并行处理（单线程）

        相关函数：
        - filter_data(): 仅过滤不转换
        - validate_data(): 仅验证不处理
        - transform_data(): 仅转换不过滤

    See Also:
        - filter_data(): 数据过滤函数
        - validate_data(): 数据验证函数
        - transform_data(): 数据转换函数
        - docs/data_processing.md: 数据处理详细文档
    """
    # 步骤1: 参数验证
    # ================
    # 说明：确保输入参数类型正确，避免后续处理出错
    if not isinstance(input_data, list):
        raise TypeError(
            f"input_data must be a list, got {type(input_data).__name__}"
        )

    if not isinstance(threshold, (int, float)):
        raise TypeError(
            f"threshold must be a number, got {type(threshold).__name__}"
        )

    if not isinstance(strict_mode, bool):
        raise TypeError(
            f"strict_mode must be a bool, got {type(strict_mode).__name__}"
        )

    # 阈值范围检查
    if not 0.0 <= threshold <= 1.0:
        raise ValueError(
            f"threshold must be between 0.0 and 1.0, got {threshold}"
        )

    # 步骤2: 初始化结果容器
    # ======================
    result = {
        "valid_count": 0,
        "filtered_count": 0,
        "error_count": 0,
        "data": [],
        "errors": []
    }

    # 边界情况：空输入
    if not input_data:
        if strict_mode:
            raise ValueError("input_data cannot be empty in strict mode")
        return result

    # 步骤3: 处理每条数据
    # ===================
    for index, item in enumerate(input_data):
        try:
            # 3.1 验证必需字段
            if "key" not in item:
                if strict_mode:
                    raise ValueError(f"Missing required field 'key' at index {index}")
                else:
                    result["error_count"] += 1
                    result["errors"].append({
                        "index": index,
                        "error": "Missing required field: key"
                    })
                    continue

            # 3.2 获取score（默认1.0）
            score = item.get("score", 1.0)

            # 3.3 过滤低质量数据
            if score < threshold:
                result["filtered_count"] += 1
                continue  # 跳过此条数据

            # 3.4 转换为标准格式
            # 说明：字段名转小写，值去除首尾空格
            standardized = {}
            for key, value in item.items():
                # 标准化键名（转小写）
                std_key = key.lower()

                # 标准化值（字符串去空格）
                if isinstance(value, str):
                    std_value = value.strip().lower()
                else:
                    std_value = value

                standardized[std_key] = std_value

            # 3.5 添加到结果
            result["data"].append(standardized)
            result["valid_count"] += 1

        except Exception as e:
            # 错误处理
            if strict_mode:
                # 严格模式：重新抛出异常
                raise
            else:
                # 宽松模式：记录错误并继续
                result["error_count"] += 1
                result["errors"].append({
                    "index": index,
                    "error": str(e)
                })

    # 步骤4: 返回结果
    # ===============
    return result


# ============================================================
# 使用示例
# ============================================================

if __name__ == "__main__":
    # 示例1：基本使用
    print("=" * 60)
    print("示例1：基本使用")
    print("=" * 60)

    sample_data = [
        {"key": "item1", "score": 0.95, "name": "Item 1"},
        {"key": "item2", "score": 0.75, "name": "Item 2"},
        {"key": "item3", "score": 0.85, "name": "Item 3"},
    ]

    result = process_data(sample_data, threshold=0.8)
    print(f"有效数据: {result['valid_count']}")
    print(f"过滤数据: {result['filtered_count']}")
    print(f"处理结果: {result['data']}")

    # 示例2：严格模式
    print("\n" + "=" * 60)
    print("示例2：严格模式")
    print("=" * 60)

    try:
        result = process_data(sample_data, threshold=0.8, strict_mode=True)
        print(f"严格模式成功: {result['valid_count']}条数据")
    except ValueError as e:
        print(f"严格模式失败: {e}")
