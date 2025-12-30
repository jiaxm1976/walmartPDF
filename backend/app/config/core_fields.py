# ============================================================
# 文件: backend/app/config/core_fields.py
# 功能: 核心字段配置（基于30%阈值分析结果）
# 作者: 开发团队
# 创建时间: 2025-12-19
# 说明: 定义每个板块的核心字段列表和中英文映射
# ============================================================

from typing import Dict, List, Set


# ============================================================
# 核心字段列表（基于30%阈值，出现频率 >= 30%）
# ============================================================

# Header板块核心字段（注意：实际出现率100%，显示33.3%是因为测试重复）
HEADER_CORE_FIELDS = [
    '开始日期',
    '结束日期',
    '期初余额',
    '备用金',
    '回款等待',
]

# Sales板块核心字段
SALES_CORE_FIELDS = [
    '产品价格',          # 100%
    '运输',              # 100%
    '净佣金',            # 100%
    '扣缴税款净额',      # 100%
    '已收税净额',        # 88.9%
    'T沃尔玛出资的节余',  # 83.3%
    '总计',              # 77.8%
    'WFS 运输退款',      # 72.2%
    'WFS 运输税退款',    # 61.1%
]

# Refund板块核心字段
REFUND_CORE_FIELDS = [
    '产品价格',          # 100%
    '佣金',              # 100%
    '扣缴税款净额',      # 83.3%
    '已收税净额',        # 77.8%
    '运输',              # 66.7%
    'T沃尔玛出资的节余',  # 61.1%
    '总计',              # 50.0%
]

# Adjustment板块核心字段
ADJUSTMENT_CORE_FIELDS = [
    '沃尔玛全球运输标签服务费',  # 50.0%
    '总计',                      # 调整明细板块总计
]

# WFS板块核心字段
WFS_CORE_FIELDS = [
    '沃尔玛商品服务(WFS)',  # 83.3% - 注意：括号规范化为半角
    '总计',                 # 83.3%
    'WFS 以太坊费',         # 61.1%
    'WFS 总折扣',           # 55.6%
]

# Other Activity板块核心字段
OTHER_CORE_FIELDS = [
    '沃尔玛产品广告',    # 83.3%
    '总计',              # 77.8%
]

# Footer板块核心字段
FOOTER_CORE_FIELDS = [
    '向您支付的金额',    # 100%
    '期末余额',          # 100%
]

# Payment板块核心字段
PAYMENT_CORE_FIELDS = [
    '状态',              # 100%
    '付款日期',          # 100%
    '付款方式',          # 100%
    '待付款金额',        # 100%
    '回款等待期',        # 100%
    '周期付款',          # 83.3%
    '设备方式',          # 83.3%
]


# ============================================================
# 中英文字段映射表
# ============================================================

# Header板块字段映射
HEADER_FIELD_MAPPING = {
    '开始日期': 'start_date',
    '结束日期': 'end_date',
    '期初余额': 'opening_balance',
    '备用金': 'reserve_funds',
    '回款等待': 'awaiting_payment',
}

# Sales板块字段映射
SALES_FIELD_MAPPING = {
    '产品价格': 'product_price',
    '运输': 'shipping',
    '净佣金': 'net_commission',
    '扣缴税款净额': 'withholding_tax',
    '已收税净额': 'net_tax_collected',
    'T沃尔玛出资的节余': 'walmart_funded_savings',
    '总计': 'total',
    'WFS 运输退款': 'wfs_shipping_refund',
    'WFS 运输税退款': 'wfs_shipping_tax_refund',
}

# Refund板块字段映射
REFUND_FIELD_MAPPING = {
    '产品价格': 'product_price',
    '佣金': 'commission',
    '扣缴税款净额': 'withholding_tax',
    '已收税净额': 'net_tax_collected',
    '运输': 'shipping',
    'T沃尔玛出资的节余': 'walmart_funded_savings',
    '总计': 'total',
}

# Adjustment板块字段映射
ADJUSTMENT_FIELD_MAPPING = {
    '沃尔玛全球运输标签服务费': 'global_shipping_label_fee',
    '总计': 'total',
}

# WFS板块字段映射
WFS_FIELD_MAPPING = {
    '沃尔玛商品服务(WFS)': 'wfs_fee',
    'WFS 以太坊费': 'wfs_ethereum_fee',
    'WFS 总折扣': 'wfs_total_discount',
    '总计': 'total',
}

# Other Activity板块字段映射
OTHER_FIELD_MAPPING = {
    '沃尔玛产品广告': 'walmart_product_ads',
    '总计': 'total',
}

# Footer板块字段映射
FOOTER_FIELD_MAPPING = {
    '向您支付的金额': 'amount_paid_to_you',
    '期末余额': 'closing_balance',
}

