# ============================================================
# 文件: backend/database/models.py
# 功能: 数据库ORM模型定义
# 作者: 开发团队
# 创建时间: 2025-12-18
# ============================================================

from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Text, DateTime,
    Enum, DECIMAL, Date, ForeignKey
)
from sqlalchemy.orm import relationship
from backend.database.config import Base


# ============================================================
# 1. PDF文件主表
# ============================================================
class PDFFile(Base):
    """PDF文件主表模型."""

    __tablename__ = "pdf_files"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="PDF文件ID")
    filename = Column(String(255), nullable=False, index=True, comment="PDF文件名")
    original_filename = Column(String(255), nullable=False, comment="原始文件名")
    file_path = Column(String(500), nullable=False, comment="文件存储路径")
    file_size = Column(Integer, nullable=False, comment="文件大小（字节）")
    file_hash = Column(String(64), nullable=False, index=True, comment="SHA256文件哈希")
    upload_time = Column(DateTime, nullable=False, default=datetime.now, comment="上传时间")
    process_status = Column(
        Enum('pending', 'processing', 'success', 'failed', name='process_status_enum'),
        nullable=False,
        default='pending',
        index=True,
        comment="处理状态"
    )
    process_time = Column(DateTime, nullable=True, comment="处理完成时间")
    error_message = Column(Text, nullable=True, comment="错误信息")
    validation_issues = Column(Text, nullable=True, comment="校验问题信息")
    created_at = Column(DateTime, nullable=False, default=datetime.now, comment="创建时间")
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now, comment="更新时间")

    # 关联关系
    header = relationship("StatementHeader", back_populates="pdf_file", uselist=False, cascade="all, delete-orphan")
    sales = relationship("SalesDetail", back_populates="pdf_file", uselist=False, cascade="all, delete-orphan")
    refund = relationship("RefundDetail", back_populates="pdf_file", uselist=False, cascade="all, delete-orphan")
    adjustment = relationship("AdjustmentDetail", back_populates="pdf_file", uselist=False, cascade="all, delete-orphan")
    wfs = relationship("WFSDetail", back_populates="pdf_file", uselist=False, cascade="all, delete-orphan")
    other_activity = relationship("OtherActivityDetail", back_populates="pdf_file", uselist=False, cascade="all, delete-orphan")
    footer = relationship("StatementFooter", back_populates="pdf_file", uselist=False, cascade="all, delete-orphan")
    payment = relationship("PaymentDetail", back_populates="pdf_file", uselist=False, cascade="all, delete-orphan")
    dynamic_fields = relationship("DynamicField", back_populates="pdf_file", cascade="all, delete-orphan")


# ============================================================
# 2. 对账单头部信息表
# ============================================================
class StatementHeader(Base):
    """对账单头部信息表模型."""

    __tablename__ = "statement_headers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    pdf_file_id = Column(Integer, ForeignKey('pdf_files.id', ondelete='CASCADE'), nullable=False, index=True)
    start_date = Column(Date, nullable=False, index=True, comment="对账单开始日期")
    end_date = Column(Date, nullable=False, index=True, comment="对账单结束日期")
    opening_balance = Column(DECIMAL(15, 2), nullable=False, default=0.00, comment="期初余额")
    reserve_funds = Column(DECIMAL(15, 2), nullable=False, default=0.00, comment="备用金")
    awaiting_payment = Column(DECIMAL(15, 2), nullable=False, default=0.00, comment="回款等待")
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    # 关联关系
    pdf_file = relationship("PDFFile", back_populates="header")


# ============================================================
# 3. 销售明细表
# ============================================================
class SalesDetail(Base):
    """销售明细表模型（优化版 - 基于30%阈值）."""

    __tablename__ = "sales_details"

    id = Column(Integer, primary_key=True, autoincrement=True)
    pdf_file_id = Column(Integer, ForeignKey('pdf_files.id', ondelete='CASCADE'), nullable=False, index=True)

    # 核心字段（频率 >= 30%）
    product_price = Column(DECIMAL(15, 2), nullable=False, default=0.00, comment="产品价格")
    shipping = Column(DECIMAL(15, 2), nullable=False, default=0.00, comment="运输费用")
    net_commission = Column(DECIMAL(15, 2), nullable=False, default=0.00, comment="净佣金")
    withholding_tax = Column(DECIMAL(15, 2), nullable=False, default=0.00, comment="扣缴税款净额")
    net_tax_collected = Column(DECIMAL(15, 2), nullable=False, default=0.00, comment="已收税净额")
    walmart_funded_savings = Column(DECIMAL(15, 2), nullable=False, default=0.00, comment="沃尔玛出资的节余")
    total = Column(DECIMAL(15, 2), nullable=False, default=0.00, comment="总计")
    wfs_shipping_refund = Column(DECIMAL(15, 2), nullable=False, default=0.00, comment="WFS运输退款")
    wfs_shipping_tax_refund = Column(DECIMAL(15, 2), nullable=False, default=0.00, comment="WFS运输税退款")

    # 低频字段汇总（频率 < 30%）
    other_total = Column(DECIMAL(15, 2), nullable=False, default=0.00, comment="其他合计（汇总低频字段）")

    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    # 关联关系
    pdf_file = relationship("PDFFile", back_populates="sales")


