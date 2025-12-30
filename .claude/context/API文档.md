# Walmart PDF解析系统 - API文档

> **版本**: 1.0 | **更新**: 2025-12-20 | **文档生成日期**: 2025-12-20

---

## 📋 目录

1. [API概览](#api概览)
2. [基础信息](#基础信息)
3. [PDF文件管理](#pdf文件管理)
4. [对账单数据](#对账单数据)
5. [数据分析](#数据分析)
6. [错误处理](#错误处理)
7. [认证和权限](#认证和权限)

---

## API概览

Walmart PDF解析系统提供RESTful API接口，支持以下主要功能模块：

| 模块 | 前缀 | 说明 |
|-----|------|------|
| PDF管理 | `/api/v1/pdfs` | PDF文件上传、查询、删除 |
| 对账单 | `/api/v1/statements` | 对账单数据查询、修改、导出 |
| 分析 | `/api/v1/analytics` | 数据统计、趋势分析、对比、异常检测 |

---

## 基础信息

### 服务地址

- 生产环境: http://localhost:8000
- API文档: http://localhost:8000/api/docs (Swagger UI)
- ReDoc: http://localhost:8000/api/redoc
- OpenAPI规范: http://localhost:8000/api/openapi.json

### 健康检查

```bash
GET /health
```

**响应示例**:
```json
{
  "status": "healthy",
  "service": "walmart-pdf-parser"
}
```

---

## PDF文件管理

### 1. 上传PDF文件

```http
POST /api/v1/pdfs/upload
```

**查询参数**:
- `skip` (int, 可选): 跳过记录数
- `limit` (int, 可选): 返回记录数

---

## 对账单数据

### 1. 获取完整对账单数据

```http
GET /api/v1/statements/{pdf_id}/data
```

**响应 (200 OK)**: 返回包括header、sales、refund等8个板块的完整数据

### 2. 导出对账单数据

```http
GET /api/v1/statements/{pdf_id}/export?format=json|csv|excel
```

---

## 数据分析

### 1. 汇总统计

```http
GET /api/v1/analytics/summary?start_date=2024-01-01&end_date=2024-12-31
```

返回总销售额、总退款、总佣金、总WFS费、总广告费、净收入等指标。

### 2. 趋势分析

```http
GET /api/v1/analytics/trends?start_date=2024-01-01&end_date=2024-12-31&granularity=monthly|weekly|statement
```

返回按时间粒度分组的时间序列数据。

### 3. 对比分析

```http
POST /api/v1/analytics/comparison
{
  "period1_start": "2024-01-01",
  "period1_end": "2024-06-30",
  "period2_start": "2024-07-01",
  "period2_end": "2024-12-31"
}
```

返回两期数据对比，包括绝对变化和百分比变化。

### 4. 异常检测

```http
GET /api/v1/analytics/anomalies?start_date=2024-01-01&end_date=2024-12-31&severity=all|low|medium|high
```

检测异常类型：
- 高退款率 (>20%)
- 负收入
- 高佣金率 (>20%)
- 高WFS费用 (>10%)
- 高广告费用 (>15%)

---

## 错误处理

### 常见HTTP状态码

| 状态码 | 说明 |
|--------|------|
| 200 | 成功 |
| 201 | 创建成功 |
| 400 | 请求错误 |
| 404 | 资源不存在 |
| 500 | 服务器错误 |

---

**文档版本**: 1.0 | **最后更新**: 2025-12-20
