# 动态板块数据库设计方案

**设计日期**: 2026-01-01  
**设计原则**: 一个 PDF = 一条语句记录，板块动态化，低频字段合并到板块"其他"字段  
**基础数据**: 6 个 PDF，31 个字段，8 个板块类型

---

## 总体架构

```
┌──────────────────────────────┐
│      statements              │  主表：每个 PDF 对应一条记录
│  (id, pdf_name, period, ...)│
└────────────┬─────────────────┘
             │ 1:N (一个 PDF 多个板块)
             │
┌────────────▼──────────────────────────────────┐
│         section_data                           │  从表：动态板块
│  (id, statement_id, section_name, data...)    │
│                                               │
│  section_name: '销售', '退款', '调整', etc.   │
│  data: JSON {field: value, ...}              │
└───────────────────────────────────────────────┘
```

---

## 表结构设计

### 表 1: statements（语句主表）

```sql
CREATE TABLE statements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pdf_name VARCHAR(255) NOT NULL UNIQUE,
    statement_period VARCHAR(100) NOT NULL,
    payment_to_you DECIMAL(12,2),
    opening_balance DECIMAL(12,2),
    reserve_fund DECIMAL(12,2),
    pending_payment DECIMAL(12,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**设计说明**:
- `pdf_name`: 原始 PDF 文件名，唯一约束
- `statement_period`: 统计区间（来自 header 板块）
- 基本余额字段（来自 header 板块，频率 100%）
- `created_at/updated_at`: 审计字段

---

### 表 2: section_data（板块数据从表）

```sql
CREATE TABLE section_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    statement_id INTEGER NOT NULL,
    section_name VARCHAR(50) NOT NULL,
    data JSON NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(statement_id) REFERENCES statements(id) ON DELETE CASCADE,
    UNIQUE(statement_id, section_name)
);
```

**设计说明**:
- `statement_id`: 外键关联到 statements
- `section_name`: 板块名称（'销售', '退款', '调整', '其他活动', 'WFS服务', 'WFS配送', '调整', 'header', 'footer'）
- `data`: JSON 格式，存储该板块的所有字段和值
- `UNIQUE(statement_id, section_name)`: 一个 PDF 每个板块只有一条记录

---

## JSON 数据结构

### 频率 ≥ 2 的字段（直接存储）

```json
{
  "section_name": "销售",
  "data": {
    "产品价格": 2000.00,
    "运输": 50.00,
    "已收税净额": 25.00,
    "净佣金": 100.00,
    "扣缴税款净额": 25.00,
    "总计": 2050.00,
    "WFS运输退款": 20.00,
    "WFS运输税退款": 5.00,
    "T沃尔玛出资的节余": 10.00,
    "销售_其他": { ... }  // 低频字段合并
  }
}
```

### 低频字段处理（频率 < 2）

**合并规则**:
- 将频率 < 2 的字段放入 `{section_name}_其他` JSON 对象
- 保留原字段名，便于回溯

**示例**:
```json
{
  "sales_section": {
    "产品价格": 2000.00,
    "运输": 50.00,
    "总计": 2050.00,
    "销售_其他": {
      "其他税款(费用)": 10.00,
      "原字段计数": 1
    }
  }
}
```

---

## 字段频率分类

### 按板块列出（频率≥2 vs <2）

| 板块 | 频率≥2的字段 | 频率<2的字段 |
|------|-----------|-----------|
| **header** | 统计区间(100%), 向您支付的金额(100%), 期初余额(100%), 备用金(100%), 回款等待(100%), 期末余额(83%) | - |
| **销售** | 产品价格(100%), 运输(100%), 已收税净额(100%), 净佣金(100%), 扣缴税款净额(100%), 总计(100%), WFS运输退款(83%), WFS运输税退款(83%), T沃尔玛出资的节余(83%) | 其他税款(费用)(17%) |
| **退款** | 佣金(100%), 产品价格(100%), 运输(100%), 已收税净额(100%), 扣缴税款净额(100%), 总计(100%), WFS总折扣(100%), T沃尔玛出资的节余(83%) | T沃尔玛出资的节余总额(17%) |
| **其他活动** | 沃尔玛产品广告(100%) | - |
| **调整** | 沃尔玛全球运输标签服务费(50%) | 退货沃尔玛运输服务费(17%) |
| **WFS商品服务** | WFS总折扣(100%), WFS商品费(67%), WFS以太坊费(67%) | WFS退货费(17%), 世界FS调整(17%), WFSRC库存支出(17%) |
| **WFS配送服务** | - | WFS配送费(17%), WFS仓储费(17%) |
| **footer** | 向您支付的金额(100%) | 专业列表(17%), 其他(17%) |

---

## 导入数据流

```
PDF 文件
  ↓
parse_pdf_direct()
  ↓ (Step 5)
jg_structured_data()
  ↓ 返回
{
  "sections": {
    "header": [{field, value, ...}, ...],
    "销售": [{field, value, ...}, ...],
    "退款": [{field, value, ...}, ...],
    ...
  },
  "metadata": {...}
}
  ↓
db_import_structured_data()
  ├─→ 创建 statement 记录
  └─→ 为每个 section 创建 section_data 记录
       ├─ 识别频率≥2的字段 → 直接存储
       └─ 频率<2的字段 → 合并到 {section_name}_其他
  ↓
INSERT INTO statements & section_data
```

---

## 查询示例

### 查询 1: 获取单个 PDF 的完整数据

```sql
SELECT 
    s.id, s.pdf_name, s.statement_period,
    sd.section_name, sd.data
