# Walmart PDF 数据库设计方案

**设计日期**: 2026-01-01  
**基于**: 6 个 PDF 样本的字段频率分析  
**设计策略**: 频率 ≥ 2 → DB 字段(NOT NULL/DEFAULT), 频率 = 1 → JSON "其他"字段

---

## 1. 字段分类与数据库结构

### 分类规则

| 频率 | 决策 | 处理方式 |
|------|------|---------|
| 6/6 (100%) | ✅ 必有字段 | `NOT NULL` |
| 5/6 (83%) | ✅ 常见字段 | `DEFAULT NULL` 或数值默认 |
| 4/6 (67%) | ✅ 通用字段 | `DEFAULT NULL` |
| 3/6 (50%) | ✅ 通用字段 | `DEFAULT NULL` |
| 2/6 (33%) | ✅ DB 字段 | `DEFAULT NULL` |
| 1/6 (17%) | ❌ 低频字段 | 合并至 JSON "其他" |

### 频率 ≥ 2 的字段汇总（19 个）

**header 板块（基本信息）**
- 统计区间 (100%, 6) - 日期范围
- 向您支付的金额 (100%, 6) - 支付金额
- 期初余额 (100%, 6) - 初始余额
- 备用金 (100%, 6) - 备用资金
- 回款等待 (100%, 6) - 待回款

**销售板块**
- 产品价格 (100%, 6) - 销售额
- 运输 (100%, 6) - 运输费
- 已收税净额 (100%, 6) - 税费
- 净佣金 (100%, 6) - 佣金
- 扣缴税款净额 (100%, 6) - 扣税
- 总计: (100%, 6) - 小计
- WFS运输退款 (83%, 5) - FBA运输退款
- WFS运输税退款 (83%, 5) - FBA运输税退款
- T沃尔玛出资的节余 (83%, 5) - 活动补贴

**退款板块**
- 佣金 (100%, 6) - 退款佣金
- WFS总折扣 (100%, 6) - FBA折扣

**其他活动**
- 沃尔玛产品广告 (100%, 6) - 广告费

**调整板块**
- 沃尔玛全球运输标签服务费 (50%, 3) - 物流费

**footer 板块**
- 期末余额 (83%, 5) - 结束余额

**WFS 板块**
- WFS商品费 (67%, 4)
- WFS以太坊费 (67%, 4)

---

## 2. 数据库表设计

### 核心表结构

