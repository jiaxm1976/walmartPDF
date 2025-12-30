# ============================================================
# 文件: backend/app/utils/field_normalizer.py
# 功能: 字段名规范化处理
# 作者: 开发团队
# 创建时间: 2025-12-19
# 说明: 统一处理PDF解析出的字段名，解决标点、空格、同义词等问题
# ============================================================

import re
import logging
from typing import Dict

logger = logging.getLogger(__name__)


# ============================================================
# 配置：需要去除的尾部标点符号
# ============================================================
# 注意：不包括括号，因为括号通常有配对含义，应该保留
TRAILING_PUNCTUATION = ['：', ':', '。', '.', '，', ',', '！', '!', '？', '?']


# ============================================================
# 配置：英文缩写列表（缩写后统一加空格）
# ============================================================
ABBREVIATIONS = ['WFS', 'MP', 'RC', 'FS', 'SKU', 'ID']


# ============================================================
# 配置：同义词映射表
# ============================================================
SYNONYM_MAP = {
    # Sales板块
    'T沃尔玛出资的节余总额': 'T沃尔玛出资的节余',
    '沃尔玛出资的节余总额': 'T沃尔玛出资的节余',

    # Refund板块
    'T沃尔玛出资的节余总额': 'T沃尔玛出资的节余',

    # WFS板块
    '世界FS 调整': 'WFS 调整',  # OCR误识别
    'WFS 以太坊费': 'WFS 以太坊费',
    'WFS 总折扣': 'WFS 总折扣',

    # 其他常见变体
    '产品价格退款': '产品价格',
    '运输费用': '运输',
    '运输费': '运输',
}


# ============================================================
# 功能函数
# ============================================================

# 移除全角转半角函数


def remove_trailing_punctuation(text: str) -> str:
    """去除尾部标点符号（循环去除所有尾部标点）.

    Args:
        text: 输入文本

    Returns:
        去除尾部标点后的文本

    Example:
        >>> remove_trailing_punctuation("总计：")
        '总计'
        >>> remove_trailing_punctuation("总计：：")
        '总计'
    """
    # 循环去除所有尾部标点符号
    while True:
        removed = False
        for punct in TRAILING_PUNCTUATION:
            if text.endswith(punct):
                text = text[:-len(punct)]
                removed = True
                break
        if not removed:
            break
    return text


def normalize_spaces(text: str) -> str:
    """规范化空格.

    处理：
    1. 去除首尾空格
    2. 多个连续空格压缩为1个
    3. 在英文缩写后统一加空格

    Args:
        text: 输入文本

    Returns:
        规范化后的文本

    Example:
        >>> normalize_spaces("WFS运输税退款")
        'WFS 运输税退款'
        >>> normalize_spaces("  产品价格  ")
        '产品价格'
    """
    # 去除首尾空格
    text = text.strip()

    # 多个连续空格压缩为1个
    text = re.sub(r'\s+', ' ', text)

    # 在英文缩写后统一加空格
    for abbr in ABBREVIATIONS:
        # 匹配缩写后面直接跟中文或其他字符（没有空格）
        pattern = rf'{abbr}(?=[^\s])'
        text = re.sub(pattern, f'{abbr} ', text)

    return text


# 移除清除所有空格函数


# 移除小写转大写函数


# 移除统一预处理函数


def apply_synonym_mapping(text: str) -> str:
    """应用同义词映射.

    Args:
        text: 输入文本

    Returns:
        映射后的标准字段名

    Example:
        >>> apply_synonym_mapping("T沃尔玛出资的节余总额")
        'T沃尔玛出资的节余'
    """
    return SYNONYM_MAP.get(text, text)


