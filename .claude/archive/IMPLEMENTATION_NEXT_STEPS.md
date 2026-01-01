# V2 数据库设计 - 实施后续步骤

**项目状态**: ✅ 设计完成，等待实施  
**创建时间**: 2026-01-01  
**下一阶段**: Phase 2 - 数据库初始化

---

## 📋 现状总结

### 已完成的交付物

#### 1️⃣ 核心设计文档
- [DATABASE_DESIGN_V2_DYNAMIC_SECTIONS.md](./ DATABASE_DESIGN_V2_DYNAMIC_SECTIONS.md) - 详细技术规格
- [DATABASE_V2_COMPLETE_SUMMARY.md](./DATABASE_V2_COMPLETE_SUMMARY.md) - 完整总结与 FAQ
- [DATABASE_V2_QUICK_REFERENCE.md](./DATABASE_V2_QUICK_REFERENCE.md) - 快速参考指南
- [DESIGN_V2_OVERVIEW.txt](./DESIGN_V2_OVERVIEW.txt) - 可视化架构总览

#### 2️⃣ 实现代码
- [schema_v2_dynamic.sql](../database/schema_v2_dynamic.sql) - SQL 初始化脚本（200+ 行）
- [structured_importer.py](../database/structured_importer.py) - Python 导入模块（336 行）

#### 3️⃣ 设计特点
- ✅ **简洁**: 仅 2 个主表 (statements + section_data)
- ✅ **动态**: 板块无需硬编码，可自动扩展
- ✅ **自动化**: 低频字段自动合并到 JSON
- ✅ **可查询**: 支持 SQL 直接查询和数据聚合

---

## 🚀 后续执行 4 阶段

### Phase 1: ✅ 设计与代码生成 (已完成)
```
✓ 需求分析与澄清
✓ V2 设计定义与批准
✓ SQL 脚本编写
✓ Python 导入模块实现
✓ 文档与示例完成
```

### Phase 2: ⏳ 数据库初始化 (下一步)

**目标**: 清空数据库，执行新 schema

**步骤**:

```bash
# 1. 备份现有数据库（可选）
cp backend/data/walmart_pdf_parser.db backend/data/walmart_pdf_parser.db.backup

# 2. 删除旧数据库
rm backend/data/walmart_pdf_parser.db

# 3. 初始化新 schema
sqlite3 backend/data/walmart_pdf_parser.db < backend/database/schema_v2_dynamic.sql

# 4. 验证表结构
sqlite3 backend/data/walmart_pdf_parser.db ".schema"
```

**预期结果**:
- statements 表创建 ✓
- section_data 表创建 ✓
- field_frequency 表创建（31 行数据预加载）✓
- db_config 表创建 ✓
- 2 个视图创建 ✓

**验证命令**:
```bash
sqlite3 backend/data/walmart_pdf_parser.db "SELECT COUNT(*) as table_count FROM sqlite_master WHERE type='table';"
# 预期输出: 4 (statements, section_data, field_frequency, db_config)

sqlite3 backend/data/walmart_pdf_parser.db "SELECT COUNT(*) FROM field_frequency;"
# 预期输出: 31
```

---

### Phase 3: ⏳ 单 PDF 导入测试 (验证逻辑)

**目标**: 测试导入流程是否正确

**前置条件**:
- 已执行 Phase 2（数据库初始化完成）
- 有一个 jg_structured_data() 的输出（JSON 格式）

**步骤**:

```python
# 获取 jg_structured_data 输出（从 PDF 解析流程中获取）
from backend.app.services.pdf_parser import jg_structured_data

# 假设已有 pdf_path = 'backend/tests/test_data/MP_01142025.pdf'
pdf_path = 'backend/tests/test_data/MP_01142025.pdf'
structured_data = jg_structured_data(pdf_path)

# 导入到数据库
from backend.database.structured_importer import StructuredDataImporter

importer = StructuredDataImporter('backend/data/walmart_pdf_parser.db')
importer.connect()
statement_id = importer.import_jg_data('MP_01142025.pdf', structured_data)
importer.disconnect()

print(f"✓ 成功导入，statement_id = {statement_id}")
```

**验证查询**:
```sql
-- 查看 statements 表
SELECT * FROM statements WHERE pdf_name = 'MP_01142025.pdf';

-- 查看该 PDF 的所有板块
SELECT section_name, json_extract(data, '$') as data_preview 
FROM section_data 
WHERE statement_id = (SELECT id FROM statements WHERE pdf_name = 'MP_01142025.pdf');

-- 查看低频字段（示例：销售板块的"其他"字段）
SELECT json_extract(data, '$.销售_其他') as 低频字段 
FROM section_data 
WHERE section_name = '销售' AND statement_id = 1;
```

**预期结果**:
- ✓ 1 条 statements 记录创建
- ✓ N 条 section_data 记录创建（N = 该 PDF 中的板块数，通常 8 个）
- ✓ 低频字段正确合并到 JSON

---

### Phase 4: ⏳ 批量导入与验证 (生产化)

**目标**: 导入所有 PDF，验证完整性

**步骤**:

```python
from backend.database.structured_importer import StructuredDataImporter
from pathlib import Path
import json

# 获取所有 PDF 的 jg_structured_data
test_data_dir = Path('backend/tests/test_data')
json_outputs = {}  # 存储所有 PDF 的 jg_structured_data

for pdf_file in test_data_dir.glob('*.pdf'):
    from backend.app.services.pdf_parser import jg_structured_data
    jg_data = jg_structured_data(str(pdf_file))
    json_outputs[pdf_file.name] = jg_data

# 批量导入
importer = StructuredDataImporter('backend/data/walmart_pdf_parser.db')
importer.connect()

for pdf_name, jg_data in json_outputs.items():
    statement_id = importer.import_jg_data(pdf_name, jg_data)
    print(f"✓ {pdf_name} → statement_id={statement_id}")

importer.disconnect()
```

