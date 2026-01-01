# 数据库结构实施指南

**设计完成时间**: 2026-01-01  
**当前阶段**: Phase 1 - 初始化  
**基础数据**: 6 个 PDF，31 个字段

---

## 快速开始（5 分钟）

### 步骤 1: 查看设计文档

```bash
# 打开完整设计文档
cat .claude/DATABASE_SCHEMA_DESIGN.md
```

**关键要点：**
- ✅ 频率 ≥ 2 的字段 (19 个) → 数据库字段，有默认值
- ❌ 频率 = 1 的字段 (12 个) → JSON "其他" 字段，保留明细

**三层字段分布：**
| 频率 | 字段数 | 数据库列 | JSON 列 |
|------|--------|---------|--------|
| 100% | 11 | NOT NULL | - |
| 50-83% | 8 | DEFAULT | - |
| 17-33% | 12 | - | JSON |

---

### 步骤 2: 初始化数据库

```bash
cd /Users/jiaxinming/JxmWork/walmart-a

# 方法 A: 使用 Python 脚本（推荐）
python scripts/db_import_new_structure.py --init

# 方法 B: 直接执行 SQL
sqlite3 backend/data/walmart_pdf_parser.db < backend/database/schema_design_v1.sql
```

**验证初始化成功：**
```bash
sqlite3 backend/data/walmart_pdf_parser.db ".tables"
# 输出应该包含：
# adjustments  other_activities  refund_details  sales_details
# section_metadata  statement_headers  wfs_services  db_config
```

---

### 步骤 3: 导入现有 PDF 解析数据

**前置条件**: 6 个 PDF 的解析结果已存在 `PdfData/*.json`

```bash
# 批量导入所有 JSON 数据
python scripts/db_import_new_structure.py --batch
```

**预期输出：**
```
================================================================================
处理: MP_01142025_statement_summary.json
  ✓ 导入头信息: MP_01142025_statement_summary.pdf (ID: 1)
  ✓ 导入销售明细
  ✓ 导入退款明细
  ✓ 导入其他活动
  ✓ 导入调整
  ✓ 导入 WFS 服务
  ✓ 导入板块元数据 (7 个板块)
...
================================================================================
导入完成: 6 成功, 0 失败
================================================================================
```

---

## 详细步骤

### Phase 1: 数据库初始化（本周完成）

**目标：** ✅ 创建表结构  
**负责：** AI 脚本  
**时间：** < 1 分钟

**执行命令：**
```bash
python scripts/db_import_new_structure.py --init
```

**验证命令：**
```bash
sqlite3 backend/data/walmart_pdf_parser.db "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;" 
```

**预期结果：**
```
adjustments
db_config
other_activities
refund_details
sales_details
section_metadata
statement_headers
wfs_services
```

---

### Phase 2: 数据导入（本周完成）

**目标：** ✅ 导入 6 个 PDF 的解析结果  
**前置：** 需要 `PdfData/*.json` 文件存在  
**时间：** < 10 秒

**执行命令：**
```bash
python scripts/db_import_new_structure.py --batch
```

**验证命令：**
```bash
# 查看已导入记录数
sqlite3 backend/data/walmart_pdf_parser.db "
SELECT 
    (SELECT COUNT(*) FROM statement_headers) as headers,
    (SELECT COUNT(*) FROM sales_details) as sales,
    (SELECT COUNT(*) FROM refund_details) as refunds
;"
```

**预期结果：**
```
headers|sales|refunds
6|6|6
```

---

### Phase 3: 数据验证（下周）

**目标：** ✅ 验证数据完整性和约束  
**时间：** 5-10 分钟

#### 验证 3.1: 外键约束

```bash
sqlite3 backend/data/walmart_pdf_parser.db "
-- 查看孤立记录（应返回 0）
SELECT COUNT(*) FROM sales_details 
WHERE header_id NOT IN (SELECT id FROM statement_headers)
;"
```

#### 验证 3.2: 字段值范围

```bash
sqlite3 backend/data/walmart_pdf_parser.db "
-- 查看异常金额（负数或极端值）
SELECT 
    source_pdf_name,
    payment_to_you,
    opening_balance
FROM statement_headers
WHERE payment_to_you < 0 OR opening_balance < 0
;"
```

#### 验证 3.3: 数据统计

```bash
sqlite3 backend/data/walmart_pdf_parser.db "
-- 生成财务汇总
SELECT * FROM financial_summary;
"
```

---

## 表结构速查

### statement_headers（基础信息）
| 字段 | 类型 | 频率 | 默认值 |
|------|------|-----|--------|
| id | INT | - | PK |
| source_pdf_name | VARCHAR(255) | - | UNIQUE |
| statement_period | VARCHAR(100) | 100% | NOT NULL |
| payment_to_you | DECIMAL(12,2) | 100% | NOT NULL |
| opening_balance | DECIMAL(12,2) | 100% | NOT NULL |
| reserve_fund | DECIMAL(12,2) | 100% | NOT NULL |
| pending_payment | DECIMAL(12,2) | 100% | NOT NULL |
| closing_balance | DECIMAL(12,2) | 83% | NULL |
| extra_data | JSON | - | NULL |