```sql
-- 表 1: statement_headers (语句头/基本信息)
CREATE TABLE statement_headers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_pdf_name VARCHAR(255) NOT NULL UNIQUE,
    statement_period VARCHAR(100) NOT NULL,           -- 统计区间
    payment_to_you DECIMAL(12,2) NOT NULL,          -- 向您支付的金额
    opening_balance DECIMAL(12,2) NOT NULL,         -- 期初余额
    reserve_fund DECIMAL(12,2) NOT NULL,            -- 备用金
    pending_payment DECIMAL(12,2) NOT NULL,         -- 回款等待
    closing_balance DECIMAL(12,2) DEFAULT NULL,     -- 期末余额
    processing_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    extra_data JSON DEFAULT NULL,                   -- 低频字段 JSON 存储
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 表 2: sales_details (销售明细)
CREATE TABLE sales_details (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    header_id INTEGER NOT NULL,
    product_price DECIMAL(12,2) NOT NULL,           -- 产品价格
    shipping DECIMAL(12,2) NOT NULL,                -- 运输
    tax_collected_net DECIMAL(12,2) NOT NULL,       -- 已收税净额
    net_commission DECIMAL(12,2) NOT NULL,          -- 净佣金
    withholding_tax_net DECIMAL(12,2) NOT NULL,     -- 扣缴税款净额
    sales_total DECIMAL(12,2) NOT NULL,             -- 总计
    wfs_shipping_refund DECIMAL(12,2) DEFAULT 0.00, -- WFS运输退款
    wfs_shipping_tax_refund DECIMAL(12,2) DEFAULT 0.00, -- WFS运输税退款
    walmart_contribution_margin DECIMAL(12,2) DEFAULT NULL, -- T沃尔玛出资的节余
    extra_data JSON DEFAULT NULL,                   -- 低频字段
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(header_id) REFERENCES statement_headers(id) ON DELETE CASCADE
);

-- 表 3: refund_details (退款明细)
CREATE TABLE refund_details (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    header_id INTEGER NOT NULL,
    commission DECIMAL(12,2) NOT NULL,              -- 佣金
    product_price DECIMAL(12,2) NOT NULL,           -- 产品价格
    shipping DECIMAL(12,2) NOT NULL,                -- 运输
    tax_collected_net DECIMAL(12,2) NOT NULL,       -- 已收税净额
    withholding_tax_net DECIMAL(12,2) NOT NULL,     -- 扣缴税款净额
    refund_total DECIMAL(12,2) NOT NULL,            -- 总计
    wfs_total_discount DECIMAL(12,2) NOT NULL,      -- WFS总折扣
    walmart_contribution_margin DECIMAL(12,2) DEFAULT NULL, -- T沃尔玛出资的节余
    extra_data JSON DEFAULT NULL,                   -- 低频字段
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(header_id) REFERENCES statement_headers(id) ON DELETE CASCADE
);

-- 表 4: other_activities (其他活动)
CREATE TABLE other_activities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    header_id INTEGER NOT NULL,
    activity_type VARCHAR(100) NOT NULL,            -- 活动类型
    walmart_product_advertising DECIMAL(12,2) DEFAULT NULL, -- 沃尔玛产品广告
    extra_data JSON DEFAULT NULL,                   -- 其他字段
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(header_id) REFERENCES statement_headers(id) ON DELETE CASCADE
);

-- 表 5: adjustments (调整)
CREATE TABLE adjustments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    header_id INTEGER NOT NULL,
    adjustment_type VARCHAR(100) NOT NULL,          -- 调整类型
    walmart_global_shipping_label_fee DECIMAL(12,2) DEFAULT NULL, -- 沃尔玛全球运输标签服务费
    extra_data JSON DEFAULT NULL,                   -- 其他字段
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(header_id) REFERENCES statement_headers(id) ON DELETE CASCADE
);

-- 表 6: wfs_services (沃尔玛配送服务 & 商品服务)
CREATE TABLE wfs_services (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    header_id INTEGER NOT NULL,
    service_type VARCHAR(50) NOT NULL,              -- 'FBA_goods' | 'FBA_shipping' | 'WFS_goods' | 'WFS_shipping'
    wfs_goods_fee DECIMAL(12,2) DEFAULT NULL,       -- WFS商品费
    wfs_ethereum_fee DECIMAL(12,2) DEFAULT NULL,    -- WFS以太坊费
    wfs_total_discount DECIMAL(12,2) DEFAULT NULL,  -- WFS总折扣
    extra_data JSON DEFAULT NULL,                   -- 其他字段
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(header_id) REFERENCES statement_headers(id) ON DELETE CASCADE
);
```

---

## 3. JSON "其他"字段设计

### 频率 = 1 的低频字段（12 个）

| 字段名 | 频率 | 所属板块 | 建议 |
|--------|------|---------|------|
| 其他税款(费用) | 1 | 销售 | → JSON other_charges |
| WFS退货费 | 1 | WFS | → JSON wfs_other |
| 世界FS调整 | 1 | WFS | → JSON wfs_adjustments |
| WFSRC库存支出 | 1 | WFS | → JSON wfs_inventory |
| 退货沃尔玛运输服务费 | 1 | 调整 | → JSON adjustment_fees |
| 专业列表 | 1 | footer | → JSON footer_items |
| 其他 | 1 | footer | → JSON footer_misc |
| T沃尔玛出资的节余总额 | 1 | 销售/退款 | → JSON walmart_totals |
| WFS配送费 | 1 | WFS配送 | → JSON wfs_logistics |
| WFS仓储费 | 1 | WFS配送 | → JSON wfs_storage |