def normalize_field_name(field_name: str) -> str:
    """字段名规范化处理（主函数）.

    处理顺序：
    1. 全角转半角
    2. 去除首尾空格
    3. 去除尾部标点符号
    4. 规范化空格（压缩多余空格 + 英文缩写后加空格）
    5. 同义词映射

    Args:
        field_name: 原始字段名

    Returns:
        规范化后的字段名

    Example:
        >>> normalize_field_name("总计：")
        '总计'
        >>> normalize_field_name("WFS运输税退款")
        'WFS 运输税退款'
        >>> normalize_field_name("T沃尔玛出资的节余总额")
        'T沃尔玛出资的节余'
    """
    # Step 1: 移除全角转半角处理
    normalized = field_name

    # Step 2: 去除首尾空格
    normalized = normalized.strip()

    # Step 3: 去除尾部标点符号
    normalized = remove_trailing_punctuation(normalized)

    # Step 4: 规范化空格
    normalized = normalize_spaces(normalized)

    # Step 5: 同义词映射
    normalized = apply_synonym_mapping(normalized)

    return normalized


def normalize_section_data(section_data: Dict[str, str]) -> Dict[str, str]:
    """规范化板块数据的所有字段名.

    Args:
        section_data: 板块数据字典 {原始字段名: 字段值}

    Returns:
        规范化后的字段数据 {规范化字段名: 字段值}

    Example:
        >>> data = {"总计：": "100", "WFS运输税退款": "-10"}
        >>> normalize_section_data(data)
        {'总计': '100', 'WFS 运输税退款': '-10'}
    """
    normalized_data = {}

    for field_name, field_value in section_data.items():
        normalized_name = normalize_field_name(field_name)

        # 如果规范化后的字段名已存在，记录警告
        if normalized_name in normalized_data:
            logger.warning(
                f"字段名冲突: '{field_name}' 规范化为 '{normalized_name}' "
                f"但已存在值 {normalized_data[normalized_name]}，"
                f"新值 {field_value} 将覆盖旧值"
            )

        normalized_data[normalized_name] = field_value

    return normalized_data


def log_unknown_field(section_name: str, field_name: str, field_value: str):
    """记录未知字段（用于后续分析）.

    Args:
        section_name: 板块名称
        field_name: 字段名
        field_value: 字段值
    """
    logger.info(
        f"[Unknown Field] Section={section_name}, "
        f"Field={field_name}, Value={field_value}"
    )


# ============================================================
# 测试用例
# ============================================================

def run_tests():
    """运行测试用例验证规范化函数."""

    print("=" * 80)
    print("字段名规范化测试")
    print("=" * 80)
    print()

    test_cases = [
        # (输入, 期望输出, 测试说明)
        ("总计：", "总计", "去除冒号"),
        ("总计:", "总计", "去除半角冒号"),
        ("产品价格。", "产品价格", "去除句号"),
        ("  产品价格  ", "产品价格", "去除首尾空格"),
        ("产品  价格", "产品 价格", "压缩多余空格"),
        ("WFS运输税退款", "WFS 运输税退款", "缩写后加空格"),
        ("WFS 运输税退款", "WFS 运输税退款", "已有空格保持"),
        ("T沃尔玛出资的节余总额", "T沃尔玛出资的节余", "同义词映射"),
        ("沃尔玛出资的节余总额", "T沃尔玛出资的节余", "同义词映射2"),
        ("ＷＦＳ（以太坊费）", "WFS (以太坊费)", "全角转半角+缩写空格"),
        ("世界FS调整", "WFS 调整", "同义词+缩写空格"),
        ("总计：：", "总计", "多个标点符号"),
        ("WFS总折扣", "WFS 总折扣", "缩写+同义词"),
    ]

    passed = 0
    failed = 0

    for input_name, expected, description in test_cases:
        result = normalize_field_name(input_name)
        if result == expected:
            print(f"✅ PASS: {description}")
            print(f"   输入: '{input_name}' → 输出: '{result}'")
            passed += 1
        else:
            print(f"❌ FAIL: {description}")
            print(f"   输入: '{input_name}'")
            print(f"   期望: '{expected}'")
            print(f"   实际: '{result}'")
            failed += 1
        print()

    print("=" * 80)
    print(f"测试结果: {passed} 通过, {failed} 失败")
    print("=" * 80)

    return failed == 0


# ============================================================
# END OF field_normalizer.py
# ============================================================


if __name__ == "__main__":
    # 运行测试
    success = run_tests()
    exit(0 if success else 1)
