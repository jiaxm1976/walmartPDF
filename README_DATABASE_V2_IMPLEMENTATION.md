# Walmart PDF 数据库设计 V2 - 项目实施指南

**版本**: 2.0 (动态板块设计)  
**状态**: ✅ 设计完成，脚本就绪  
**完成时间**: 2026-01-01  

---

## 📖 快速导航

| 文档 | 用途 | 阶段 |
|------|------|------|
| [DATABASE_DESIGN_V2_DYNAMIC_SECTIONS.md](.claude/DATABASE_DESIGN_V2_DYNAMIC_SECTIONS.md) | 详细技术设计 | 📖 参考 |
| [DATABASE_V2_COMPLETE_SUMMARY.md](.claude/DATABASE_V2_COMPLETE_SUMMARY.md) | 完整总结 + FAQ | 📖 参考 |
| [DATABASE_V2_QUICK_REFERENCE.md](.claude/DATABASE_V2_QUICK_REFERENCE.md) | 快速参考指南 | 📖 参考 |
| [DESIGN_V2_OVERVIEW.txt](.claude/DESIGN_V2_OVERVIEW.txt) | 可视化架构 | 📖 参考 |
| [IMPLEMENTATION_NEXT_STEPS.md](.claude/IMPLEMENTATION_NEXT_STEPS.md) | 实施步骤详解 | 📖 参考 |
| **本文档** | 项目总览与执行指南 | 🚀 现在开始 |

---

## 🎯 项目目标

### 核心需求
1. **一个 PDF = 一条 statement 记录** ✅
2. **板块动态化**（无需硬编码新板块）✅
3. **低频字段自动合并**（频率 < 2 → JSON）✅
4. **支持 SQL 查询**（可聚合、可统计）✅
5. **最小化复杂性**（仅 2 个主表）✅

### 设计成果
- ✅ V2 数据库设计规范（600+ 行）
- ✅ SQL 初始化脚本（200+ 行，包含字段频率表）
- ✅ Python 导入模块（336 行，自动化低频字段合并）
- ✅ 4 个配套脚本（初始化、导入、验证）
- ✅ 5 份详细文档（设计、总结、参考、概览、步骤）

---

## 🚀 执行 5 阶段计划

### Phase 1: ✅ 设计与代码生成 (已完成)

**完成内容**:
- ✓ 需求分析与澄清
- ✓ V2 设计定义
- ✓ SQL 脚本编写
- ✓ Python 模块实现
- ✓ 文档编写

**关键决定**:
- **2 表设计**: statements + section_data（vs V1 的 7 表）
- **动态板块**: section_name VARCHAR(50)（支持无限扩展）
- **频率阈值**: 2（频率 < 2 的字段合并到 JSON）
- **JSON 存储**: 低频字段使用 {section_name}_其他 格式

---

### Phase 2: ⏳ 数据库初始化

**目标**: 清空数据库，初始化 V2 schema

**执行命令**:
```bash
python scripts/init_database_v2.py
```

**脚本功能**:
1. 备份现有数据库（可选恢复）
2. 删除旧 walmart_pdf_parser.db
3. 执行 SQL 初始化脚本
4. 验证表结构（4 表 + 2 视图）
5. 验证字段频率表已预加载（31 行）

**预期输出**:
```
✓ 已备份数据库至: backend/data/backups/walmart_pdf_parser_20260101_120000.db
✓ 已删除旧数据库: backend/data/walmart_pdf_parser.db
✓ schema 初始化完成: backend/data/walmart_pdf_parser.db
✓ 已创建 4 个表
✓ 已创建 2 个视图
✓ field_frequency 表有 31 条记录
```

**验证命令**:
```bash
# 验证表结构
sqlite3 backend/data/walmart_pdf_parser.db ".schema"

# 验证字段频率表
sqlite3 backend/data/walmart_pdf_parser.db "SELECT COUNT(*) FROM field_frequency;"
# 预期输出: 31
```

**时间**: ~1 分钟

---

### Phase 3: ⏳ 单 PDF 导入测试

**目标**: 验证导入逻辑正确性

**执行命令**:
```bash
# 方式 1: 自动选择第一个 PDF
python scripts/test_single_pdf_import.py

# 方式 2: 指定 PDF 文件
python scripts/test_single_pdf_import.py backend/tests/test_data/MP_01142025.pdf
```