**验证查询**:
```sql
-- 统计导入的 PDF 数量
SELECT COUNT(*) as total_pdfs FROM statements;

-- 统计总板块数
SELECT COUNT(*) as total_sections FROM section_data;

-- 按板块统计分布
SELECT section_name, COUNT(*) as count 
FROM section_data 
GROUP BY section_name
ORDER BY count DESC;

-- 检查低频字段合并（示例）
SELECT statement_id, section_name, 
       json_keys(json_extract(data, '$.' || section_name || '_其他')) as 其他字段列表
FROM section_data
WHERE json_extract(data, '$.' || section_name || '_其他') IS NOT NULL
LIMIT 10;
```

**预期结果**:
- ✓ 6 条 statements 记录（一个 PDF 一条）
- ✓ ~48 条 section_data 记录（约 6 × 8 板块）
- ✓ 所有低频字段正确归档

---

### Phase 5: ⏳ 查询验证 (功能测试)

**目标**: 验证常见查询模式正确

**查询 1: 获取单个 PDF 的完整数据**
```sql
SELECT 
  s.pdf_name,
  s.statement_period,
  s.payment_to_you,
  sd.section_name,
  sd.data
FROM statements s
LEFT JOIN section_data sd ON s.id = sd.statement_id
WHERE s.pdf_name = 'MP_01142025.pdf';
```

**查询 2: 按板块聚合销售额**
```sql
-- 需要先确认数据结构
SELECT 
  section_name,
  SUM(json_extract(data, '$.产品价格')) as total_product_price
FROM section_data
WHERE section_name = '销售'
GROUP BY statement_id;
```

**查询 3: 对比退款率**
```sql
SELECT 
  s.pdf_name,
  json_extract((SELECT data FROM section_data WHERE section_name='销售' AND statement_id=s.id), '$.产品价格') as 销售,
  json_extract((SELECT data FROM section_data WHERE section_name='退款' AND statement_id=s.id), '$.产品价格') as 退款,
  ROUND(
    json_extract((SELECT data FROM section_data WHERE section_name='退款' AND statement_id=s.id), '$.产品价格') /
    json_extract((SELECT data FROM section_data WHERE section_name='销售' AND statement_id=s.id), '$.产品价格') * 100, 2
  ) as 退款率_百分比
FROM statements s;
```

---

## 📝 执行检查清单

### Phase 2 - 数据库初始化
- [ ] 备份现有数据库（如需要）
- [ ] 删除 backend/data/walmart_pdf_parser.db
- [ ] 执行 SQL 初始化脚本
- [ ] 验证表结构（4 个表 + 2 个视图）
- [ ] 验证 field_frequency 表有 31 行数据

### Phase 3 - 单 PDF 导入
- [ ] 获取一个 PDF 的 jg_structured_data 输出
- [ ] 使用 StructuredDataImporter 导入
- [ ] 验证 statements 表新增 1 条记录
- [ ] 验证 section_data 表新增 N 条记录
- [ ] 检查低频字段是否正确合并到 JSON

### Phase 4 - 批量导入
- [ ] 导入所有 6 个测试 PDF
- [ ] 验证 statements 表有 6 条记录
- [ ] 验证 section_data 表约 48 条记录
- [ ] 验证所有板块数据完整

### Phase 5 - 查询验证
- [ ] 单 PDF 查询可成功执行
- [ ] 销售额聚合查询可正确输出
- [ ] 退款率对比查询可正确计算

---

## 📂 核心文件索引

| 文件 | 用途 | 状态 |
|------|------|------|
| schema_v2_dynamic.sql | SQL 初始化脚本 | ✅ 就绪 |
| structured_importer.py | Python 导入模块 | ✅ 就绪 |
| DATABASE_DESIGN_V2_DYNAMIC_SECTIONS.md | 详细设计规格 | ✅ 就绪 |
| DATABASE_V2_COMPLETE_SUMMARY.md | 完整总结 | ✅ 就绪 |
| DATABASE_V2_QUICK_REFERENCE.md | 快速参考 | ✅ 就绪 |
| DESIGN_V2_OVERVIEW.txt | 可视化总览 | ✅ 就绪 |

---

## 💡 关键要点

1. **动态板块**: section_name 无需硬编码，支持无限扩展
2. **自动合并**: 频率 < 2 的字段自动归档到 {section_name}_其他
3. **简洁查询**: 可直接用 SQL 查询 JSON 字段，无需复杂 JOIN
4. **可审计**: created_at/updated_at 记录所有变更时间

---

## ❓ 常见问题

**Q: 为什么只有 2 个表？**  
A: 动态板块设计避免了硬编码表结构，低频字段合并减少了列数

**Q: JSON 存储的性能如何？**  
A: SQLite JSON 扩展优化了性能，对于 Walmart 数据量完全足够

**Q: 如何添加新板块？**  
A: 无需修改 schema，直接写入 section_data 表，section_name 为新板块名

**Q: 如何查询低频字段？**  
A: 使用 json_extract(data, '$.{section_name}_其他.字段名')

---

## 🎯 下一步行动

1. **立即**: 阅读本文，理解 4 阶段计划
2. **阶段 2**: 执行数据库初始化
3. **阶段 3**: 进行单 PDF 导入测试
4. **阶段 4**: 批量导入所有 PDF
5. **阶段 5**: 验证所有查询模式正确

---

**预计总时间**: 2-4 小时（取决于 PDF 解析速度）  
**风险**: 低（数据库清空前已备份）  
**可回退**: 是（保留 .backup 文件）