### sales_details（销售明细）
| 字段 | 类型 | 频率 | 默认值 |
|------|------|-----|--------|
| header_id | INT | - | FK |
| product_price | DECIMAL(12,2) | 100% | NOT NULL |
| shipping | DECIMAL(12,2) | 100% | NOT NULL |
| tax_collected_net | DECIMAL(12,2) | 100% | NOT NULL |
| net_commission | DECIMAL(12,2) | 100% | NOT NULL |
| withholding_tax_net | DECIMAL(12,2) | 100% | NOT NULL |
| sales_total | DECIMAL(12,2) | 100% | NOT NULL |
| wfs_shipping_refund | DECIMAL(12,2) | 83% | 0.00 |
| wfs_shipping_tax_refund | DECIMAL(12,2) | 83% | 0.00 |
| walmart_contribution_margin | DECIMAL(12,2) | 83% | NULL |

### refund_details（退款明细）
| 字段 | 类型 | 频率 | 默认值 |
|------|------|-----|--------|
| header_id | INT | - | FK |
| commission | DECIMAL(12,2) | 100% | NOT NULL |
| product_price | DECIMAL(12,2) | 100% | NOT NULL |
| shipping | DECIMAL(12,2) | 100% | NOT NULL |
| tax_collected_net | DECIMAL(12,2) | 100% | NOT NULL |
| withholding_tax_net | DECIMAL(12,2) | 100% | NOT NULL |
| refund_total | DECIMAL(12,2) | 100% | NOT NULL |
| wfs_total_discount | DECIMAL(12,2) | 100% | NOT NULL |
| walmart_contribution_margin | DECIMAL(12,2) | 83% | NULL |

---

## 常用查询

### 查询 1: 获取完整语句

```sql
SELECT * FROM statement_headers 
WHERE source_pdf_name = 'MP_01142025_statement_summary.pdf';
```

### 查询 2: 获取销售明细

```sql
SELECT h.statement_period, s.*
FROM sales_details s
JOIN statement_headers h ON s.header_id = h.id
ORDER BY h.statement_period;
```

### 查询 3: 财务汇总

```sql
SELECT * FROM financial_summary;
```

### 查询 4: 统计 WFS 费用

```sql
SELECT 
    h.source_pdf_name,
    SUM(s.wfs_shipping_refund) as total_wfs_refund,
    COUNT(DISTINCT w.id) as wfs_service_count
FROM statement_headers h
LEFT JOIN sales_details s ON h.id = s.header_id
LEFT JOIN wfs_services w ON h.id = w.header_id
GROUP BY h.source_pdf_name;
```

---

## 常见问题 (FAQ)

### Q1: 为什么有些字段放在 JSON 中？

**A:** 频率 = 1 的字段（只在 1 个 PDF 中出现）特征：
- 业务不稳定性高（未来可能不出现）
- 扰动 DB 结构（新增太多稀用列）
- 占用存储空间（大多数行为 NULL）

**解决方案：** 放入 JSON，未来如果某字段频率增加到 ≥ 2，自动提升为 DB 列。

---

### Q2: 低频字段数据在哪里？

**A:** 在各表的 `extra_data` JSON 字段中：

```sql
-- 查看某 PDF 的所有低频字段
SELECT extra_data FROM statement_headers 
WHERE source_pdf_name = 'MP_01142025_statement_summary.pdf';

-- JSON 格式示例：
{
  "footer": {
    "专业列表": "value1",
    "其他": "value2"
  }
}
```

---

### Q3: 如何添加新字段？

**当新字段出现时：**

1. 运行月度分析
   ```bash
   python scripts/batch_test_and_analyze.py
   ```

2. 如果频率 ≥ 2，使用 Alembic 迁移添加列
   ```bash
   alembic revision --autogenerate -m "add new_field column"
   alembic upgrade head
   ```

3. 如果频率 = 1，自动存入 JSON（无需修改表结构）

---

### Q4: 默认值为什么这样设置？

| 字段类型 | 默认值 | 原因 |
|---------|--------|------|
| 必有字段 (100%) | NOT NULL | 确保数据完整性 |
| 常见字段 (50-83%) | DEFAULT NULL/0 | 容忍偶发缺失 |
| 可选字段 (17%) | JSON | 避免 NULL 列泛滥 |

---

### Q5: 如何导出数据到 CSV？

```bash
# 导出所有语句到 CSV
sqlite3 backend/data/walmart_pdf_parser.db ".mode csv" \
  "SELECT * FROM statement_headers;" > statements.csv

# 导出财务汇总
sqlite3 backend/data/walmart_pdf_parser.db ".mode csv" \
  "SELECT * FROM financial_summary;" > summary.csv
```

---

## 下一步

### ✅ 已完成
- [x] 字段分析（31 字段，6 PDF）
- [x] 表结构设计（7 核心表）
- [x] SQL 脚本生成
- [x] Python 导入脚本

### 📋 待做
- [ ] Phase 1: 执行 `python scripts/db_import_new_structure.py --init`
- [ ] Phase 2: 执行 `python scripts/db_import_new_structure.py --batch`
- [ ] Phase 3: 运行验证查询
- [ ] 文档更新（README）
- [ ] 可选：创建 Alembic 迁移框架（未来扩展用）

### 🚀 优化方向
1. **性能优化**：添加更多索引
2. **审计日志**：记录数据变更
3. **数据质量**：异常值检测与清洗
4. **API 层**：CRUD 接口开发

---

**联系**: 有任何问题，请参考 `.claude/DATABASE_SCHEMA_DESIGN.md`