**脚本功能**:
1. 选择测试 PDF
2. 执行 jg_structured_data() 解析
3. 使用 StructuredDataImporter 导入
4. 验证导入结果

**验证内容**:
- ✓ 1 条 statements 记录创建
- ✓ N 条 section_data 记录创建（N = 板块数）
- ✓ 低频字段自动合并到 JSON

**预期输出**:
```
✓ 正在解析 PDF: MP_01142025.pdf
✓ 解析完成，包含 8 个板块: header, 销售, 退款, 调整, 其他活动, WFS商品, WFS配送, footer
✓ 已连接数据库: backend/data/walmart_pdf_parser.db
✓ 正在导入 MP_01142025.pdf...
✓ 导入成功，statement_id = 1
✓ statements 表: 1 条记录
✓ section_data 表: 8 条记录
✓ 低频字段合并: 销售._其他
```

**验证查询**（手动）:
```sql
-- 查看导入的 PDF
SELECT * FROM statements WHERE pdf_name = 'MP_01142025.pdf';

-- 查看所有板块
SELECT section_name FROM section_data WHERE statement_id = 1;

-- 查看低频字段（示例）
SELECT json_extract(data, '$.销售_其他') FROM section_data WHERE section_name = '销售' AND statement_id = 1;
```

**时间**: ~30 秒 - 2 分钟（取决于 PDF 大小和 OCR 引擎）

---

### Phase 4: ⏳ 批量导入所有 PDF

**目标**: 导入所有测试 PDF，生成统计报告

**执行命令**:
```bash
python scripts/batch_import_all_pdfs.py
```

