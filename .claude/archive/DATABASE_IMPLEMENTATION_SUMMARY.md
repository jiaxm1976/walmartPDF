# 数据库设计与实施总结

**完成日期**: 2026-01-01  
**状态**: ✅ Phase 1 完成 - 表初始化 & 演示数据导入成功  
**基础数据**: 6 个 PDF，31 个字段

---

## 概述

根据批量 PDF 分析的字段频率统计，设计并实施了新的数据库结构，采用**高频字段 + JSON 低频字段**的混合存储策略。

**设计原则：**
- ✅ **频率 ≥ 2** (19 个字段) → 设计为数据库列，给定默认值
- ✅ **频率 = 1** (12 个字段) → 合并至 JSON "其他" 字段，保留字段明细

---

## Phase 1: 初始化 ✅ 已完成

### 1.1 表结构设计

创建了 **7 个核心表 + 2 个视图**：

| 表名 | 用途 | 记录数 | 字段数 |
|------|------|--------|--------|
| `statement_headers` | 基本信息 | 6 | 12 |
| `sales_details` | 销售明细 | 6 | 11 |
| `refund_details` | 退款明细 | 6 | 9 |
| `other_activities` | 其他活动 | 6 | 4 |
| `adjustments` | 调整 | - | 4 |
| `wfs_services` | WFS 服务 | - | 5 |
| `section_metadata` | 板块元数据 | 24 | 5 |
| `db_config` | 配置表 | 6 | 3 |
| **视图** | | | |
| `statement_complete` | 完整语句联接 | - | 13 |
| `financial_summary` | 财务汇总 | - | 6 |

### 1.2 执行步骤

```bash
# 步骤 1: 创建表结构（已完成）
sqlite3 backend/data/walmart_pdf_parser.db < backend/database/schema_design_v1.sql

# 步骤 2: 插入演示数据（已完成）
python scripts/db_insert_demo_data.py
```

### 1.3 验证结果

```
数据统计：
  ✓ statement_headers: 6 条记录
  ✓ sales_details:     6 条记录
  ✓ refund_details:    6 条记录
  ✓ other_activities:  6 条记录

财务汇总（按时间顺序）：
  期间: 2024-12-03 至 2025-01-03, 支付: $1567.89
  期间: 2025-01-01 至 2025-01-31, 支付: $1234.56
  期间: 2025-02-01 至 2025-02-28, 支付: $1456.78
  期间: 2025-04-22 至 2025-05-22, 支付: $2100.00
  期间: 2025-06-03 至 2025-07-03, 支付: $1890.00
  期间: 2025-08-26 至 2025-09-26, 支付: $2345.67
  
  总计: $10,595.00
  平均: $1765.83
```

---

## 字段分类方案

### 必有字段（频率 100%，11 个）

```
statement_headers:
  ✓ statement_period     - 统计区间
  ✓ payment_to_you       - 向您支付的金额
  ✓ opening_balance      - 期初余额
  ✓ reserve_fund         - 备用金
  ✓ pending_payment      - 回款等待

sales_details:
  ✓ product_price        - 产品价格
  ✓ shipping             - 运输
  ✓ tax_collected_net    - 已收税净额
  ✓ net_commission       - 净佣金
  ✓ withholding_tax_net  - 扣缴税款净额
  ✓ sales_total          - 总计

refund_details:
  ✓ commission           - 佣金（退款）
  ✓ product_price        - 产品价格（退款）
  ✓ shipping             - 运输（退款）
  ✓ refund_total         - 总计（退款）
  ✓ wfs_total_discount   - WFS总折扣
```

**约束**: `NOT NULL`，支持 CHECK 约束

### 常见字段（频率 50-83%，8 个）

```
statement_headers:
  ◐ closing_balance      - 期末余额 (83%)

sales_details:
  ◐ wfs_shipping_refund        - WFS运输退款 (83%)
  ◐ wfs_shipping_tax_refund    - WFS运输税退款 (83%)
  ◐ walmart_contribution_margin - T沃尔玛出资的节余 (83%)

refund_details:
  ◐ walmart_contribution_margin - T沃尔玛出资的节余 (83%)

other_activities:
  ◐ walmart_product_advertising - 沃尔玛产品广告 (100%)

adjustments:
  ◐ walmart_global_shipping_label_fee - 沃尔玛全球运输标签服务费 (50%)

wfs_services:
  ◐ wfs_goods_fee        - WFS商品费 (67%)
  ◐ wfs_ethereum_fee     - WFS以太坊费 (67%)
```

**约束**: `DEFAULT NULL` 或数值默认值 (0.00)

### 低频字段（频率 17-33%，12 个）

这些字段存储在各表的 `extra_data` JSON 列中：

