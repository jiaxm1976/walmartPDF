# ============================================================
# 文件: backend/app/schemas/analytics.py
# 功能: 数据分析系统的Pydantic Schema定义
# 作者: 开发团队
# 创建时间: 2025-12-20
# ============================================================

from pydantic import BaseModel, Field
from datetime import date
from decimal import Decimal
from typing import Optional, List, Dict


# ========== 请求模型 ==========

class AnalyticsRequestBase(BaseModel):
    """分析请求基类"""
    start_date: date = Field(..., description="开始日期")
    end_date: date = Field(..., description="结束日期")
    granularity: str = Field(
        default="statement",
        description="时间粒度 (statement|monthly|weekly)"
    )


class TrendAnalysisRequest(AnalyticsRequestBase):
    """趋势分析请求"""
    metrics: List[str] = Field(
        default=["total_sales", "total_refund", "net_revenue"],
        description="要分析的指标"
    )


class ComparisonRequest(BaseModel):
    """对比分析请求"""
    period1_start: date = Field(..., description="第一期开始日期")
    period1_end: date = Field(..., description="第一期结束日期")
    period2_start: date = Field(..., description="第二期开始日期")
    period2_end: date = Field(..., description="第二期结束日期")
    granularity: str = Field(default="monthly", description="时间粒度")


# ========== 响应模型 ==========

class AggregatedMetrics(BaseModel):
    """汇总指标"""
    total_sales: Decimal = Field(description="总销售额")
    total_refund: Decimal = Field(description="总退款额")
    total_commission: Decimal = Field(description="总佣金")
    total_wfs_fee: Decimal = Field(description="总WFS费用")
    total_ads_cost: Decimal = Field(description="总广告费用")
    net_revenue: Decimal = Field(description="净收入")
    statement_count: int = Field(description="对账单数量")
    period_days: int = Field(description="周期天数")


class PeriodData(BaseModel):
    """单期数据"""
    period_label: str = Field(description="时期标签 (如 2024-12)")
    start_date: date = Field(description="周期开始日期")
    end_date: date = Field(description="周期结束日期")
    metrics: AggregatedMetrics = Field(description="该周期的汇总指标")


class TrendAnalysisResponse(BaseModel):
    """趋势分析响应"""
    time_series: List[PeriodData] = Field(description="时间序列数据")
    granularity: str = Field(description="时间粒度")
    total_periods: int = Field(description="总周期数")


class ComparisonResponse(BaseModel):
    """对比分析响应"""
    period1: AggregatedMetrics = Field(description="第一期指标")
    period2: AggregatedMetrics = Field(description="第二期指标")
    changes: Dict[str, Dict[str, Decimal]] = Field(
        description="变化量 {'total_sales': {'absolute': 100.00, 'percentage': 10.5}}"
    )


class AnomalyItem(BaseModel):
    """异常项"""
    pdf_id: int = Field(description="PDF文件ID")
    statement_period: str = Field(description="对账单周期")
    anomaly_type: str = Field(description="异常类型 (high_refund_rate | negative_revenue | high_commission_rate | high_wfs_fee_rate | high_ads_cost_rate)")
    metric_name: str = Field(description="指标名称")
    metric_value: Decimal = Field(description="实际值")
    threshold: Decimal = Field(description="阈值")
    severity: str = Field(description="严重程度 (low|medium|high)")
    message: str = Field(description="异常描述信息")


class AnomalyDetectionResponse(BaseModel):
    """异常检测响应"""
    total_statements: int = Field(description="检测的对账单总数")
    anomaly_count: int = Field(description="发现的异常数量")
    anomalies: List[AnomalyItem] = Field(description="异常项列表")


# ============================================================
# END OF analytics.py
# ============================================================