# ============================================================
# 4. 退款明细表
# ============================================================
class RefundDetail(Base):
    """退款明细表模型（优化版 - 基于30%阈值）."""

    __tablename__ = "refund_details"

    id = Column(Integer, primary_key=True, autoincrement=True)
    pdf_file_id = Column(Integer, ForeignKey('pdf_files.id', ondelete='CASCADE'), nullable=False, index=True)

    # 核心字段（频率 >= 30%）
    product_price = Column(DECIMAL(15, 2), nullable=False, default=0.00, comment="产品价格（退款）")
    commission = Column(DECIMAL(15, 2), nullable=False, default=0.00, comment="佣金")
    withholding_tax = Column(DECIMAL(15, 2), nullable=False, default=0.00, comment="扣缴税款净额")
    net_tax_collected = Column(DECIMAL(15, 2), nullable=False, default=0.00, comment="已收税净额")
    shipping = Column(DECIMAL(15, 2), nullable=False, default=0.00, comment="运输费用（退款）")
    walmart_funded_savings = Column(DECIMAL(15, 2), nullable=False, default=0.00, comment="沃尔玛出资的节余")
    total = Column(DECIMAL(15, 2), nullable=False, default=0.00, comment="总计")

    # 低频字段汇总（频率 < 30%）
    other_total = Column(DECIMAL(15, 2), nullable=False, default=0.00, comment="其他合计（汇总低频字段）")

    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    # 关联关系
    pdf_file = relationship("PDFFile", back_populates="refund")


# ============================================================
# 5. 调整明细表
# ============================================================
class AdjustmentDetail(Base):
    """调整明细表模型（优化版 - 基于30%阈值）."""

    __tablename__ = "adjustment_details"

    id = Column(Integer, primary_key=True, autoincrement=True)
    pdf_file_id = Column(Integer, ForeignKey('pdf_files.id', ondelete='CASCADE'), nullable=False, index=True)

    # 核心字段（频率 >= 30%）
    global_shipping_label_fee = Column(DECIMAL(15, 2), nullable=False, default=0.00, comment="沃尔玛全球运输标签服务费")
    total = Column(DECIMAL(15, 2), nullable=False, default=0.00, comment="总计")

    # 低频字段汇总（频率 < 30%）
    other_total = Column(DECIMAL(15, 2), nullable=False, default=0.00, comment="其他合计（汇总低频字段）")

    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    # 关联关系
    pdf_file = relationship("PDFFile", back_populates="adjustment")


# ============================================================
# 6. WFS服务明细表
# ============================================================
class WFSDetail(Base):
    """WFS服务明细表模型（优化版 - 基于30%阈值）."""

    __tablename__ = "wfs_details"

    id = Column(Integer, primary_key=True, autoincrement=True)
    pdf_file_id = Column(Integer, ForeignKey('pdf_files.id', ondelete='CASCADE'), nullable=False, index=True)

    # 核心字段（频率 >= 30%）
    wfs_fee = Column(DECIMAL(15, 2), nullable=False, default=0.00, comment="沃尔玛商品服务（WFS）费用")
    wfs_ethereum_fee = Column(DECIMAL(15, 2), nullable=False, default=0.00, comment="WFS 以太坊费")
    wfs_total_discount = Column(DECIMAL(15, 2), nullable=False, default=0.00, comment="WFS 总折扣")
    total = Column(DECIMAL(15, 2), nullable=False, default=0.00, comment="总计")

    # 低频字段汇总（频率 < 30%）
    other_total = Column(DECIMAL(15, 2), nullable=False, default=0.00, comment="其他合计（汇总低频字段）")

    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    # 关联关系
    pdf_file = relationship("PDFFile", back_populates="wfs")


# ============================================================
# 7. 其他活动明细表
# ============================================================
class OtherActivityDetail(Base):
    """其他活动明细表模型（优化版 - 基于30%阈值）."""

    __tablename__ = "other_activity_details"

    id = Column(Integer, primary_key=True, autoincrement=True)
    pdf_file_id = Column(Integer, ForeignKey('pdf_files.id', ondelete='CASCADE'), nullable=False, index=True)

    # 核心字段（频率 >= 30%）
    walmart_product_ads = Column(DECIMAL(15, 2), nullable=False, default=0.00, comment="沃尔玛产品广告费用")
    total = Column(DECIMAL(15, 2), nullable=False, default=0.00, comment="总计")

    # 低频字段汇总（频率 < 30%）
    other_total = Column(DECIMAL(15, 2), nullable=False, default=0.00, comment="其他合计（汇总低频字段）")

    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    # 关联关系
    pdf_file = relationship("PDFFile", back_populates="other_activity")