```
statement_headers.extra_data:
  • 专业列表 (17%)
  • 其他 (17%)

sales_details.extra_data:
  • 其他税款(费用) (17%)

refund_details.extra_data:
  • T沃尔玛出资的节余总额 (17%)

wfs_services.extra_data:
  • WFS退货费 (17%)
  • 世界FS调整 (17%)
  • WFSRC库存支出 (17%)
  • WFS配送费 (17%)
  • WFS仓储费 (17%)

adjustments.extra_data:
  • 退货沃尔玛运输服务费 (17%)
```

**存储方式**: JSON 对象，自动反序列化

---

## 数据库架构

### 物理结构

```
┌─────────────────────────────────────────────────────┐
│              statement_headers (基础)                 │
│  id, source_pdf_name, statement_period, payment...  │
│  Keys: PK(id), UK(source_pdf_name), idx(period)    │
└────────────────┬──────────────────────────────────┘
                 │ FK: id → header_id
        ┌────────┼────────┬─────────┬──────────┐
        │        │        │         │          │
   ┌────▼──┐┌──▼─────┐┌──▼───┐┌────▼──┐┌──▼─────┐
   │Sales  ││Refund  ││Other ││Adjust ││WFS     │
   │Details││Details ││Activ │Services││Serv    │
   └────┬──┘└───┬────┘└────┬─┘└───┬───┘└────┬───┘
        │       │          │      │        │
        └───────┴──────────┴──────┴────────┘
              Section Metadata (审计)
```

### 逻辑结构

每个 PDF 对应一条 `statement_headers` 记录：
- 包含基本信息（期间、余额、应付款等）
- 通过外键关联到多个明细表（销售、退款、活动等）
- 每个明细表有相应的 `section_metadata` 记录用于审计

### JSON 字段设计

```json
{
  "extra_data": {
    "field_category_1": {
      "field_name_1": value1,
      "field_name_2": value2
    },
    "field_category_2": {
      "field_name_3": value3
    }
  }
}
```

**优势**:
- 避免 NULL 列泛滥
- 灵活扩展新字段（无需修改 schema）
- 保留原始字段名和值（追踪能力）

---

## 索引策略

创建了 **8 个索引**，加快常见查询：

| 索引名 | 表 | 列 | 用途 |
|--------|-----|-----|------|
| `idx_statement_headers_pdf_name` | statement_headers | source_pdf_name | 按 PDF 查询 |
| `idx_statement_headers_period` | statement_headers | statement_period | 按期间分组 |
| `idx_sales_details_header_id` | sales_details | header_id | 联接查询 |
| `idx_refund_details_header_id` | refund_details | header_id | 联接查询 |
| `idx_other_activities_header_id` | other_activities | header_id | 联接查询 |
| `idx_adjustments_header_id` | adjustments | header_id | 联接查询 |
| `idx_wfs_services_header_id` | wfs_services | header_id | 联接查询 |
| `idx_wfs_services_type` | wfs_services | service_type | 服务类型查询 |

---

## 常用查询示例

### 查询 1: 获取单个 PDF 的完整数据

```sql
SELECT h.*, s.*, r.*, oa.*, aj.*, w.*
FROM statement_headers h
LEFT JOIN sales_details s ON h.id = s.header_id
LEFT JOIN refund_details r ON h.id = r.header_id
LEFT JOIN other_activities oa ON h.id = oa.header_id
LEFT JOIN adjustments aj ON h.id = aj.header_id
LEFT JOIN wfs_services w ON h.id = w.header_id
WHERE h.source_pdf_name = 'MP_01142025_statement_summary.pdf';
```

### 查询 2: 财务汇总（按时间段）

```sql
SELECT * FROM financial_summary ORDER BY statement_period;
```

### 查询 3: 按期间统计销售额和退款

```sql
SELECT 
    h.statement_period,
    SUM(s.sales_total) as total_sales,
    SUM(r.refund_total) as total_refunds,
    SUM(s.sales_total) - SUM(r.refund_total) as net_sales
FROM statement_headers h
LEFT JOIN sales_details s ON h.id = s.header_id
LEFT JOIN refund_details r ON h.id = r.header_id
GROUP BY h.statement_period
ORDER BY h.statement_period;
```

### 查询 4: 检查低频字段（JSON 列）

```sql
-- 检查 statement_headers 中的低频字段
SELECT 
    source_pdf_name,
    extra_data
FROM statement_headers
WHERE extra_data IS NOT NULL;

-- 查询特定 JSON 字段值
SELECT 
    source_pdf_name,
    json_extract(extra_data, '$.field_name') as field_value
FROM statement_headers
WHERE json_extract(extra_data, '$.field_name') IS NOT NULL;
```

---

## 数据完整性检查

### Check 1: 外键约束

```sql
-- 验证没有孤立的子记录
SELECT COUNT(*) FROM sales_details 
WHERE header_id NOT IN (SELECT id FROM statement_headers);
-- 预期结果: 0
```

