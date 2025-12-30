# ============================================================
# 文件: backend/app/services/analytics_service.py
# 功能: 数据分析业务逻辑服务
# 作者: 开发团队
# 创建时间: 2025-12-20
# ============================================================

from typing import List, Dict, Any
from datetime import date, datetime, timedelta
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


class AnalyticsService:
    """数据分析服务，提供4类分析功能"""

    # ========== 1. 汇总统计 ==========

    @staticmethod
    def calculate_aggregated_metrics(
        statements: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """计算汇总指标.

        Args:
            statements: 对账单数据列表

        Returns:
            Dict: 包含以下指标的字典
                - total_sales: 总销售额
                - total_refund: 总退款额
                - total_commission: 总佣金
                - total_wfs_fee: 总WFS费用
                - total_ads_cost: 总广告费用
                - net_revenue: 净收入
                - statement_count: 对账单数量
                - period_days: 周期天数
        """
        if not statements:
            return {
                "total_sales": Decimal(0),
                "total_refund": Decimal(0),
                "total_commission": Decimal(0),
                "total_wfs_fee": Decimal(0),
                "total_ads_cost": Decimal(0),
                "net_revenue": Decimal(0),
                "statement_count": 0,
                "period_days": 0,
            }

        total_sales = Decimal(0)
        total_refund = Decimal(0)
        total_commission = Decimal(0)
        total_wfs_fee = Decimal(0)
        total_ads_cost = Decimal(0)
        min_start_date = None
        max_end_date = None

        for stmt in statements:
            header = stmt.get("header")
            sales = stmt.get("sales")
            refund = stmt.get("refund")
            wfs = stmt.get("wfs")
            other_activity = stmt.get("other_activity")

            # 汇总各项金额
            if sales and sales.total:
                total_sales += Decimal(str(sales.total))
            if sales and sales.net_commission:
                total_commission += Decimal(str(sales.net_commission))

            if refund and refund.total:
                total_refund += Decimal(str(refund.total))

            if wfs and wfs.total:
                total_wfs_fee += Decimal(str(wfs.total))

            if other_activity and other_activity.walmart_product_ads:
                total_ads_cost += Decimal(str(other_activity.walmart_product_ads))

            # 记录日期范围
            if header:
                if min_start_date is None or header.start_date < min_start_date:
                    min_start_date = header.start_date
                if max_end_date is None or header.end_date > max_end_date:
                    max_end_date = header.end_date

        # 计算净收入
        net_revenue = total_sales + total_refund + total_commission + total_wfs_fee + total_ads_cost

        # 计算周期天数
        period_days = 0
        if min_start_date and max_end_date:
            period_days = (max_end_date - min_start_date).days + 1

        return {
            "total_sales": total_sales,
            "total_refund": total_refund,
            "total_commission": total_commission,
            "total_wfs_fee": total_wfs_fee,
            "total_ads_cost": total_ads_cost,
            "net_revenue": net_revenue,
            "statement_count": len(statements),
            "period_days": period_days,
        }

    # ========== 2. 趋势分析 ==========

    @staticmethod
    def calculate_trend_analysis(
        statements_grouped: Dict[str, List[Dict[str, Any]]],
        granularity: str
    ) -> List[Dict[str, Any]]:
        """计算趋势分析数据.

        Args:
            statements_grouped: 按时期分组的对账单数据
            granularity: 时间粒度 (monthly|weekly|statement)

        Returns:
            List: 时间序列数据列表
        """
        time_series = []

        for period_label in sorted(statements_grouped.keys()):
            period_statements = statements_grouped[period_label]

            # 获取该周期的日期范围
            start_date = None
            end_date = None
            for stmt in period_statements:
                header = stmt.get("header")
                if header:
                    if start_date is None or header.start_date < start_date:
                        start_date = header.start_date
                    if end_date is None or header.end_date > end_date:
                        end_date = header.end_date

            # 计算该周期的汇总指标
            metrics = AnalyticsService.calculate_aggregated_metrics(period_statements)

            period_data = {
                "period_label": period_label,
                "start_date": start_date,
                "end_date": end_date,
                "metrics": metrics,
            }
            time_series.append(period_data)

        return time_series

    # ========== 3. 对比分析 ==========

    @staticmethod
    def calculate_comparison(
        period1_statements: List[Dict[str, Any]],
        period2_statements: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """计算两期对比.

        Args:
            period1_statements: 第一期对账单列表
            period2_statements: 第二期对账单列表

        Returns:
            Dict: 对比结果，包括两期指标和变化量
        """
        metrics1 = AnalyticsService.calculate_aggregated_metrics(period1_statements)
        metrics2 = AnalyticsService.calculate_aggregated_metrics(period2_statements)

        # 计算变化量
        changes = {}
        metric_keys = [
            "total_sales",
            "total_refund",
            "total_commission",
            "total_wfs_fee",
            "total_ads_cost",
            "net_revenue",
        ]

        for key in metric_keys:
            val1 = metrics1.get(key, Decimal(0))
            val2 = metrics2.get(key, Decimal(0))

            absolute_change = val2 - val1
            percentage_change = Decimal(0)

            # 避免除零
            if val1 != 0:
                percentage_change = (absolute_change / abs(val1) * Decimal(100)).quantize(
                    Decimal("0.01")
                )

            changes[key] = {
                "absolute": absolute_change,
                "percentage": percentage_change,
            }

        return {
            "period1": metrics1,
            "period2": metrics2,
            "changes": changes,
        }

    # ========== 4. 异常检测 ==========

    @staticmethod
    def detect_anomalies(statements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """检测异常数据.

        检测规则:
        - 退款率异常: refund_total / sales_total > 20%
        - 净收入为负: net_revenue < 0
        - 佣金率异常: commission / sales > 20%
        - WFS费用占比异常: wfs_fee / sales > 10%
        - 广告费用占比异常: ads_cost / sales > 15%

        Args:
            statements: 对账单数据列表

        Returns:
            List: 异常项列表
        """
        anomalies = []

        for stmt in statements:
            header = stmt.get("header")
            sales = stmt.get("sales")
            refund = stmt.get("refund")
            wfs = stmt.get("wfs")
            other_activity = stmt.get("other_activity")
            pdf_file = stmt.get("pdf_file")

            if not header or not pdf_file:
                continue

            statement_period = f"{header.start_date.strftime('%Y-%m-%d')} 至 {header.end_date.strftime('%Y-%m-%d')}"
            pdf_id = pdf_file.id

            # 计算销售总额
            sales_total = Decimal(str(sales.total)) if sales and sales.total else Decimal(0)

            # 1. 检测退款率异常
            if refund and refund.total and sales_total > 0:
                refund_total = abs(Decimal(str(refund.total)))
                refund_rate = (refund_total / sales_total * Decimal(100)).quantize(Decimal("0.01"))

                if refund_rate > Decimal(20):
                    severity = AnalyticsService._get_severity(refund_rate, Decimal(20), Decimal(50))
                    anomalies.append({
                        "pdf_id": pdf_id,
                        "statement_period": statement_period,
                        "anomaly_type": "high_refund_rate",
                        "metric_name": "退款率",
                        "metric_value": refund_rate,
                        "threshold": Decimal(20),
                        "severity": severity,
                        "message": f"退款率 {refund_rate}% 超过阈值 20%",
                    })

            # 2. 检测净收入为负
            net_revenue = AnalyticsService._calculate_net_revenue(stmt)
            if net_revenue < 0:
                anomalies.append({
                    "pdf_id": pdf_id,
                    "statement_period": statement_period,
                    "anomaly_type": "negative_revenue",
                    "metric_name": "净收入",
                    "metric_value": net_revenue,
                    "threshold": Decimal(0),
                    "severity": "high",
                    "message": f"净收入为负: {net_revenue}",
                })

            # 3. 检测佣金率异常
            if sales and sales.net_commission and sales_total > 0:
                commission_rate = (abs(Decimal(str(sales.net_commission))) / sales_total * Decimal(100)).quantize(
                    Decimal("0.01")
                )

                if commission_rate > Decimal(20):
                    severity = AnalyticsService._get_severity(commission_rate, Decimal(20), Decimal(50))
                    anomalies.append({
                        "pdf_id": pdf_id,
                        "statement_period": statement_period,
                        "anomaly_type": "high_commission_rate",
                        "metric_name": "佣金率",
                        "metric_value": commission_rate,
                        "threshold": Decimal(20),
                        "severity": severity,
                        "message": f"佣金率 {commission_rate}% 超过阈值 20%",
                    })

            # 4. 检测WFS费用占比异常
            if wfs and wfs.total and sales_total > 0:
                wfs_rate = (abs(Decimal(str(wfs.total))) / sales_total * Decimal(100)).quantize(Decimal("0.01"))

                if wfs_rate > Decimal(10):
                    severity = AnalyticsService._get_severity(wfs_rate, Decimal(10), Decimal(30))
                    anomalies.append({
                        "pdf_id": pdf_id,
                        "statement_period": statement_period,
                        "anomaly_type": "high_wfs_fee_rate",
                        "metric_name": "WFS费用占比",
                        "metric_value": wfs_rate,
                        "threshold": Decimal(10),
                        "severity": severity,
                        "message": f"WFS费用占比 {wfs_rate}% 超过阈值 10%",
                    })

            # 5. 检测广告费用占比异常
            if other_activity and other_activity.walmart_product_ads and sales_total > 0:
                ads_rate = (abs(Decimal(str(other_activity.walmart_product_ads))) / sales_total * Decimal(100)).quantize(
                    Decimal("0.01")
                )

                if ads_rate > Decimal(15):
                    severity = AnalyticsService._get_severity(ads_rate, Decimal(15), Decimal(40))
                    anomalies.append({
                        "pdf_id": pdf_id,
                        "statement_period": statement_period,
                        "anomaly_type": "high_ads_cost_rate",
                        "metric_name": "广告费用占比",
                        "metric_value": ads_rate,
                        "threshold": Decimal(15),
                        "severity": severity,
                        "message": f"广告费用占比 {ads_rate}% 超过阈值 15%",
                    })

        logger.info(f"检测异常: 共检测 {len(statements)} 条对账单，发现 {len(anomalies)} 个异常")
        return anomalies

    # ========== 辅助方法 ==========

    @staticmethod
    def _calculate_net_revenue(statement: Dict[str, Any]) -> Decimal:
        """计算净收入.

        净收入 = 销售总额 + 退款总额 + 佣金 + WFS费用 + 广告费用
        """
        sales = statement.get("sales")
        refund = statement.get("refund")
        wfs = statement.get("wfs")
        other_activity = statement.get("other_activity")

        total = Decimal(0)

        if sales and sales.total:
            total += Decimal(str(sales.total))
        if sales and sales.net_commission:
            total += Decimal(str(sales.net_commission))

        if refund and refund.total:
            total += Decimal(str(refund.total))

        if wfs and wfs.total:
            total += Decimal(str(wfs.total))

        if other_activity and other_activity.walmart_product_ads:
            total += Decimal(str(other_activity.walmart_product_ads))

        return total

    @staticmethod
    def _get_severity(value: Decimal, low_threshold: Decimal, high_threshold: Decimal) -> str:
        """根据偏差程度确定严重程度.

        Args:
            value: 实际值
            low_threshold: 低阈值
            high_threshold: 高阈值

        Returns:
            str: 严重程度 (low|medium|high)
        """
        if value > high_threshold:
            return "high"
        elif value > low_threshold:
            return "medium"
        else:
            return "low"


# ============================================================
# END OF analytics_service.py
# ============================================================
