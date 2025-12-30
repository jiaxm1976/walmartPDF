# ============================================================
# 文件: backend/app/schemas/pdf_file.py
# 功能: PDF文件相关的Pydantic schemas
# 作者: 开发团队
# 创建时间: 2025-12-18
# ============================================================

from datetime import datetime, date
from typing import Optional, List, Dict, Any, TYPE_CHECKING
from decimal import Decimal
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    pass


# ============================================================
# 1. PDF文件schemas
# ============================================================

class PDFFileBase(BaseModel):
    """PDF文件基础模型."""
    filename: str = Field(..., description="PDF文件名")
    original_filename: str = Field(..., description="原始文件名")


class PDFFileCreate(PDFFileBase):
    """创建PDF文件时的请求模型."""
    file_path: str = Field(..., description="文件存储路径")
    file_size: int = Field(..., description="文件大小（字节）")
    file_hash: str = Field(..., description="SHA256文件哈希")


class PDFFileUpdate(BaseModel):
    """更新PDF文件状态的请求模型."""
    process_status: Optional[str] = Field(None, description="处理状态")
    error_message: Optional[str] = Field(None, description="错误信息")


class PDFFileResponse(PDFFileBase):
    """PDF文件响应模型."""
    id: int
    file_path: str
    file_size: int
    file_hash: str
    upload_time: datetime
    process_status: str
    process_time: Optional[datetime]
    error_message: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True  # Pydantic v2 使用 from_attributes 替代 orm_mode


# ============================================================
# 2. 对账单头部schemas
# ============================================================

class StatementHeaderBase(BaseModel):
    """对账单头部基础模型."""
    start_date: date = Field(..., description="对账单开始日期")
    end_date: date = Field(..., description="对账单结束日期")
    opening_balance: Decimal = Field(default=0.00, description="期初余额")
    reserve_funds: Decimal = Field(default=0.00, description="备用金")
    awaiting_payment: Decimal = Field(default=0.00, description="回款等待")


class StatementHeaderCreate(StatementHeaderBase):
    """创建对账单头部的请求模型."""
    pdf_file_id: int


class StatementHeaderUpdate(BaseModel):
    """更新对账单头部的请求模型."""
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    opening_balance: Optional[Decimal] = None
    reserve_funds: Optional[Decimal] = None
    awaiting_payment: Optional[Decimal] = None


class StatementHeaderResponse(StatementHeaderBase):
    """对账单头部响应模型."""
    id: int
    pdf_file_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================
# 3. 销售明细schemas
# ============================================================

class SalesDetailBase(BaseModel):
    """销售明细基础模型."""
    product_price: Decimal = Field(default=0.00, description="产品价格")
    shipping: Decimal = Field(default=0.00, description="运输费用")
    wfs_shipping_refund: Decimal = Field(default=0.00, description="WFS运输退款")
    net_tax_collected: Decimal = Field(default=0.00, description="已收税净额")
    net_commission: Decimal = Field(default=0.00, description="净佣金")
    withholding_tax: Decimal = Field(default=0.00, description="扣缴税款")
    wfs_shipping_tax_refund: Decimal = Field(default=0.00, description="WFS运输税退款")
    walmart_funded_savings: Decimal = Field(default=0.00, description="沃尔玛出资的节余")
    total: Decimal = Field(default=0.00, description="总计")
    other_total: Decimal = Field(default=0.00, description="其他合计（汇总低频字段）")


class SalesDetailCreate(SalesDetailBase):
    """创建销售明细的请求模型."""
    pdf_file_id: int


class SalesDetailUpdate(BaseModel):
    """更新销售明细的请求模型."""
    product_price: Optional[Decimal] = None
    shipping: Optional[Decimal] = None
    wfs_shipping_refund: Optional[Decimal] = None
    net_tax_collected: Optional[Decimal] = None
    net_commission: Optional[Decimal] = None
    withholding_tax: Optional[Decimal] = None
    wfs_shipping_tax_refund: Optional[Decimal] = None
    walmart_funded_savings: Optional[Decimal] = None
    total: Optional[Decimal] = None
    other_total: Optional[Decimal] = None


class SalesDetailResponse(SalesDetailBase):
    """销售明细响应模型."""
    id: int
    pdf_file_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================
# 4. 退款明细schemas
# ============================================================