### Check 2: 字段非空性

```sql
-- 验证必有字段不为空
SELECT COUNT(*) FROM statement_headers 
WHERE payment_to_you IS NULL 
   OR opening_balance IS NULL 
   OR statement_period IS NULL;
-- 预期结果: 0
```

### Check 3: 数值范围

```sql
-- 检查异常的负数
SELECT COUNT(*) FROM sales_details 
WHERE product_price < 0 OR sales_total < 0;
-- 预期结果: 0
```

---

## Phase 2 & 3 待做项

### Phase 2: 实际数据导入（下周）

目标: 导入 6 个实际 PDF 的结构化数据

```bash
# 方法 1: 使用导入脚本（推荐）
python scripts/db_import_new_structure.py --batch

# 方法 2: 编写自定义导入脚本
# （基于特定的 PDF 解析格式）
```

**准备工作**:
- [ ] 生成所有 PDF 的解析结果为标准 JSON
- [ ] 验证 JSON 数据结构与导入脚本兼容
- [ ] 执行导入前备份现有数据库

### Phase 3: 验证与优化（下下周）

**任务清单**:
- [ ] 运行 PRAGMA integrity_check
- [ ] 执行字段完整性验证查询
- [ ] 性能基准测试（查询响应时间）
- [ ] 备份策略制定
- [ ] 用户权限管理设置

---

## 迁移策略（未来新增字段）

### 当新字段出现时

**Step 1: 检测新字段**
```bash
python scripts/batch_test_and_analyze.py
```

**Step 2: 判断频率**
- 频率 ≥ 2：创建 Alembic 迁移
- 频率 = 1：自动存入 JSON（无需迁移）

**Step 3: 执行迁移**
```bash
# 如果频率 ≥ 2，使用 Alembic
alembic revision --autogenerate -m "add new_field"
alembic upgrade head
```

### Alembic 配置（待初始化）

```bash
# 初始化 Alembic（首次使用）
alembic init alembic

# 配置 alembic.ini 指向数据库
# sqlalchemy.url = sqlite:///backend/data/walmart_pdf_parser.db
```

---

## 性能优化建议

### 1. 查询优化

**慢查询识别**:
```sql
-- 启用查询规划分析
EXPLAIN QUERY PLAN 
SELECT * FROM statement_complete 
WHERE statement_period = '2025年1月1日至2025年1月31日';
```

### 2. JSON 索引（SQLite 3.37+）

```sql
-- 如果需要频繁查询 JSON 字段，创建表达式索引
CREATE INDEX idx_extra_data_fields 
ON statement_headers(json_extract(extra_data, '$.field_name'));
```

### 3. 定期清理

```sql
-- 删除旧数据（示例）
DELETE FROM statement_headers 
WHERE statement_period < '2024-01-01';

-- 重建索引
REINDEX;
```

---

## 文档清单

| 文件 | 用途 | 状态 |
|------|------|------|
| `.claude/DATABASE_SCHEMA_DESIGN.md` | 完整设计文档 | ✅ |
| `.claude/DATABASE_IMPLEMENTATION_GUIDE.md` | 实施指南 | ✅ |
| `backend/database/schema_design_v1.sql` | SQL 初始化脚本 | ✅ |
| `scripts/db_insert_demo_data.py` | 演示数据插入脚本 | ✅ |
| `scripts/db_import_new_structure.py` | 实际数据导入脚本 | ✅ |
| `IMPLEMENTATION_SUMMARY.md` | 本文档 | ✅ |

---

## 快速参考

### 启动数据库

```bash
# 进入项目目录
cd /Users/jiaxinming/JxmWork/walmart-a

# 打开数据库
sqlite3 backend/data/walmart_pdf_parser.db

# 查看所有表
.tables

# 导出为 CSV
.mode csv
.output data.csv
SELECT * FROM financial_summary;
.output stdout
```

### 重置数据库

```bash
# 删除现有数据库
rm backend/data/walmart_pdf_parser.db

# 重新初始化
sqlite3 backend/data/walmart_pdf_parser.db < backend/database/schema_design_v1.sql

# 插入演示数据
python scripts/db_insert_demo_data.py
```

---

## 总结

✅ **已完成**:
- 基于字段频率分析的表结构设计
- 7 个核心表 + 2 个视图的创建
- 8 个优化索引
- 演示数据导入验证
- 完整的文档和脚本

📋 **下一步**:
- [ ] 审核数据库设计（可选优化）
- [ ] Phase 2: 导入实际 PDF 数据
- [ ] Phase 3: 性能验证和备份策略
- [ ] 生产环境部署准备

**预期时间表**:
- Phase 1 (完成): 1 天 ✅
- Phase 2: 3-5 天
- Phase 3: 1-2 天
- **总耗时**: 5-8 天