**脚本功能**:
1. 遍历所有测试 PDF（backend/tests/test_data/*.pdf）
2. 逐个执行 jg_structured_data() 解析
3. 批量导入到数据库
4. 生成统计报告
5. 输出数据完整性验证

**预期输出**:
```
[2026-01-01 12:00:00] ✓ 找到 6 个 PDF 文件
[2026-01-01 12:00:00] ✓ 已连接数据库

[2026-01-01 12:00:01] → [1/6] MP_01142025.pdf
[2026-01-01 12:00:01] ✓ 导入成功 (statement_id=1, 板块=8)

[2026-01-01 12:00:02] → [2/6] MP_02142025.pdf
[2026-01-01 12:00:02] ✓ 导入成功 (statement_id=2, 板块=8)

... (其他 PDF) ...

✓ 已导入 6 个 PDF
✓ 已创建 48 个板块记录（6 PDF × 8 板块）
✓ 成功率: 100%

✓ statements 表: 6 条记录
✓ section_data 表: 48 条记录
✓ 低频字段合并: 24 个
```

**验证查询**（手动）:
```sql
-- 统计 PDF 数量
SELECT COUNT(*) FROM statements;
-- 预期: 6

-- 统计板块数
SELECT COUNT(*) FROM section_data;
-- 预期: ~48

-- 板块分布
SELECT section_name, COUNT(*) FROM section_data GROUP BY section_name;
-- 预期: 每个板块 6 条记录
```

**时间**: 2-5 分钟（取决于 PDF 大小和 OCR 引擎）

---

### Phase 5: ⏳ 查询验证

**目标**: 验证常见查询模式正确

**执行命令**:
```bash
python scripts/verify_queries.py
```

**脚本验证 4 种查询**:

1. **查询 1**: 获取单 PDF 的完整数据
   ```sql
   SELECT * FROM statements WHERE pdf_name = 'MP_01142025.pdf';
   SELECT * FROM section_data WHERE statement_id = 1;
   ```

2. **查询 2**: 按板块统计记录
   ```sql
   SELECT section_name, COUNT(*) as record_count
   FROM section_data
   GROUP BY section_name;
   ```

3. **查询 3**: 提取关键字段（产品价格）
   ```sql
   SELECT s.pdf_name, sd.section_name, 
          json_extract(sd.data, '$.产品价格') as 产品价格
   FROM statements s
   LEFT JOIN section_data sd ON s.id = sd.statement_id
   WHERE sd.section_name IN ('销售', '退款');
   ```

4. **查询 4**: 检查低频字段合并
   ```sql
   SELECT section_name,
          COUNT(*) as 总数,
          SUM(CASE WHEN json_extract(data, '$.' || section_name || '_其他') IS NOT NULL 
                  THEN 1 ELSE 0 END) as 有低频字段
   FROM section_data
   GROUP BY section_name;
   ```

**预期输出**:
```
✓ 查询 1 完成 - 单 PDF 数据获取成功
✓ 查询 2 完成 - 板块统计完成
✓ 查询 3 完成 - 字段提取成功
✓ 查询 4 完成 - 低频字段合并验证成功
✓ 数据完整性检查通过
```

**时间**: ~10 秒

---

## 📊 全流程时间估计

| 阶段 | 任务 | 时间 |
|------|------|------|
| Phase 1 | ✅ 设计与代码生成 | 已完成 |
| Phase 2 | 数据库初始化 | ~1 分钟 |
| Phase 3 | 单 PDF 导入测试 | ~2 分钟 |
| Phase 4 | 批量导入所有 PDF | ~5 分钟 |
| Phase 5 | 查询验证 | ~1 分钟 |
| **总计** | **完整实施** | **~9 分钟** |

---

## 📂 核心文件清单

### 设计文档（参考资料）
| 文件 | 行数 | 用途 |
|------|------|------|
| DATABASE_DESIGN_V2_DYNAMIC_SECTIONS.md | 600+ | 详细技术规格 |
| DATABASE_V2_COMPLETE_SUMMARY.md | 339+ | 完整总结与 FAQ |
| DATABASE_V2_QUICK_REFERENCE.md | 300+ | 快速参考 |
| DESIGN_V2_OVERVIEW.txt | 200+ | 可视化架构 |
| IMPLEMENTATION_NEXT_STEPS.md | 400+ | 实施步骤详解 |

### 实现代码
| 文件 | 行数 | 用途 | 状态 |
|------|------|------|------|
| backend/database/schema_v2_dynamic.sql | 200+ | SQL 初始化脚本 | ✅ 就绪 |
| backend/database/structured_importer.py | 336 | Python 导入模块 | ✅ 就绪 |

### 执行脚本
| 脚本 | 行数 | 功能 | 阶段 |
|------|------|------|------|
| scripts/init_database_v2.py | 150+ | 数据库初始化 | Phase 2 |
| scripts/test_single_pdf_import.py | 180+ | 单 PDF 导入测试 | Phase 3 |
| scripts/batch_import_all_pdfs.py | 250+ | 批量导入 | Phase 4 |
| scripts/verify_queries.py | 300+ | 查询验证 | Phase 5 |

---

## 🔑 关键技术点

### 1. 动态板块支持
```sql
-- section_name 无需硬编码
-- 可自动添加新板块，无需修改 schema
CREATE TABLE section_data (
    ...,
    section_name VARCHAR(50) NOT NULL,  -- 灵活，支持无限扩展
    ...
);
```

### 2. 低频字段自动合并
```json
// 频率 ≥ 2 的字段 → 顶级保存
{
  "产品价格": 2000,
  "运输": 50
}

// 频率 < 2 的字段 → JSON 合并
{
  "销售_其他": {
    "其他税款(费用)": 10,
    "其他字段": "值"
  }
}
```

### 3. 查询优化
```sql
-- 使用 JSON 函数直接查询
SELECT json_extract(data, '$.产品价格') 
FROM section_data 
WHERE section_name = '销售';

-- 聚合查询
SELECT SUM(CAST(json_extract(data, '$.产品价格') AS DECIMAL(12,2)))
FROM section_data
WHERE section_name = '销售';
```

---

## ⚠️ 注意事项

### 备份策略
- ✅ Phase 2 会自动备份现有数据库到 `backend/data/backups/`
- 保留备份直到验证完全通过

### 数据验证
- ✓ 每个阶段都包含验证步骤
- ✓ 字段频率表会在 Phase 2 自动预加载
- ✓ 数据完整性在 Phase 4 和 Phase 5 验证

### 性能考虑
- SQLite JSON 操作对于 Walmart 数据量（几百个 PDF）完全足够
- 如未来数据大幅增长（>10K PDF），可考虑迁移到 PostgreSQL

### 可回退性
- ✅ 所有操作可逆（保留备份文件）
- ⏪ 可通过恢复备份回到任何历史版本

---

## 🎯 下一步行动

### 现在就开始：

```bash
# Step 1: Phase 2 - 数据库初始化
python scripts/init_database_v2.py

# Step 2: Phase 3 - 单 PDF 导入测试
python scripts/test_single_pdf_import.py

# Step 3: Phase 4 - 批量导入所有 PDF
python scripts/batch_import_all_pdfs.py

# Step 4: Phase 5 - 查询验证
python scripts/verify_queries.py
```

### 或逐步执行：
```bash
# 仅执行 Phase 2
python scripts/init_database_v2.py

# [验证后] 执行 Phase 3
python scripts/test_single_pdf_import.py

# [验证后] 执行 Phase 4
python scripts/batch_import_all_pdfs.py

# [验证后] 执行 Phase 5
python scripts/verify_queries.py
```

---

## 💡 高级操作

### 集成到 PDF 处理流程

在现有 PDF 处理代码中添加：

```python
from backend.database.structured_importer import StructuredDataImporter
from backend.app.services.pdf_parser import jg_structured_data

# 在 PDF 处理完成后
pdf_path = 'path/to/pdf.pdf'
jg_data = jg_structured_data(pdf_path)

# 导入到数据库
importer = StructuredDataImporter()
importer.connect()
statement_id = importer.import_jg_data(pdf_path.name, jg_data)
importer.disconnect()

print(f"PDF 已导入，statement_id = {statement_id}")
```

### 自定义查询

查看 [DATABASE_DESIGN_V2_DYNAMIC_SECTIONS.md](.claude/DATABASE_DESIGN_V2_DYNAMIC_SECTIONS.md) 中的**查询模式**章节，获取更多查询示例。

### 扩展支持

- **新板块**: 直接在 jg_structured_data() 中添加新的 section，无需修改数据库
- **新字段**: 
  - 频率 ≥ 2：字段自动保存为 JSON 顶级字段
  - 频率 < 2：自动合并到 {section_name}_其他

---

## 📞 故障排除

### 问题：导入失败

**可能原因**:
1. PDF 路径错误
2. jg_structured_data() 返回格式异常
3. 数据库连接失败

**解决**:
```bash
# 检查 PDF 文件
ls -la backend/tests/test_data/*.pdf

# 检查数据库
sqlite3 backend/data/walmart_pdf_parser.db ".tables"

# 查看详细日志（修改 logging level）
# 在 structured_importer.py 中调整 logging 设置
```

### 问题：查询返回空结果

**可能原因**:
1. 导入未完成
2. 数据库为空

**解决**:
```bash
# 检查 statements 表
sqlite3 backend/data/walmart_pdf_parser.db "SELECT COUNT(*) FROM statements;"

# 检查 section_data 表
sqlite3 backend/data/walmart_pdf_parser.db "SELECT COUNT(*) FROM section_data;"
```

### 问题：低频字段未合并

**可能原因**:
1. field_frequency 表未正确初始化
2. 字段频率阈值设置不当

**解决**:
```bash
# 检查字段频率表
sqlite3 backend/data/walmart_pdf_parser.db "SELECT * FROM field_frequency LIMIT 5;"

# 验证字段频率数据
# 应该有 31 行数据，频率值应为 17-100 之间
```

---

## ✅ 最终检查清单

在启动 Phase 2 前，确保：

- [ ] 已阅读本文档全部内容
- [ ] 了解 5 阶段计划
- [ ] 备份了关键数据（如需要）
- [ ] 有权限访问 backend/data/ 目录
- [ ] Python 环境已配置

在启动 Phase 3 前，确保：

- [ ] Phase 2 已成功完成
- [ ] 数据库中有 4 个表和 2 个视图
- [ ] field_frequency 表有 31 行数据

在启动 Phase 4 前，确保：

- [ ] Phase 3 已成功完成
- [ ] 单 PDF 导入结果正确
- [ ] statements 和 section_data 记录已创建

在启动 Phase 5 前，确保：

- [ ] Phase 4 已成功完成
- [ ] 所有 6 个 PDF 已导入
- [ ] 数据库中有 ~48 条 section_data 记录

---

## 📝 版本记录

| 版本 | 日期 | 说明 |
|------|------|------|
| V1.0 | 2026-01 | 初始版本（已废弃） |
| V2.0 | 2026-01 | 动态板块设计（当前） |

---

## 🎓 进一步学习

- [SQLite JSON 函数文档](https://www.sqlite.org/json1.html)
- [Python sqlite3 模块](https://docs.python.org/3/library/sqlite3.html)
- [SQL 最佳实践](https://use-the-index-luke.com/)

---

**准备好开始了吗？** 🚀

执行：`python scripts/init_database_v2.py`
