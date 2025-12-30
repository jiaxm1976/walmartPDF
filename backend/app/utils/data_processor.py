# ============================================================
# 文件: backend/app/utils/data_processor.py
# 功能: 数据处理工具（集成规范化+核心字段+other_total）
# 作者: 开发团队
# 创建时间: 2025-12-19
# 说明: 处理PDF解析数据，准备入库
# ============================================================

import logging
from typing import Dict, Tuple
from decimal import Decimal

# 导入配置和工具
from app.config.core_fields import (
    is_core_field,
    get_english_field_name,
    CORE_FIELDS_MAP,
)
from app.utils.field_normalizer import (
    normalize_field_name,
    normalize_section_data,
    log_unknown_field,
)

logger = logging.getLogger(__name__)


# ============================================================
# 核心函数
# ============================================================

def parse_amount(value_str: str) -> Decimal:
    """解析金额字符串为Decimal.

    Args:
        value_str: 金额字符串（可能包含$、逗号等）

    Returns:
        Decimal金额

    Example:
        >>> parse_amount("$1,234.56")
        Decimal('1234.56')
        >>> parse_amount("-1,234.56")
        Decimal('-1234.56')
    """
    if not value_str:
        return Decimal('0.00')

    # 去除常见符号
    cleaned = str(value_str).strip()
    cleaned = cleaned.replace('$', '').replace('美元', '').replace(',', '').replace(' ', '')

    # 处理空字符串
    if not cleaned or cleaned == '-' or cleaned == '':
        return Decimal('0.00')

    try:
        return Decimal(cleaned)
    except Exception as e:
        logger.warning(f"金额解析失败: '{value_str}' -> 错误: {e}, 返回0.00")
        return Decimal('0.00')


def process_section_data(section_name: str, section_data: Dict[str, str]) -> Tuple[Dict[str, Decimal], Decimal]:
    """处理板块数据，分离核心字段和计算other_total.

    Args:
        section_name: 板块名称 (sales, refund, adjustment等)
        section_data: 板块数据 {字段名: 字段值}

    Returns:
        (核心字段数据字典, other_total金额)

    Example:
        >>> data = {"产品价格": "1000", "运输": "50", "其他税款": "5"}
        >>> core, other = process_section_data("sales", data)
        >>> core
        {'product_price': Decimal('1000'), 'shipping': Decimal('50'), ...}
        >>> other
        Decimal('5')
    """
    # Step 1: 规范化所有字段名
    normalized_data = normalize_section_data(section_data)

    # Step 2: 分离核心字段和低频字段
    core_field_data = {}
    other_total = Decimal('0.00')

    for field_name, field_value in normalized_data.items():
        # 检查是否为核心字段
        if is_core_field(section_name, field_name):
            # 核心字段：获取英文名并转换金额
            english_name = get_english_field_name(section_name, field_name)
            if english_name:
                core_field_data[english_name] = parse_amount(field_value)
            else:
                logger.warning(
                    f"[{section_name}] 核心字段'{field_name}'未找到英文映射，跳过"
                )
        else:
            # 低频字段：累加到other_total
            amount = parse_amount(field_value)
            other_total += amount

            # 记录未知字段（用于后续分析）
            log_unknown_field(section_name, field_name, field_value)

    return core_field_data, other_total


def fill_default_values(section_name: str, core_field_data: Dict[str, Decimal]) -> Dict[str, Decimal]:
    """为缺失的核心字段填充默认值0.00.

    Args:
        section_name: 板块名称
        core_field_data: 已有的核心字段数据

    Returns:
        填充完整的核心字段数据

    Example:
        >>> data = {'product_price': Decimal('1000')}
        >>> filled = fill_default_values('sales', data)
        >>> 'shipping' in filled
        True
        >>> filled['shipping']
        Decimal('0.00')
    """
    # 获取该板块所有核心字段
    from app.config.core_fields import FIELD_MAPPING_MAP

    field_mapping = FIELD_MAPPING_MAP.get(section_name, {})

    # 填充默认值
    filled_data = core_field_data.copy()

    for english_name in field_mapping.values():
        if english_name not in filled_data:
            filled_data[english_name] = Decimal('0.00')

    return filled_data


def prepare_section_for_database(section_name: str, section_data: Dict[str, str]) -> Dict[str, Decimal]:
    """准备板块数据用于数据库存储.

    这是主入口函数，整合所有处理步骤。

    Args:
        section_name: 板块名称
        section_data: 原始板块数据 {字段名: 字段值}

    Returns:
        数据库字段数据 {英文字段名: Decimal金额}，包含other_total

    Example:
        >>> raw_data = {
        ...     "产品价格": "1000",
        ...     "运输": "50",
        ...     "其他税款（费用）": "5"
        ... }
        >>> db_data = prepare_section_for_database("sales", raw_data)
        >>> db_data['product_price']
        Decimal('1000')
        >>> db_data['other_total']
        Decimal('5')
    """
    # Step 1: 处理数据，分离核心字段和other_total
    core_field_data, other_total = process_section_data(section_name, section_data)

    # Step 2: 填充默认值
    complete_data = fill_default_values(section_name, core_field_data)

    # Step 3: 添加other_total
    complete_data['other_total'] = other_total

    logger.info(
        f"[{section_name}] 处理完成: "
        f"{len(core_field_data)} 个核心字段, "
        f"other_total = {other_total}"
    )

    return complete_data


# ============================================================
# END OF data_processor.py
# ============================================================


if __name__ == "__main__":
    # 测试示例
    print("=" * 80)
    print("数据处理器测试")
    print("=" * 80)
    print()

    # 测试用例1: Sales板块
    print("测试1: Sales板块数据处理")
    print("-" * 80)

    test_sales_data = {
        "产品价格": "1355.89",
        "运输": "13.98",
        "WFS运输退款": "-13.98",
        "已收税净额": "92.92",
        "净佣金": "-195.44",
        "扣缴税款净额": "-91.91",
        "WFS 运输税退款": "-1.01",
        "T沃尔玛出资的节余": "0.00",
        "总计：": "1160.45",
        "其他税款（费用）": "5.00",  # 低频字段
    }

    result = prepare_section_for_database("sales", test_sales_data)

    print("核心字段:")
    for field, value in sorted(result.items()):
        if field != 'other_total':
            print(f"  {field:30} = {value}")

    print(f"\n低频字段汇总:")
    print(f"  other_total                    = {result['other_total']}")
    print()

    # 测试用例2: Adjustment板块（只有1个核心字段）
    print("测试2: Adjustment板块数据处理")
    print("-" * 80)

    test_adjustment_data = {
        "退货沃尔玛运输服务费": "-17.50",  # 低频字段
        "沃尔玛全球运输标签服务费": "-216.68",  # 核心字段
        "总计": "-234.18",  # 低频字段（不在核心列表）
    }

    result2 = prepare_section_for_database("adjustment", test_adjustment_data)

    print("核心字段:")
    for field, value in sorted(result2.items()):
        if field != 'other_total':
            print(f"  {field:30} = {value}")

    print(f"\n低频字段汇总:")
    print(f"  other_total                    = {result2['other_total']}")
    print()

    print("=" * 80)
    print("✅ 测试完成")
    print("=" * 80)
