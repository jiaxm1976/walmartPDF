# Archived Content Index / 归档内容索引

**生成日期**: 2026-01-02  
**目的**: 管理仓库中已过时、已迁移或临时生成的文件

---

## 📁 目录结构

```
archived/
├── backend/
│   ├── database/
│   │   └── schema_design_v1.sql          # ❌ 旧 v1 schema（不再使用）
│   ├── tests/                            # 📦 已迁移的测试目录
│   │   ├── unit/
│   │   ├── integration/
│   │   ├── output/                       # 测试输出日志
│   │   └── test_data/                    # 测试用 PDF 样本
│   ├── __pycache__/                      # Python 缓存
│   └── ...
├── scripts/
│   ├── db_import_new_structure.py        # ❌ 旧导入脚本
│   ├── test-output/                      # 脚本执行的临时输出
│   ├── __pycache__/                      # Python 缓存
│   └── test/                             # 旧测试脚本输出
├── test_outputs/                         # 测试运行产物
├── pycache/                              # Python 编译缓存
├── backup_20251216/                      # 历史备份
├── .pytest_cache/                        # pytest 缓存
├── 备份测试/                             # 旧测试备份
└── ...
```

---

## 🗂️ 内容分类说明

### ❌ 不再使用的文件（可安全删除）

| 文件 | 原因 | 备注 |
|------|------|------|
| `schema_design_v1.sql` | 仓库已迁移到 V2 动态 schema | 如需参考旧设计，见 `.claude/archive/` 文档 |
| `db_import_new_structure.py` | 旧导入脚本，已由 `batch_import_v2.py` 替代 | V2 版本在项目根 `scripts/` 目录 |

### 📦 已迁移的代码

| 目录 | 内容 | 说明 |
|------|------|------|
| `backend/tests/` | 单元&集成测试 | 原始放在根目录，已归档；新测试在 `backend/tests/` |
| `scripts/test-output/` | 脚本执行结果 | PDF 识别的中间产物（图像、JSON）和日志 |

### 🗑️ 临时/缓存文件

| 目录 | 类型 | 清理策略 |
|------|------|---------|
| `__pycache__/` | Python 编译缓存 | 可安全删除，运行时会重新生成 |
| `.pytest_cache/` | pytest 缓存 | 可安全删除 |
| `test_outputs/` | 测试日志 | 可按需删除（参考已有日志后） |
| `backup_20251216/` | 数据库备份 | 根据需求保留或删除 |

---

## 🔄 恢复与访问指南

### 如何访问已归档的旧设计文档

```bash
# 旧 v1 schema 定义（用于参考，不应在生产环境中使用）
cat archived/backend/database/schema_design_v1.sql

# 旧导入脚本（已弃用）
cat archived/scripts/db_import_new_structure.py
```

### 如何恢复备份数据库

```bash
# 查看可用备份
ls -lh backend/data/backups/

# 恢复特定备份
cp backend/data/backups/walmart_pdf_parser_20260101_120000.db \
   backend/data/walmart_pdf_parser.db
```

### 如何检查测试输出

```bash
# 查看最近一次批量导入的日志
tail -100 archived/backend/tests/output/batch_test.log

# 查看特定 PDF 的识别结果（如可用）
ls archived/scripts/test-output/ | grep "MP_01142025"
```

---

## 📊 归档内容统计

```
总共归档项目：
- Python 源文件：3 个（旧脚本 & 备份）
- Python 缓存目录：15 个
- 测试输出目录：20+ 个
- 测试数据文件：6 个 PDF 样本
- 日志文件：50+ 个
- 中间产物（图像、JSON）：200+ 个
```

---

## ✅ 清理建议

### 立即可删除

```bash
# 1. 清理 Python 缓存（安全）
rm -rf archived/__pycache__ archived/*/__pycache__

# 2. 清理 pytest 缓存（安全）
rm -rf archived/.pytest_cache archived/**/.pytest_cache

# 3. 清理旧脚本输出（若无需保留）
rm -rf archived/scripts/test-output
```

### 需确认后删除

```bash
# 1. 旧导入脚本（建议先确认无其他地方引用）
rm archived/scripts/db_import_new_structure.py

# 2. v1 schema（如确实不需要参考）
rm archived/backend/database/schema_design_v1.sql

# 3. 测试备份（若已有新的单元测试）
rm -rf archived/backend/tests/
```

---

## 🛡️ 归档策略

**当前策略**（2026-01-02）：
1. 所有过期代码移入 `archived/`（保留，便于参考和恢复）
2. 所有缓存文件保留在 `archived/`（不影响工作区）
3. `.gitignore` 已更新以排除 `archived/` 目录

**未来策略**：
- 每月清理一次 `archived/` 中的缓存与临时文件
- 将 `archived/` 中的重要文件迁移到 `.claude/archive/`（更新保存）
- 对于旧脚本，在注释中添加弃用时间，6 个月后可删除

---

## 📝 变更记录

- **2026-01-02**: 初始归档索引，扫描并整理了仓库中的所有临时文件与过期代码。

---

## 📞 问题排查

**Q: 我需要旧的 v1 schema 来理解数据库升级过程**  
A: 检查 `archived/backend/database/schema_design_v1.sql` 或 `.claude/archive/` 中的设计文档。

**Q: 某个测试的中间输出在哪里？**  
A: 检查 `archived/scripts/test-output/` 或 `archived/backend/tests/output/` 目录。

**Q: 可以安全地删除 `archived/` 中的所有文件吗？**  
A: 可以删除缓存（`__pycache__`, `.pytest_cache`）和临时输出文件。但建议保留：
- `backend/database/schema_design_v1.sql`（用于参考）
- 数据库备份（`backup_*`）
- 过期脚本（标注好弃用原因）

---

**最后更新**: 2026-01-02  
**维护者**: AI 代码管理助手
