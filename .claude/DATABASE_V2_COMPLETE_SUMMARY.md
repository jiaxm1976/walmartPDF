# 数据库重新设计 - 完整方案总结

**版本**: V2.0 (动态板块设计)  
**完成时间**: 2026-01-01  
**状态**: ✅ 设计完成，待实施

---

## 为什么重新设计？

### V1 的问题（已废弃）
- ❌ 过度规范化：7 个表，复杂的外键关系
- ❌ 字段冗余：同一字段在多个表中重复
- ❌ 难以扩展：新增板块需要新建表
- ❌ 查询复杂：多重 LEFT JOIN，容易出错

### V2 的改进（当前设计）
- ✅ 简洁设计：仅 2 个表（statements + section_data）
- ✅ 动态板块：新增板块无需修改 schema
- ✅ 自动合并：低频字段自动合并，减少列数
- ✅ 易于维护：查询更直观，代码更简洁

---

## 核心设计理念

### 1. 一个 PDF = 一条 statement 记录

```
PDF 文件 → parse_pdf_direct() → jg_structured_data()
                                      ↓
                           {sections, metadata}
                                      ↓
                          import_jg_data() → DB
                                      ↓
                         statement (1 条) + section_data (N 条)
```

### 2. 板块动态化

不硬编码板块类型，而是根据实际数据创建：
- 现有板块：header, 销售, 退款, 调整, 其他活动, WFS商品, WFS配送, footer
- 未来板块：无需修改 schema，直接写入

### 3. 低频字段自动合并

**合并规则**:
```
频率 < 2 的字段 → 合并到 {section_name}_其他 (JSON 格式)
频率 ≥ 2 的字段 → 直接保存（顶级字段）
```

**示例**:
```json
销售板块：{
  "产品价格": 2000,          // 频率 100%，顶级
  "运输": 50,               // 频率 100%，顶级
  "销售_其他": {            // 低频字段合并
    "其他税款(费用)": 10
  }
}
```

---

## 表结构设计

### statements 表（主表）

```
┌─────────────────────────────────────┐
│ id (PK)                             │
│ pdf_name (UNIQUE) → 原始文件名       │
│ statement_period → 统计区间          │
│ payment_to_you → 应付金额            │
│ opening_balance → 期初余额           │
│ reserve_fund → 备用金                │
│ pending_payment → 回款等待           │
│ created_at, updated_at              │
└─────────────────────────────────────┘
```

**用途**: 存储每个 PDF 的基本信息（来自 header 板块）

### section_data 表（从表）

```
┌───────────────────────────────────────┐
│ id (PK)                               │
│ statement_id (FK) → 关联 statements   │
│ section_name → '销售'/'退款'/etc      │
│ data (JSON) → {字段名: 值, ...}       │
│ created_at                            │
│ UNIQUE(statement_id, section_name)    │
└───────────────────────────────────────┘
```

**用途**: 存储每个板块的数据（一个 PDF 多条记录）

---

## 数据导入流程

### 完整导入链路

```
1. PDF 解析
   pdf → parse_pdf_direct() → Step 5: jg_structured_data()
   
2. 结构化数据
   {
     "sections": {
       "header": [items],
       "销售": [items],
       ...
     },
     "metadata": {...}
   }
   
3. 数据库导入 (StructuredDataImporter)
   ├─ 读取 sections
   ├─ 提取 header 信息 → 插入 statements
   ├─ 对每个 section:
   │  ├─ 识别低频字段 (查询 field_frequency 表)
   │  ├─ 合并到 {section_name}_其他
   │  └─ 插入 section_data
   └─ 提交事务
   
4. 数据库
   statements: 1 条记录
   section_data: N 条记录 (N = 板块数)
```

---

## 字段频率映射

### 频率 ≥ 2 的字段（19 个）

| 板块 | 字段列表 |
|------|--------|
| header | 统计区间, 向您支付的金额, 期初余额, 备用金, 回款等待, 期末余额 |
| 销售 | 产品价格, 运输, 已收税净额, 净佣金, 扣缴税款净额, 总计, WFS运输退款, WFS运输税退款, T沃尔玛出资的节余 |
| 退款 | 佣金, 产品价格, 运输, 已收税净额, 扣缴税款净额, 总计, WFS总折扣, T沃尔玛出资的节余 |
| 其他活动 | 沃尔玛产品广告 |
| 调整 | 沃尔玛全球运输标签服务费 |
| WFS | WFS总折扣, WFS商品费, WFS以太坊费 |
| footer | 向您支付的金额 |

### 频率 < 2 的字段（12 个）

这些字段自动合并到对应板块的 `{section_name}_其他` 字段中：

```
销售_其他:       其他税款(费用)
退款_其他:       T沃尔玛出资的节余总额
调整_其他:       退货沃尔玛运输服务费
WFS_其他:        WFS退货费, 世界FS调整, WFSRC库存支出, WFS配送费, WFS仓储费
footer_其他:     专业列表, 其他
```

---

## 核心优势