### JSON 字段示例

```json
// statement_headers.extra_data
{
  "footer_items": {
    "专业列表": value,
    "其他": value
  },
  "footer_misc": {
    ...
  }
}

// sales_details.extra_data
{
  "other_charges": {
    "其他税款(费用)": value
  }
}

// refund_details.extra_data
{
  "walmart_totals": {
    "T沃尔玛出资的节余总额": value
  }
}

// wfs_services.extra_data
{
  "wfs_other": {
    "WFS退货费": value,
    "世界FS调整": value,
    "WFSRC库存支出": value
  },
  "wfs_logistics": {
    "WFS配送费": value,
    "WFS仓储费": value
  }
}
```

---

## 4. 默认值设置策略

### 数值字段默认值

| 字段类型 | 默认值 | 说明 |
|---------|-------|------|
| DECIMAL (金额) | 0.00 | 数值默认为 0，可选字段为 NULL |
| VARCHAR (文本) | NULL | 无强制默认 |
| TIMESTAMP | CURRENT_TIMESTAMP | 自动时间戳 |
| JSON | NULL | 无数据时为 NULL |

### 字段默认值表

```sql
-- statement_headers 默认值
closing_balance DEFAULT NULL      -- 可能部分 PDF 缺失

-- sales_details 默认值
wfs_shipping_refund DEFAULT 0.00
wfs_shipping_tax_refund DEFAULT 0.00
walmart_contribution_margin DEFAULT NULL

-- refund_details 默认值
walmart_contribution_margin DEFAULT NULL

-- adjustments 默认值
walmart_global_shipping_label_fee DEFAULT NULL
```

---

## 5. 索引设计

```sql
-- 加快查询速度
CREATE INDEX idx_statement_headers_pdf_name ON statement_headers(source_pdf_name);
CREATE INDEX idx_statement_headers_period ON statement_headers(statement_period);
CREATE INDEX idx_sales_details_header_id ON sales_details(header_id);
CREATE INDEX idx_refund_details_header_id ON refund_details(header_id);
CREATE INDEX idx_other_activities_header_id ON other_activities(header_id);
CREATE INDEX idx_adjustments_header_id ON adjustments(header_id);
CREATE INDEX idx_wfs_services_header_id ON wfs_services(header_id);
```

---

## 6. 数据完整性约束

```sql
-- 约束检查
ALTER TABLE sales_details
ADD CHECK (product_price >= 0);

ALTER TABLE sales_details
ADD CHECK (sales_total >= 0);

ALTER TABLE refund_details
ADD CHECK (commission >= 0);

-- 唯一性约束
ALTER TABLE statement_headers
ADD UNIQUE(source_pdf_name);
```

---

## 7. 字段映射表