class RefundDetailBase(BaseModel):
    """退款明细基础模型."""
    product_price: Decimal = Field(default=0.00, description="产品价格（退款）")
    shipping: Decimal = Field(default=0.00, description="运输费用（退款）")
    net_tax_collected: Decimal = Field(default=0.00, description="已收税净额")
    commission: Decimal = Field(default=0.00, description="佣金")
    withholding_tax: Decimal = Field(default=0.00, description="扣缴税款")
    walmart_funded_savings: Decimal = Field(default=0.00, description="沃尔玛出资的节余")
    total: Decimal = Field(default=0.00, description="总计")
    other_total: Decimal = Field(default=0.00, description="其他合计（汇总低频字段）")


class RefundDetailCreate(RefundDetailBase):
    """创建退款明细的请求模型."""
    pdf_file_id: int


class RefundDetailUpdate(BaseModel):
    """更新退款明细的请求模型."""
    product_price: Optional[Decimal] = None
    shipping: Optional[Decimal] = None
    net_tax_collected: Optional[Decimal] = None
    commission: Optional[Decimal] = None
    withholding_tax: Optional[Decimal] = None
    walmart_funded_savings: Optional[Decimal] = None
    total: Optional[Decimal] = None
    other_total: Optional[Decimal] = None


class RefundDetailResponse(RefundDetailBase):
    """退款明细响应模型."""
    id: int
    pdf_file_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================
# 5. 调整明细schemas
# ============================================================

class AdjustmentDetailBase(BaseModel):
    """调整明细基础模型."""
    global_shipping_label_fee: Decimal = Field(default=0.00, description="沃尔玛全球运输标签服务费")
    other_total: Decimal = Field(default=0.00, description="其他合计（汇总低频字段）")


class AdjustmentDetailCreate(AdjustmentDetailBase):
    """创建调整明细的请求模型."""
    pdf_file_id: int


class AdjustmentDetailUpdate(BaseModel):
    """更新调整明细的请求模型."""
    global_shipping_label_fee: Optional[Decimal] = None
    other_total: Optional[Decimal] = None


class AdjustmentDetailResponse(AdjustmentDetailBase):
    """调整明细响应模型."""
    id: int
    pdf_file_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================
# 6. WFS明细schemas
# ============================================================

class WFSDetailBase(BaseModel):
    """WFS明细基础模型."""
    wfs_fee: Decimal = Field(default=0.00, description="沃尔玛商品服务（WFS）费用")
    wfs_ethereum_fee: Decimal = Field(default=0.00, description="WFS以太坊费")
    wfs_total_discount: Decimal = Field(default=0.00, description="WFS总折扣")
    total: Decimal = Field(default=0.00, description="总计")
    other_total: Decimal = Field(default=0.00, description="其他合计（汇总低频字段）")


class WFSDetailCreate(WFSDetailBase):
    """创建WFS明细的请求模型."""
    pdf_file_id: int


class WFSDetailUpdate(BaseModel):
    """更新WFS明细的请求模型."""
    wfs_fee: Optional[Decimal] = None
    wfs_ethereum_fee: Optional[Decimal] = None
    wfs_total_discount: Optional[Decimal] = None
    total: Optional[Decimal] = None
    other_total: Optional[Decimal] = None


class WFSDetailResponse(WFSDetailBase):
    """WFS明细响应模型."""
    id: int
    pdf_file_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================
# 7. 其他活动明细schemas
# ============================================================

class OtherActivityDetailBase(BaseModel):
    """其他活动明细基础模型."""
    walmart_product_ads: Decimal = Field(default=0.00, description="沃尔玛产品广告费用")
    total: Decimal = Field(default=0.00, description="总计")
    other_total: Decimal = Field(default=0.00, description="其他合计（汇总低频字段）")


class OtherActivityDetailCreate(OtherActivityDetailBase):
    """创建其他活动明细的请求模型."""
    pdf_file_id: int


class OtherActivityDetailUpdate(BaseModel):
    """更新其他活动明细的请求模型."""
    walmart_product_ads: Optional[Decimal] = None
    total: Optional[Decimal] = None
    other_total: Optional[Decimal] = None


class OtherActivityDetailResponse(OtherActivityDetailBase):
    """其他活动明细响应模型."""
    id: int
    pdf_file_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================
