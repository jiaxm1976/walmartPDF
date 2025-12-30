# Phase 4 数据分析系统 - 功能文档

> **版本**: 1.0 | **发布日期**: 2025-12-20 | **状态**: ✅ 完成

---

## 📋 目录

1. [功能概述](#功能概述)
2. [需求对标](#需求对标)
3. [分析类型](#分析类型)
4. [时间粒度](#时间粒度)
5. [异常检测](#异常检测)
6. [API使用](#api使用)
7. [测试结果](#测试结果)

---

## 功能概述

### 核心价值

Phase 4 实现完整的数据分析系统，支持对对账单数据的多角度分析：

- **汇总统计**: 快速了解整体财务状况
- **趋势分析**: 发现长期变化规律
- **对比分析**: 评估不同时期的表现差异
- **异常检测**: 自动识别异常业务情况

### 技术架构

```
CRUD层 (日期范围查询)
    ↓
Service层 (业务逻辑)
    ↓
API层 (HTTP端点)
    ↓
客户端
```

### 统计指标

8个核心指标每个分析都会输出：

| 指标 | 说明 | 计算方式 |
|-----|------|---------|
| total_sales | 总销售额 | sum(sales.total) |
| total_refund | 总退款额 | sum(refund.total) |
| total_commission | 总佣金 | sum(sales.net_commission) |
| total_wfs_fee | 总WFS费用 | sum(wfs.total) |
| total_ads_cost | 总广告费用 | sum(other_activity.walmart_product_ads) |
| net_revenue | 净收入 | 上述5项之和 |
| statement_count | 对账单数 | count(statements) |
| period_days | 周期天数 | max_date - min_date + 1 |

---

## 需求对标

### 用户需求清单

✅ **分析类型**
- [x] 汇总统计 (Aggregation)
- [x] 多期对比 (Comparison)
- [x] 趋势分析 (Trend Analysis)
- [x] 异常检测 (Anomaly Detection)

✅ **时间粒度**
- [x] 按对账单 (statement)
- [x] 按月汇总 (monthly)
- [x] 按周汇总 (weekly)
- [x] 自定义日期范围 (custom date range)

✅ **技术要求**
- [x] Decimal精度计算
- [x] 完整的单元和集成测试
- [x] 全部错误处理
- [x] API文档完善

---

## 分析类型

### 1. 汇总统计 (Aggregation)

**用途**: 快速获取指定时间范围的整体财务概览

**API**:
```bash
GET /api/v1/analytics/summary?start_date=2024-01-01&end_date=2024-12-31
```

**响应示例**:
```json
{
  "total_sales": "4107.62",
  "total_refund": "-262.70",
  "total_commission": "-1197.01",
  "total_wfs_fee": "-328.78",
  "total_ads_cost": "0",
  "net_revenue": "2319.13",
  "statement_count": 9,
  "period_days": 290
}
```

**应用场景**:
- 财务报表生成
- CEO dashboard展示
- 快速财务评估

---

### 2. 趋势分析 (Trend Analysis)

**用途**: 观察财务指标随时间的变化趋势

**API**:
```bash
GET /api/v1/analytics/trends?start_date=2024-01-01&end_date=2024-12-31&granularity=monthly
```

**时间粒度**:
- `monthly` - 按月份分组
- `weekly` - 按周份分组
- `statement` - 每个对账单独立

**响应示例** (部分):
```json
{
  "time_series": [
    {
      "period_label": "2024-12",
      "start_date": "2024-12-01",
      "end_date": "2024-12-31",
      "metrics": {
        "total_sales": "1850.00",
        "total_commission": "-405.44",
        "net_revenue": "1275.89",
        "statement_count": 3,
        "period_days": 31
      }
    }
  ],
  "granularity": "monthly",
  "total_periods": 6
}
```

**应用场景**:
- 销售趋势图表展示
- 季节性分析
- 增长率计算

---

### 3. 对比分析 (Comparison)

**用途**: 比较两个不同时间段的数据差异

**API**:
```bash
POST /api/v1/analytics/comparison
{
  "period1_start": "2024-01-01",
  "period1_end": "2024-06-30",
  "period2_start": "2024-07-01",
  "period2_end": "2024-12-31"
}
```

**响应包含**:
- 两期的完整指标
- 绝对变化值 (absolute)
- 百分比变化 (percentage)

**响应示例**:
```json
{
  "period1": { 指标 },
  "period2": { 指标 },
  "changes": {
    "total_sales": {
      "absolute": "107.62",
      "percentage": "5.38"
    },
    "net_revenue": {
      "absolute": "-780.87",
      "percentage": "-50.38"
    }
  }
}
```

**应用场景**:
- 同比分析 (YoY)
- 环比分析 (MoM)
- 季度对比
- 效果评估

---

### 4. 异常检测 (Anomaly Detection)

**用途**: 自动发现异常的业务指标

**API**:
```bash
GET /api/v1/analytics/anomalies?start_date=2024-01-01&end_date=2024-12-31&severity=high
```

**严重程度**:
- `all` - 所有异常
- `low` - 轻微异常 (10-20%偏差)
- `medium` - 中等异常 (20-50%偏差)
- `high` - 严重异常 (>50%偏差)

**响应示例**:
```json
{
  "total_statements": 9,
  "anomaly_count": 4,
  "anomalies": [
    {
      "pdf_id": 1,
      "statement_period": "2024-12-06 至 2025-01-11",
      "anomaly_type": "negative_revenue",
      "metric_name": "净收入",
      "metric_value": "-256.11",
      "threshold": "0",
      "severity": "high",
      "message": "净收入为负: -256.11"
    }
  ]
}
```

---

## 时间粒度

### 支持的时间粒度

#### 1. Statement (按对账单)
- 每个对账单作为一个独立单位
- 用于详细分析单个对账单

#### 2. Weekly (按周汇总)
- ISO标准周编号: `2024-W50`
- 适合短期趋势观察

#### 3. Monthly (按月汇总)
- 标准月份格式: `2024-12`
- 最常用的时间粒度

#### 4. Custom (自定义范围)
- 任意日期范围: `start_date` - `end_date`
- 灵活的查询方式

### 组合使用示例

```bash
# 月度趋势分析
GET /api/v1/analytics/trends?granularity=monthly

# 周度对比
POST /api/v1/analytics/comparison
{
  "granularity": "weekly"
}

# 自定义范围汇总
GET /api/v1/analytics/summary?start_date=2024-11-15&end_date=2024-12-15
```

---

## 异常检测

### 检测规则详解

#### 1. 退款率异常 (high_refund_rate)
```
条件: refund.total / sales.total > 20%
严重程度: 
  - 20-50%: 中等 (medium)
  - >50%: 严重 (high)
含义: 退款过多可能表示产品质量或客户满意度问题
```

#### 2. 负收入 (negative_revenue)
```
条件: net_revenue < 0
严重程度: 总是 high
含义: 成本和费用超过销售收入，需要立即关注
```

#### 3. 佣金率异常 (high_commission_rate)
```
条件: commission / sales > 20%
严重程度:
  - 20-50%: 中等 (medium)
  - >50%: 严重 (high)
含义: 沃尔玛佣金过高，影响利润率
```

#### 4. WFS费用异常 (high_wfs_fee_rate)
```
条件: wfs_fee / sales > 10%
严重程度:
  - 10-30%: 中等 (medium)
  - >30%: 严重 (high)
含义: WFS仓储费用过高
```

#### 5. 广告费用异常 (high_ads_cost_rate)
```
条件: ads_cost / sales > 15%
严重程度:
  - 15-40%: 中等 (medium)
  - >40%: 严重 (high)
含义: 广告投入与回报比例失衡
```

---

## API使用

### 完整的API调用流程

#### 步骤1: 获取汇总统计
```bash
curl "http://localhost:8000/api/v1/analytics/summary?start_date=2024-01-01&end_date=2024-12-31"
```

#### 步骤2: 获取月度趋势
```bash
curl "http://localhost:8000/api/v1/analytics/trends?start_date=2024-01-01&end_date=2024-12-31&granularity=monthly"
```

#### 步骤3: 对比两个半年
```bash
curl -X POST "http://localhost:8000/api/v1/analytics/comparison" \
  -H "Content-Type: application/json" \
  -d '{"period1_start":"2024-01-01","period1_end":"2024-06-30","period2_start":"2024-07-01","period2_end":"2024-12-31"}'
```

#### 步骤4: 检测异常
```bash
curl "http://localhost:8000/api/v1/analytics/anomalies?start_date=2024-01-01&end_date=2024-12-31&severity=high"
```

### Python客户端示例

```python
import requests
import json

BASE_URL = "http://localhost:8000/api/v1/analytics"

# 汇总统计
response = requests.get(f"{BASE_URL}/summary", params={
    "start_date": "2024-01-01",
    "end_date": "2024-12-31"
})
summary = response.json()
print(f"净收入: {summary['net_revenue']}")

# 趋势分析
response = requests.get(f"{BASE_URL}/trends", params={
    "start_date": "2024-01-01",
    "end_date": "2024-12-31",
    "granularity": "monthly"
})
trends = response.json()
for period in trends["time_series"]:
    print(f"{period['period_label']}: {period['metrics']['net_revenue']}")

# 异常检测
response = requests.get(f"{BASE_URL}/anomalies", params={
    "start_date": "2024-01-01",
    "end_date": "2024-12-31",
    "severity": "high"
})
anomalies = response.json()
print(f"发现 {anomalies['anomaly_count']} 个异常")
```

---

## 测试结果

### 集成测试 (8/8通过)

✅ **测试 1**: 汇总统计计算准确性
- 对账单数: 9
- 总销售额: 4107.62
- 净收入: 2319.13
- 周期天数: 290

✅ **测试 2**: 月度趋势分析
- 周期数: 6
- 每个月的指标完整
- 时间顺序正确

✅ **测试 3**: 周度趋势分析
- 周期数: 9
- 周分组正确
- ISO周编号格式正确

✅ **测试 4**: 两期对比计算
- 第一期销售额: 0
- 第二期销售额: 1011.81
- 变化量正确计算

✅ **测试 5**: 异常检测规则
- 总对账单数: 9
- 异常数量: 4
- 异常类型: negative_revenue

✅ **测试 6**: 日期范围查询
- 查询范围: 2024-12-01 至 2025-01-31
- 找到对账单数: 4

✅ **测试 7**: 无数据时期处理
- 空时期返回: 0条对账单
- 行为符合预期

✅ **测试 8**: 金额精度计算
- 所有金额: Decimal类型
- 精度验证: 通过

---

## 文件清单

### 核心文件

| 文件 | 行数 | 说明 |
|-----|------|------|
| `backend/app/crud/pdf_file.py` | +90 | CRUD扩展 |
| `backend/app/schemas/analytics.py` | 141 | Schema定义 |
| `backend/app/services/analytics_service.py` | 350 | Service实现 |
| `backend/app/api/v1/analytics.py` | 200 | API端点 |
| `backend/tests/test_analytics_functionality.py` | 460 | 集成测试 |

### 新增方法

**CRUD层**:
- `get_statements_by_date_range()` - 日期范围查询
- `get_statements_grouped_by_period()` - 按粒度分组

**Service层**:
- `calculate_aggregated_metrics()` - 汇总统计
- `calculate_trend_analysis()` - 趋势分析
- `calculate_comparison()` - 对比分析
- `detect_anomalies()` - 异常检测

**API层**:
- `GET /api/v1/analytics/summary` - 汇总统计
- `GET /api/v1/analytics/trends` - 趋势分析
- `POST /api/v1/analytics/comparison` - 对比分析
- `GET /api/v1/analytics/anomalies` - 异常检测

---

## 后续改进方向

### 短期改进 (可选)
- [ ] 缓存热点查询结果
- [ ] 添加更多异常检测规则
- [ ] 导出分析结果为Excel报表

### 中期改进 (可选)
- [ ] 机器学习预测模型
- [ ] 自定义告警阈值
- [ ] 历史数据对比

### 长期改进 (可选)
- [ ] 实时数据流处理
- [ ] 分布式计算支持
- [ ] 高级可视化Dashboard

---

## 相关文档

- [API文档](API文档.md) - 完整的API参考
- [数据库文档](数据库文档.md) - 数据库设计和优化

---

**文档版本**: 1.0 | **最后更新**: 2025-12-20 | **维护者**: 开发团队
