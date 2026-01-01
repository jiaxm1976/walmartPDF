# 🚀 Walmart PDF 数据库 V2 - 快速开始指南

**预计时间**: 9 分钟  
**难度**: ⭐ 简单  
**前置条件**: Python 3.9+，SQLite3

---

## ⚡ 30 秒快速开始

```bash
# 1. 初始化数据库 (1 分钟)
python scripts/init_database_v2.py

# 2. 测试单 PDF 导入 (2 分钟)
python scripts/test_single_pdf_import.py

# 3. 批量导入所有 PDF (5 分钟)
python scripts/batch_import_all_pdfs.py

# 4. 验证查询 (1 分钟)
python scripts/verify_queries.py

# ✓ 完成！数据库已准备就绪
```

---

## 📋 完整步骤

### 步骤 1️⃣: 初始化数据库

```bash
python scripts/init_database_v2.py
```

**预期输出**:
```
✓ 已备份数据库至: backend/data/backups/walmart_pdf_parser_20260101_120000.db
✓ 已删除旧数据库
✓ schema 初始化完成
✓ 已创建 4 个表
✓ 已创建 2 个视图
✓ field_frequency 表有 31 条记录
```

**验证**:
```bash
sqlite3 backend/data/walmart_pdf_parser.db "SELECT COUNT(*) FROM field_frequency;"
# 预期输出: 31
```

### 步骤 2️⃣: 测试单 PDF 导入

```bash
python scripts/test_single_pdf_import.py
```

**预期输出**:
```
✓ 正在解析 PDF: MP_01142025.pdf
✓ 解析完成，包含 8 个板块
✓ 已连接数据库
✓ 导入成功，statement_id = 1
✓ statements 表: 1 条记录
✓ section_data 表: 8 条记录
✓ 低频字段合并: 销售._其他
```

### 步骤 3️⃣: 批量导入所有 PDF

```bash
python scripts/batch_import_all_pdfs.py
```

**预期输出**:
```
✓ 找到 6 个 PDF 文件
✓ 已导入 6 个 PDF
✓ 已创建 48 个板块记录
✓ 成功率: 100%
```

### 步骤 4️⃣: 验证查询

```bash
python scripts/verify_queries.py
```

**预期输出**:
```
✓ 查询 1 完成 - 单 PDF 数据获取成功
✓ 查询 2 完成 - 板块统计完成
✓ 查询 3 完成 - 字段提取成功
✓ 查询 4 完成 - 低频字段合并验证成功
✓ 数据完整性检查通过
```

---

## 🔍 快速验证

```bash
# 查看 statements 表
sqlite3 backend/data/walmart_pdf_parser.db \
  "SELECT COUNT(*) as '已导入的PDF' FROM statements;"

# 查看 section_data 表
sqlite3 backend/data/walmart_pdf_parser.db \
  "SELECT COUNT(*) as '已导入的板块' FROM section_data;"

# 查看板块分布
sqlite3 backend/data/walmart_pdf_parser.db \
  "SELECT section_name, COUNT(*) FROM section_data GROUP BY section_name;"
```

---

## 📊 设计要点

| 特性 | 说明 |
|------|------|
| **表结构** | 2 个主表 (statements + section_data) |
| **板块模式** | 动态化，无需硬编码 |
| **低频字段** | 自动合并到 {section_name}_其他 JSON |
| **频率阈值** | 字段频率 < 2 为低频 |
| **查询** | 支持 SQL + JSON 提取 |

---

## 💾 数据库备份

所有备份自动保存在 `backend/data/backups/`

```bash
# 查看备份列表
ls -la backend/data/backups/

# 恢复备份（如需要）
cp backend/data/backups/walmart_pdf_parser_20260101_120000.db \
   backend/data/walmart_pdf_parser.db
```

---

## ❓ 常见问题

**Q: 可以跳过某些步骤吗？**  
A: 建议按顺序执行。Phase 2 → Phase 3 → Phase 4 → Phase 5

**Q: 导入失败怎么办？**  
A: 查看脚本输出中的错误信息，或检查 PDF 文件是否完整

**Q: 可以重新运行吗？**  
A: 可以。Phase 2 会自动备份，重新运行会清空数据库重新初始化

**Q: 如何添加新 PDF？**  
A: 直接调用 StructuredDataImporter.import_jg_data()

---

## 🎯 下一步

### 集成到项目
```python
from backend.database.structured_importer import StructuredDataImporter
from backend.app.services.pdf_parser import jg_structured_data

# 在 PDF 处理完成后
jg_data = jg_structured_data(pdf_path)
importer = StructuredDataImporter()
importer.connect()
statement_id = importer.import_jg_data(pdf_name, jg_data)
importer.disconnect()
```

### 详细文档
- [完整实施指南](README_DATABASE_V2_IMPLEMENTATION.md)
- [设计规格文档](.claude/DATABASE_DESIGN_V2_DYNAMIC_SECTIONS.md)
- [快速参考指南](.claude/DATABASE_V2_QUICK_REFERENCE.md)

---

**准备好了？开始吧！** 🚀

```bash
python scripts/init_database_v2.py
```