| 原始字段名 | 数据库表 | 数据库列 | 频率 | 类型 | 默认值 |
|-----------|--------|--------|-----|------|-------|
| 统计区间 | statement_headers | statement_period | 100% | VARCHAR | - |
| 向您支付的金额 | statement_headers | payment_to_you | 100% | DECIMAL | - |
| 期初余额 | statement_headers | opening_balance | 100% | DECIMAL | - |
| 备用金 | statement_headers | reserve_fund | 100% | DECIMAL | - |
| 回款等待 | statement_headers | pending_payment | 100% | DECIMAL | - |
| 期末余额 | statement_headers | closing_balance | 83% | DECIMAL | NULL |
| 产品价格 | sales_details | product_price | 100% | DECIMAL | - |
| 运输 | sales_details/refund_details | shipping | 100% | DECIMAL | - |
| 已收税净额 | sales_details/refund_details | tax_collected_net | 100% | DECIMAL | - |
| 净佣金 | sales_details | net_commission | 100% | DECIMAL | - |
| 总计 | sales_details/refund_details | sales_total/refund_total | 100% | DECIMAL | - |
| 佣金 | refund_details | commission | 100% | DECIMAL | - |
| WFS总折扣 | refund_details/wfs_services | wfs_total_discount | 100% | DECIMAL | - |
| 沃尔玛产品广告 | other_activities | walmart_product_advertising | 100% | DECIMAL | NULL |
| WFS运输退款 | sales_details | wfs_shipping_refund | 83% | DECIMAL | 0.00 |
| WFS运输税退款 | sales_details | wfs_shipping_tax_refund | 83% | DECIMAL | 0.00 |
| 扣缴税款净额 | sales_details/refund_details | withholding_tax_net | 100% | DECIMAL | - |
| 期末余额 | statement_headers | closing_balance | 83% | DECIMAL | NULL |
| WFS商品费 | wfs_services | wfs_goods_fee | 67% | DECIMAL | NULL |
| WFS以太坊费 | wfs_services | wfs_ethereum_fee | 67% | DECIMAL | NULL |
| 沃尔玛全球运输标签服务费 | adjustments | walmart_global_shipping_label_fee | 50% | DECIMAL | NULL |
| 其他税款(费用) | sales_details | extra_data→JSON | 17% | JSON | - |
| ... (其他 1 频率字段) | (各表) | extra_data→JSON | 17% | JSON | - |

---

## 8. 迁移策略

### Phase 1: 初始化（本周）
```bash
# 执行 SQL 脚本创建表
sqlite3 backend/data/walmart_pdf_parser.db < schema.sql

# 验证表创建
sqlite3 backend/data/walmart_pdf_parser.db ".tables"
```

### Phase 2: 数据导入（下周）
- 编写数据转换脚本：新结构 → 数据库
- 批量导入 6 个 PDF 的解析结果
- 验证数据完整性

### Phase 3: 验证（下下周）
- 运行查询测试
- 验证外键约束
- 性能测试

---

## 9. SQL 查询示例

```sql
-- 查询单个语句的完整信息
SELECT h.*, s.*, r.*, o.* 
FROM statement_headers h
LEFT JOIN sales_details s ON h.id = s.header_id
LEFT JOIN refund_details r ON h.id = r.header_id
LEFT JOIN other_activities o ON h.id = o.header_id
WHERE h.source_pdf_name = 'MP_01142025_statement_summary.pdf';

-- 统计销售总额
SELECT 
    h.statement_period,
    SUM(s.product_price) as total_sales,
    SUM(r.commission) as total_refunds
FROM statement_headers h
LEFT JOIN sales_details s ON h.id = s.header_id
LEFT JOIN refund_details r ON h.id = r.header_id
GROUP BY h.statement_period;

-- 查询 WFS 服务统计
SELECT 
    h.source_pdf_name,
    w.service_type,
    w.wfs_goods_fee,
    w.wfs_ethereum_fee
FROM statement_headers h
LEFT JOIN wfs_services w ON h.id = w.header_id
WHERE w.service_type LIKE 'FBA_%';
```

---

## 10. 未来扩展计划

### 新字段处理流程
1. **识别阶段**：新字段出现在 PDF 中
2. **统计阶段**：下月重新运行 `batch_test_and_analyze.py`
3. **决策阶段**：
   - 频率 ≥ 2：添加为 DB 列（Alembic 迁移）
   - 频率 = 1：放入 JSON 列

### 建议表扩展
- `platform_adjustments` - 如果未来新增平台调整
- `promotional_activities` - 如果广告/活动字段增加
- `payment_methods` - 如果支付方式字段增加

---

## 11. 验证清单

- [ ] 创建表结构 SQL 脚本
- [ ] 执行 SQL 初始化数据库
- [ ] 编写数据转换脚本（新结构 → DB）
- [ ] 导入 6 个 PDF 的解析数据
- [ ] 验证数据完整性（行数、字段值）
- [ ] 测试外键约束
- [ ] 测试 JSON 字段查询
- [ ] 性能基准测试
- [ ] 文档更新