# Payment板块字段映射
PAYMENT_FIELD_MAPPING = {
    '状态': 'status',
    '付款日期': 'payment_date',
    '付款方式': 'payment_method',
    '待付款金额': 'amount_to_be_paid',
    '回款等待期': 'return_waiting_period',
    '周期付款': 'payment_frequency',
    '设备方式': 'device_method',
}


# ============================================================
# 汇总配置
# ============================================================

# 所有板块的核心字段集合
CORE_FIELDS_MAP: Dict[str, Set[str]] = {
    'header': set(HEADER_CORE_FIELDS),
    'sales': set(SALES_CORE_FIELDS),
    'refund': set(REFUND_CORE_FIELDS),
    'adjustment': set(ADJUSTMENT_CORE_FIELDS),
    'wfs': set(WFS_CORE_FIELDS),
    'other': set(OTHER_CORE_FIELDS),
    'footer': set(FOOTER_CORE_FIELDS),
    'payment_details': set(PAYMENT_CORE_FIELDS),
}

# 所有板块的字段映射
FIELD_MAPPING_MAP: Dict[str, Dict[str, str]] = {
    'header': HEADER_FIELD_MAPPING,
    'sales': SALES_FIELD_MAPPING,
    'refund': REFUND_FIELD_MAPPING,
    'adjustment': ADJUSTMENT_FIELD_MAPPING,
    'wfs': WFS_FIELD_MAPPING,
    'other': OTHER_FIELD_MAPPING,
    'footer': FOOTER_FIELD_MAPPING,
    'payment_details': PAYMENT_FIELD_MAPPING,
}


# ============================================================
# 辅助函数
# ============================================================

def is_core_field(section_name: str, field_name: str) -> bool:
    """判断字段是否为核心字段.

    Args:
        section_name: 板块名称
        field_name: 字段名（已规范化）

    Returns:
        True表示核心字段，False表示低频字段

    Example:
        >>> is_core_field('sales', '产品价格')
        True
        >>> is_core_field('sales', '其他税款')
        False
    """
    core_fields = CORE_FIELDS_MAP.get(section_name, set())
    return field_name in core_fields


def get_english_field_name(section_name: str, chinese_field_name: str) -> str:
    """获取字段的英文名.

    Args:
        section_name: 板块名称
        chinese_field_name: 中文字段名（已规范化）

    Returns:
        英文字段名，如果未找到则返回None

    Example:
        >>> get_english_field_name('sales', '产品价格')
        'product_price'
    """
    field_mapping = FIELD_MAPPING_MAP.get(section_name, {})
    return field_mapping.get(chinese_field_name)


def get_core_fields_list(section_name: str) -> List[str]:
    """获取板块的核心字段列表.

    Args:
        section_name: 板块名称

    Returns:
        核心字段列表

    Example:
        >>> get_core_fields_list('sales')
        ['产品价格', '运输', '净佣金', ...]
    """
    return list(CORE_FIELDS_MAP.get(section_name, set()))


def get_all_sections() -> List[str]:
    """获取所有板块名称列表.

    Returns:
        板块名称列表
    """
    return list(CORE_FIELDS_MAP.keys())


# ============================================================
# 统计信息
# ============================================================

def print_statistics():
    """打印核心字段统计信息."""

    print("=" * 80)
    print("核心字段配置统计（基于30%阈值）")
    print("=" * 80)
    print()

    total_core = 0
    for section_name, core_fields in CORE_FIELDS_MAP.items():
        count = len(core_fields)
        total_core += count
        print(f"  {section_name:20} {count:3} 个核心字段")

    print()
    print("-" * 80)
    print(f"  总计:                 {total_core:3} 个核心字段")
    print("=" * 80)


# ============================================================
# END OF core_fields.py
# ============================================================


if __name__ == "__main__":
    print_statistics()
    print()

    # 测试示例
    print("=" * 80)
    print("功能测试")
    print("=" * 80)
    print()

    print("测试1: is_core_field()")
    print(f"  is_core_field('sales', '产品价格') = {is_core_field('sales', '产品价格')}")
    print(f"  is_core_field('sales', '其他税款') = {is_core_field('sales', '其他税款')}")
    print()

    print("测试2: get_english_field_name()")
    print(f"  get_english_field_name('sales', '产品价格') = {get_english_field_name('sales', '产品价格')}")
    print(f"  get_english_field_name('refund', '佣金') = {get_english_field_name('refund', '佣金')}")
    print()

    print("测试3: get_core_fields_list()")
    print(f"  get_core_fields_list('adjustment') = {get_core_fields_list('adjustment')}")
    print()