| 方面 | V1（已废弃） | V2（当前） |
|------|-----------|---------|
| **表数** | 7 个表 | 2 个表 |
| **主键关系** | 复杂多层 | 简单 1:N |
| **新增板块** | 需创建新表 | 无需修改 schema |
| **新增字段** | 需修改表结构 | 自动进入 JSON |
| **查询复杂性** | 多重 JOIN | 单表 + JSON 提取 |
| **维护成本** | 高（多表同步） | 低（集中式） |
| **灵活性** | 低（硬编码） | 高（动态化） |

---

## 实施清单

### 准备阶段
- [x] 完成 V2 设计文档
- [x] 生成 SQL 初始化脚本
- [x] 编写导入模块 (StructuredDataImporter)
- [x] 生成快速参考指南

### 执行阶段（待做）
- [ ] 备份旧数据库（如有）
- [ ] 清空数据库文件
- [ ] 执行 SQL 脚本初始化
- [ ] 验证表结构
- [ ] 测试导入模块
- [ ] 导入实际 PDF 数据
- [ ] 验证数据完整性

### 验证阶段（待做）
- [ ] 执行查询验证
- [ ] 检查低频字段合并
- [ ] 性能测试
- [ ] 文档更新

---

## 文件清单

| 文件 | 用途 | 状态 |
|------|------|------|
| `.claude/DATABASE_DESIGN_V2_DYNAMIC_SECTIONS.md` | 详细设计文档 | ✅ |
| `.claude/DATABASE_V2_QUICK_REFERENCE.md` | 快速参考 | ✅ |
| `backend/database/schema_v2_dynamic.sql` | SQL 初始化脚本 | ✅ |
| `backend/database/structured_importer.py` | 导入模块 | ✅ |
| `DATABASE_V2_SUMMARY.md` | 本文档 | ✅ |

---

## 快速验证

### 初始化数据库

```bash
# 清空旧数据库
rm backend/data/walmart_pdf_parser.db

# 执行初始化脚本
sqlite3 backend/data/walmart_pdf_parser.db < backend/database/schema_v2_dynamic.sql

# 验证表结构
sqlite3 backend/data/walmart_pdf_parser.db ".schema"
```

### 测试导入

```python
from backend.database.structured_importer import StructuredDataImporter
import json

# 初始化导入器
importer = StructuredDataImporter()
importer.connect()

# 读取示例 jg_structured_data
with open('example_structured_data.json') as f:
    jg_data = json.load(f)

# 导入数据
statement_id = importer.import_jg_data('MP_01142025.pdf', jg_data)
print(f"✓ 导入成功: statement_id={statement_id}")

importer.disconnect()
```

### 验证查询

```sql
-- 查看已导入的数据
SELECT COUNT(*) FROM statements;
SELECT COUNT(*) FROM section_data;

-- 查看板块列表
SELECT DISTINCT section_name FROM section_data;

-- 查看具体数据
SELECT * FROM section_data WHERE section_name = '销售' LIMIT 1;
```

---

## 设计对比

### 同一字段在多个板块的处理

**场景**: "产品价格"在销售和退款都存在

**V1 方式（问题）**:
```
sales_details.product_price (销售的产品价格)
refund_details.product_price (退款的产品价格)
→ 两个表，容易混淆，JOIN 时容易出错
```

**V2 方式（改进）**:
```
section_data (statement_id=1, section_name='销售')
  data: {"产品价格": 2000, ...}

section_data (statement_id=1, section_name='退款')
  data: {"产品价格": 100, ...}
  
→ 同一个表，按板块区分，清晰直观
```

---

## 答疑

### Q1: 为什么不用多列（JSONB）存储所有板块数据？

**A**: 考虑过，但有缺点：
- 难以按板块查询（需要深层 JSON 遍历）
- 无法利用数据库索引
- 扩展性差（添加新板块需要修改 JSON 结构）

**一条记录一个板块**的方案更好：
- 按板块高效查询
- JSON 保持简洁（仅该板块数据）
- 支持动态新增板块

### Q2: 低频字段为什么要合并？

**A**: 避免表列数膨胀：
- 12 个低频字段，不合并需要 12 个额外列
- 大多数 PDF 不会用到这些字段 → 大量 NULL
- 合并到 JSON → 占用空间小，查询灵活

### Q3: 频率阈值为什么是 2？

**A**: 基于 6 个 PDF 的分析：
- 频率 ≥ 2：至少在 2 个 PDF 中出现（业务相关）
- 频率 < 2：只在 1 个 PDF 中出现（可能异常）

未来可根据数据调整（修改 `field_frequency` 表）

---

## 下一步

1. **确认设计** ← 你在这里
2. **初始化数据库** → 执行 SQL 脚本
3. **测试导入** → 运行导入模块
4. **批量导入** → 导入所有 PDF
5. **性能验证** → 查询测试
6. **生产部署** → 正式上线

---

**设计已完成，随时可开始实施！🚀**

如有任何问题或需要调整，请提出！