FROM statements s
LEFT JOIN section_data sd ON s.id = sd.statement_id
WHERE s.pdf_name = 'MP_01142025_statement_summary.pdf'
ORDER BY s.id, sd.section_name;
```

### 查询 2: 汇总某月的销售额

```sql
SELECT 
    s.statement_period,
    json_extract(sd.data, '$.产品价格') as sales_price,
    json_extract(sd.data, '$.总计') as sales_total
FROM statements s
LEFT JOIN section_data sd ON s.id = sd.statement_id
WHERE sd.section_name = '销售'
  AND s.statement_period LIKE '2025年1月%'
ORDER BY s.pdf_name;
```

### 查询 3: 对比退款率

```sql
SELECT 
    s.statement_period,
    SUM(CAST(json_extract(sales.data, '$.总计') AS REAL)) as total_sales,
    SUM(CAST(json_extract(refund.data, '$.总计') AS REAL)) as total_refunds,
    ROUND(
        SUM(CAST(json_extract(refund.data, '$.总计') AS REAL)) / 
        SUM(CAST(json_extract(sales.data, '$.总计') AS REAL)) * 100, 
        2
    ) as refund_rate
FROM statements s
LEFT JOIN section_data sales ON s.id = sales.statement_id AND sales.section_name = '销售'
LEFT JOIN section_data refund ON s.id = refund.statement_id AND refund.section_name = '退款'
GROUP BY s.statement_period
ORDER BY s.statement_period;
```

### 查询 4: 查看低频字段（{section_name}_其他）

```sql
SELECT 
    s.pdf_name,
    sd.section_name,
    json_extract(sd.data, '$.' || sd.section_name || '_其他') as other_fields
FROM statements s
LEFT JOIN section_data sd ON s.id = sd.statement_id
WHERE json_extract(sd.data, '$.' || sd.section_name || '_其他') IS NOT NULL
ORDER BY s.pdf_name, sd.section_name;
```

---

## 索引策略

```sql
CREATE INDEX idx_section_data_statement_id ON section_data(statement_id);
CREATE INDEX idx_section_data_section_name ON section_data(section_name);
CREATE INDEX idx_statements_period ON statements(statement_period);
CREATE INDEX idx_statements_pdf_name ON statements(pdf_name);
```

---

## 导入脚本逻辑

### 伪代码

```python
def import_structured_data(pdf_name: str, jg_data: dict):
    """
    将 jg_structured_data() 的输出导入到数据库
    
    Args:
        pdf_name: PDF 文件名
        jg_data: jg_structured_data() 的返回值，包含 sections 和 metadata
    """
    
    # Step 1: 创建 statement 记录
    statement_id = insert_statement(
        pdf_name=pdf_name,
        statement_period=extract_from_header(jg_data, '统计区间'),
        payment_to_you=extract_from_header(jg_data, '向您支付的金额'),
        opening_balance=extract_from_header(jg_data, '期初余额'),
        ...
    )
    
    # Step 2: 为每个板块创建 section_data 记录
    sections = jg_data['sections']
    
    for section_name, items in sections.items():
        # 将 items (list) 转换为 dict
        section_dict = {item['field']: item['value'] for item in items}
        
        # Step 3: 合并低频字段到 {section_name}_其他
        high_freq_fields = FREQUENCY_MAP[section_name]  # 查询频率表
        other_fields = {}
        
        for field_name, field_value in section_dict.items():
            if field_name not in high_freq_fields:
                # 低频字段
                other_fields[field_name] = field_value
            # 高频字段直接保留在 section_dict 中
        
        # 如果有低频字段，添加到 section_dict
        if other_fields:
            section_dict[f'{section_name}_其他'] = other_fields
        
        # Step 4: 写入 section_data 表
        insert_section_data(
            statement_id=statement_id,
            section_name=section_name,
            data=section_dict  # 转换为 JSON
        )
```

---

## 数据库初始化

```sql
-- 创建表
CREATE TABLE statements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pdf_name VARCHAR(255) NOT NULL UNIQUE,
    statement_period VARCHAR(100),
    payment_to_you DECIMAL(12,2),
    opening_balance DECIMAL(12,2),
    reserve_fund DECIMAL(12,2),
    pending_payment DECIMAL(12,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE section_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    statement_id INTEGER NOT NULL,
    section_name VARCHAR(50) NOT NULL,
    data JSON NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(statement_id) REFERENCES statements(id) ON DELETE CASCADE,
    UNIQUE(statement_id, section_name)
);

-- 创建索引
CREATE INDEX idx_section_data_statement_id ON section_data(statement_id);
CREATE INDEX idx_section_data_section_name ON section_data(section_name);
CREATE INDEX idx_statements_period ON statements(statement_period);
CREATE INDEX idx_statements_pdf_name ON statements(pdf_name);
```

---

## 优势总结

| 特点 | 优势 |
|------|------|
| **动态板块** | 新增板块无需修改 schema，直接写入 section_name |
| **简洁结构** | 只需 2 个表，易于维护和理解 |
| **灵活扩展** | 新字段自动进入 JSON，无需迁移 |
| **数据完整性** | 低频字段保存在 {section_name}_其他，可完整回溯 |
| **查询易用** | 同一字段在不同板块分别查询，避免歧义 |
| **性能优化** | 索引支持按板块、时间段快速查询 |

---

## 下一步

1. ✅ 确认此设计方案
2. 清空现有数据库
3. 生成 SQL 初始化脚本
4. 编写导入脚本（集成到执行代码）
5. 生成测试和演示查询

