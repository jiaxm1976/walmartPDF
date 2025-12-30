# ============================================================
# 文件: backend/app/config/field_aliases.py
# 功能: 字段名中英文映射（用于导出时显示中文别名）
# 作者: 开发团队
# 创建时间: 2025-12-20
# ============================================================

# 对账单头部字段别名
HEADER_ALIASES = {
    "start_date": "开始日期",
    "end_date": "结束日期",
    "opening_balance": "期初余额",
    "reserve_funds": "备用金",
    "awaiting_payment": "待结算金额",
}

# 销售明细字段别名
SALES_ALIASES = {
    "product_price": "产品价格",
    "shipping": "运输费用",
    "wfs_shipping_refund": "WFS运输退款",
    "net_tax_collected": "已收税净额",
    "net_commission": "净佣金",
    "withholding_tax": "扣缴税款净额",
    "wfs_shipping_tax_refund": "WFS运输税退款",
    "walmart_funded_savings": "沃尔玛出资的节余",
    "total": "合计",
    "other_total": "其他合计",
}

# 退款明细字段别名
REFUND_ALIASES = {
    "product_price": "产品价格（退款）",
    "shipping": "运输费用（退款）",
    "net_tax_collected": "已收税净额",
    "commission": "佣金",
    "withholding_tax": "扣缴税款净额",
    "walmart_funded_savings": "沃尔玛出资的节余",
    "total": "合计",
    "other_total": "其他合计",
}

# 调整明细字段别名
ADJUSTMENT_ALIASES = {
    "global_shipping_label_fee": "沃尔玛全球运输标签服务费",
    "other_total": "其他合计",
}

# WFS明细字段别名
WFS_ALIASES = {
    "wfs_fee": "WFS服务费用",
    "wfs_ethereum_fee": "WFS以太坊费",
    "wfs_total_discount": "WFS总折扣",
    "total": "合计",
    "other_total": "其他合计",
}

# 其他活动字段别名
OTHER_ACTIVITY_ALIASES = {
    "walmart_product_ads": "沃尔玛产品广告费用",
    "total": "合计",
    "other_total": "其他合计",
}

# 对账单尾部字段别名
FOOTER_ALIASES = {
    "amount_paid_to_you": "向您支付的金额",
    "closing_balance": "期末余额",
    "other_total": "其他合计",
}

# 付款详情字段别名
PAYMENT_ALIASES = {
    "status": "付款状态",
    "payment_date": "付款日期",
    "payment_frequency": "周期付款",
    "payment_method": "付款方式",
    "device_method": "设备方式",
    "amount_to_be_paid": "待付款金额",
    "amount_waiting_return": "等待回款金额",
    "return_waiting_period": "回款等待期",
    "warning_message": "警告信息",
}

# PDF文件信息字段别名
PDF_FILE_ALIASES = {
    "filename": "系统文件名",
    "original_filename": "原始文件名",
    "file_path": "文件路径",
    "file_size": "文件大小",
    "file_hash": "文件哈希",
    "upload_time": "上传时间",
    "process_status": "处理状态",
    "process_time": "处理完成时间",
    "error_message": "错误信息",
    "created_at": "创建时间",
    "updated_at": "更新时间",
}

# 获取字段别名的通用函数
def get_field_alias(field_name: str, section: str) -> str:
    """获取字段的中文别名.

    Args:
        field_name: 英文字段名
        section: 板块名称（header/sales/refund等）

    Returns:
        str: 中文别名，如果不存在则返回原字段名
    """
    aliases_map = {
        "header": HEADER_ALIASES,
        "sales": SALES_ALIASES,
        "refund": REFUND_ALIASES,
        "adjustment": ADJUSTMENT_ALIASES,
        "wfs": WFS_ALIASES,
        "other_activity": OTHER_ACTIVITY_ALIASES,
        "footer": FOOTER_ALIASES,
        "payment": PAYMENT_ALIASES,
        "pdf_file": PDF_FILE_ALIASES,
    }

    aliases = aliases_map.get(section, {})
    return aliases.get(field_name, field_name)


# ============================================================
# END OF field_aliases.py
# ============================================================