# 8. 对账单尾部schemas
# ============================================================

class StatementFooterBase(BaseModel):
    """对账单尾部基础模型."""
    amount_paid_to_you: Decimal = Field(default=0.00, description="向您支付的金额")
    closing_balance: Decimal = Field(default=0.00, description="期末余额")
    other_total: Decimal = Field(default=0.00, description="其他合计（汇总低频字段）")


class StatementFooterCreate(StatementFooterBase):
    """创建对账单尾部的请求模型."""
    pdf_file_id: int


class StatementFooterUpdate(BaseModel):
    """更新对账单尾部的请求模型."""
    amount_paid_to_you: Optional[Decimal] = None
    closing_balance: Optional[Decimal] = None
    other_total: Optional[Decimal] = None


class StatementFooterResponse(StatementFooterBase):
    """对账单尾部响应模型."""
    id: int
    pdf_file_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================
# 9. 付款详情schemas
# ============================================================

class PaymentDetailBase(BaseModel):
    """付款详情基础模型."""
    status: str = Field(default="", description="付款状态")
    payment_date: Optional[date] = Field(None, description="付款日期")
    payment_frequency: str = Field(default="", description="周期付款")
    payment_method: str = Field(default="", description="付款方式")
    device_method: str = Field(default="", description="设备方式")
    amount_to_be_paid: Decimal = Field(default=0.00, description="待付款金额")
    amount_waiting_return: Decimal = Field(default=0.00, description="等待回款金额")
    return_waiting_period: str = Field(default="", description="回款等待期")
    warning_message: Optional[str] = Field(None, description="警告信息")


class PaymentDetailCreate(PaymentDetailBase):
    """创建付款详情的请求模型."""
    pdf_file_id: int


class PaymentDetailUpdate(BaseModel):
    """更新付款详情的请求模型."""
    status: Optional[str] = None
    payment_date: Optional[date] = None
    payment_frequency: Optional[str] = None
    payment_method: Optional[str] = None
    device_method: Optional[str] = None
    amount_to_be_paid: Optional[Decimal] = None
    amount_waiting_return: Optional[Decimal] = None
    return_waiting_period: Optional[str] = None
    warning_message: Optional[str] = None


class PaymentDetailResponse(PaymentDetailBase):
    """付款详情响应模型."""
    id: int
    pdf_file_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================
# 10. 完整对账单数据schemas（用于数据检查和修改）
# ============================================================

class StatementDataResponse(BaseModel):
    """完整对账单数据响应模型（用于数据检查和修改）."""
    pdf_file: PDFFileResponse
    header: Optional[StatementHeaderResponse] = None
    sales: Optional[SalesDetailResponse] = None
    refund: Optional[RefundDetailResponse] = None
    adjustment: Optional[AdjustmentDetailResponse] = None
    wfs: Optional[WFSDetailResponse] = None
    other_activity: Optional[OtherActivityDetailResponse] = None
    footer: Optional[StatementFooterResponse] = None
    payment: Optional[PaymentDetailResponse] = None

    class Config:
        from_attributes = True


class StatementDataUpdate(BaseModel):
    """完整对账单数据更新请求模型."""
    header: Optional[StatementHeaderUpdate] = None
    sales: Optional[SalesDetailUpdate] = None
    refund: Optional[RefundDetailUpdate] = None
    adjustment: Optional[AdjustmentDetailUpdate] = None
    wfs: Optional[WFSDetailUpdate] = None
    other_activity: Optional[OtherActivityDetailUpdate] = None
    footer: Optional[StatementFooterUpdate] = None
    payment: Optional[PaymentDetailUpdate] = None


# ============================================================
# 11. 通用响应schemas
# ============================================================

class MessageResponse(BaseModel):
    """通用消息响应."""
    message: str
    detail: Optional[str] = None


class PaginationParams(BaseModel):
    """分页参数."""
    page: int = Field(default=1, ge=1, description="页码")
    page_size: int = Field(default=10, ge=1, le=100, description="每页数量")


class PaginatedResponse(BaseModel):
    """分页响应."""
    total: int = Field(..., description="总记录数")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页数量")
    total_pages: int = Field(..., description="总页数")
    items: List[Any] = Field(..., description="数据列表")


# ============================================================
# END OF pdf_file.py
# ============================================================