# ============================================================
# 8. 对账单尾部信息表
# ============================================================
class StatementFooter(Base):
    """对账单尾部信息表模型（优化版 - 基于30%阈值）."""

    __tablename__ = "statement_footers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    pdf_file_id = Column(Integer, ForeignKey('pdf_files.id', ondelete='CASCADE'), nullable=False, index=True)

    # 核心字段（频率 >= 30%）
    amount_paid_to_you = Column(DECIMAL(15, 2), nullable=False, default=0.00, comment="向您支付的金额")
    closing_balance = Column(DECIMAL(15, 2), nullable=False, default=0.00, comment="期末余额")

    # 低频字段汇总（频率 < 30%）
    other_total = Column(DECIMAL(15, 2), nullable=False, default=0.00, comment="其他合计（汇总低频字段）")

    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    # 关联关系
    pdf_file = relationship("PDFFile", back_populates="footer")


# ============================================================
# 9. 付款详情表
# ============================================================
class PaymentDetail(Base):
    """付款详情表模型（优化版 - 基于30%阈值）."""

    __tablename__ = "payment_details"

    id = Column(Integer, primary_key=True, autoincrement=True)
    pdf_file_id = Column(Integer, ForeignKey('pdf_files.id', ondelete='CASCADE'), nullable=False, index=True)

    # 核心字段（频率 >= 30%）
    status = Column(String(50), nullable=False, default='', comment="付款状态")
    payment_date = Column(Date, nullable=True, index=True, comment="付款日期")
    payment_method = Column(String(100), nullable=False, default='', comment="付款方式")
    amount_to_be_paid = Column(DECIMAL(15, 2), nullable=False, default=0.00, comment="待付款金额")
    return_waiting_period = Column(String(50), nullable=False, default='', comment="回款等待期")
    payment_frequency = Column(String(50), nullable=False, default='', comment="周期付款")
    device_method = Column(String(100), nullable=False, default='', comment="设备方式")

    # 低频字段（直接保留为独立列，因为Payment板块低频字段不多）
    amount_waiting_return = Column(DECIMAL(15, 2), nullable=False, default=0.00, comment="等待回款金额")
    warning_message = Column(Text, nullable=True, comment="警告信息")

    # 低频字段汇总（预留，用于未来扩展）
    other_total = Column(DECIMAL(15, 2), nullable=False, default=0.00, comment="其他合计（汇总低频字段）")

    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    # 关联关系
    pdf_file = relationship("PDFFile", back_populates="payment")


# ============================================================
# 10. 动态字段扩展表
# ============================================================
class DynamicField(Base):
    """动态字段扩展表模型（用于存储不规则字段）."""

    __tablename__ = "dynamic_fields"

    id = Column(Integer, primary_key=True, autoincrement=True)
    pdf_file_id = Column(Integer, ForeignKey('pdf_files.id', ondelete='CASCADE'), nullable=False, index=True)
    section_type = Column(
        Enum('sales', 'refund', 'adjustment', 'wfs', 'other', 'footer', name='section_type_enum'),
        nullable=False,
        index=True,
        comment="板块类型"
    )
    field_name = Column(String(255), nullable=False, index=True, comment="字段名称")
    field_value = Column(String(500), nullable=False, comment="字段值")
    created_at = Column(DateTime, nullable=False, default=datetime.now)

    # 关联关系
    pdf_file = relationship("PDFFile", back_populates="dynamic_fields")


# ============================================================
# 2. V2 Schema - 简化的核心表结构
# ============================================================

class Statement(Base):
    """财务报表主表（V2）"""
    __tablename__ = "statements"
    
    id = Column(Integer, primary_key=True, comment="报表ID")
    pdf_name = Column(String(255), nullable=False, unique=True, index=True, comment="PDF文件名")
    statement_period = Column(String(255), comment="统计期间")
    payment_to_you = Column(String(255), comment="向您支付的金额")
    opening_balance = Column(String(255), comment="期初余额")
    reserve_fund = Column(String(255), comment="备用金")
    pending_payment = Column(String(255), comment="回款等待")
    created_at = Column(DateTime, nullable=True, default=datetime.now, comment="创建时间")
    updated_at = Column(DateTime, nullable=True, default=datetime.now, comment="更新时间")
    
    # 关联关系
    section_data = relationship("SectionData", back_populates="statement", cascade="all, delete-orphan")


class SectionData(Base):
    """板块数据表（V2）"""
    __tablename__ = "section_data"
    
    id = Column(Integer, primary_key=True, comment="板块ID")
    statement_id = Column(Integer, ForeignKey("statements.id", ondelete="CASCADE"), nullable=False, index=True, comment="报表ID")
    section_name = Column(String(100), nullable=False, index=True, comment="板块名称（header/sales/refund/adjustment/wfs/other/footer/payment等）")
    data = Column(Text, nullable=False, comment="板块数据（JSON格式）")
    created_at = Column(DateTime, nullable=True, default=datetime.now, comment="创建时间")
    updated_at = Column(DateTime, nullable=True, default=datetime.now, comment="更新时间")
    
    # 关联关系
    statement = relationship("Statement", back_populates="section_data")


# ============================================================
# END OF models.py
# ============================================================
