# 数据库设计 V2 - 快速参考

**设计版本**: V2.0 (动态板块设计)  
**更新日期**: 2026-01-01  
**状态**: 设计完成，待实施

---

## 📊 核心架构一览

```
┌─────────────────────────────────────────┐
│ 一个 PDF = 一条 statement 记录           │
├──────────────────┬──────────────────────┤
│ id               │ pdf_name             │
│ statement_period │ payment_to_you, ...  │
└──────────────────┴──────┬───────────────┘
                          │ 1:N
                    ┌─────▼──────────┐
                    │ section_data   │ (动态板块)
                    ├────────────────┤
                    │ statement_id   │ (FK)
                    │ section_name   │ (销售/退款/etc)
                    │ data (JSON)    │ (字段 + 值)
                    └────────────────┘
```

---

## 🎯 表设计速查

### statements 表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT PK | 主键 |
| pdf_name | VARCHAR(255) | PDF 文件名（唯一） |
| statement_period | VARCHAR(100) | 统计区间（来自 header） |
| payment_to_you | DECIMAL | 应付金额 |
| opening_balance | DECIMAL | 期初余额 |
| reserve_fund | DECIMAL | 备用金 |
| pending_payment | DECIMAL | 回款等待 |
| created_at | TIMESTAMP | 创建时间 |

### section_data 表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT PK | 主键 |
| statement_id | INT FK | 关联 statement |
| section_name | VARCHAR(50) | 板块名称（销售/退款/etc） |
| data | JSON | 该板块的所有字段（频率≥2 + {section_name}_其他） |
| created_at | TIMESTAMP | 创建时间 |

---

## 📝 数据结构示例

### 原始数据（来自 jg_structured_data）

```json
{
  "sections": {
    "销售": [
      {"field": "产品价格", "value": 2000.00, ...},
      {"field": "运输", "value": 50.00, ...},
      {"field": "其他税款(费用)", "value": 10.00, ...}
    ]
  }
}
```

### 写入数据库后（section_data.data）

```json
{
  "产品价格": 2000.00,
  "运输": 50.00,
  "销售_其他": {
    "其他税款(费用)": 10.00
  }
}
```

**说明**: 频率<2 的字段自动合并到 `{section_name}_其他`

---

## 🔧 实施步骤

### Step 1: 初始化数据库

```bash
# 清空旧数据库
rm backend/data/walmart_pdf_parser.db

# 执行初始化脚本
sqlite3 backend/data/walmart_pdf_parser.db < backend/database/schema_v2_dynamic.sql
```

### Step 2: 导入单个 PDF

```python
from backend.database.structured_importer import StructuredDataImporter

# 初始化导入器
importer = StructuredDataImporter('backend/data/walmart_pdf_parser.db')
importer.connect()

# 假设已有 jg_data (从 jg_structured_data() 得到)
statement_id = importer.import_jg_data('MP_01142025.pdf', jg_data)

importer.disconnect()
```

---

## 💾 字段频率一览

### 频率 ≥ 2（直接存储）

**header**: 统计区间, 向您支付的金额, 期初余额, 备用金, 回款等待, 期末余额  
**销售**: 产品价格, 运输, 已收税净额, 净佣金, 扣缴税款净额, 总计, WFS运输退款, WFS运输税退款, T沃尔玛出资的节余  
**退款**: 佣金, 产品价格, 运输, 已收税净额, 扣缴税款净额, 总计, WFS总折扣, T沃尔玛出资的节余  
**其他活动**: 沃尔玛产品广告  
**调整**: 沃尔玛全球运输标签服务费  
**WFS**: WFS总折扣, WFS商品费, WFS以太坊费  
**footer**: 向您支付的金额

### 频率 < 2（合并到 {section_name}_其他）

**销售_其他**: 其他税款(费用)  
**退款_其他**: T沃尔玛出资的节余总额  
**调整_其他**: 退货沃尔玛运输服务费  
**WFS_其他**: WFS退货费, 世界FS调整, WFSRC库存支出, WFS配送费, WFS仓储费  
**footer_其他**: 专业列表, 其他

---

## 🔍 查询示例

### 查询 1: 获取一个 PDF 的完整数据

```sql
SELECT s.pdf_name, s.statement_period, sd.section_name, sd.data
FROM statements s
LEFT JOIN section_data sd ON s.id = sd.statement_id
WHERE s.pdf_name = 'MP_01142025.pdf'
ORDER BY sd.section_name;
```

### 查询 2: 汇总销售额（按月）

```sql
SELECT 
    s.statement_period,
    json_extract(sd.data, '$.产品价格') as product_price,
    json_extract(sd.data, '$.总计') as total
FROM statements s
LEFT JOIN section_data sd ON s.id = sd.statement_id
WHERE sd.section_name = '销售'
ORDER BY s.statement_period;
```

### 查询 3: 计算退款率

```sql
SELECT 
    s.statement_period,
    CAST(json_extract(sales.data, '$.总计') AS REAL) as sales_total,
    CAST(json_extract(refund.data, '$.总计') AS REAL) as refund_total,
    ROUND(
        CAST(json_extract(refund.data, '$.总计') AS REAL) / 
        CAST(json_extract(sales.data, '$.总计') AS REAL) * 100,
        2
    ) as refund_rate
FROM statements s
LEFT JOIN section_data sales ON s.id = sales.statement_id AND sales.section_name = '销售'
LEFT JOIN section_data refund ON s.id = refund.statement_id AND refund.section_name = '退款';
```

### 查询 4: 查看低频字段

```sql
SELECT 
    s.pdf_name,
    sd.section_name,
    json_extract(sd.data, '$.' || sd.section_name || '_其他') as other_fields
FROM statements s
LEFT JOIN section_data sd ON s.id = sd.statement_id
WHERE json_extract(sd.data, '$.' || sd.section_name || '_其他') IS NOT NULL;
```

---

## 📌 关键特性

| 特性 | 说明 |
|------|------|
| **动态板块** | 新增板块无需修改 schema，直接写 section_name |
| **自动合并** | 导入时自动识别和合并低频字段 |
| **数据完整性** | 低频字段保存在 JSON，可完整回溯 |
| **灵活查询** | 同字段在不同板块分别存储，避免歧义 |
| **简洁设计** | 仅 2 个表，易于维护 |

---

## ⚠️ 注意事项

1. **JSON 查询**: SQLite JSON 函数支持 (json_extract, json_array_length 等)
2. **数值处理**: 查询时使用 `CAST(...AS REAL)` 转换数值类型
3. **字符编码**: 确保 JSON 中文字符正确编码（使用 `ensure_ascii=False`）
4. **频率阈值**: 当前设为 2，可通过 `field_frequency` 表调整

---

**设计完成，可随时实施！🚀**