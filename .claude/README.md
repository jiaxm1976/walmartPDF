# Walmart PDF Parser - 项目文档中心 📚

> **最后更新**: 2026-01-01  
> **文档版本**: V2.0  
> **项目状态**: ✅ 生产就绪

---

## 🚀 快速导航

### 新手入门
- [🎯 项目协作规范](CLAUDE.md) - AI 助手和开发者协作指南
- [⚡ 快速开始指南](QUICKSTART_DATABASE_V2.md) - 5 分钟上手数据库 V2
- [📋 安装说明](../README_安装说明.txt) - 环境配置与依赖安装

### 核心文档
- [📊 项目完成报告](PROJECT_COMPLETION_REPORT.md) - V2 实施总结与成果
- [🗂️ 数据库索引](DATABASE_INDEX.md) - 数据库快速查询入口
- [📝 任务跟踪](TaskList.md) - 项目任务与进度管理

---

## 🏗️ 架构与设计

### 数据库 V2 设计
- [📖 V2 完整设计文档](DATABASE_V2_COMPLETE_SUMMARY.md)
  - 2 表动态设计（statements + section_data）
  - 字段频率自动分类
  - 低频字段 JSON 合并策略
  - 查询模式与最佳实践

---

## 🔍 测试与技术文档

### 完整测试流程 (从 PDF 到数据库)
1. [🎨 整体测试架构](testing_flow_diagram.md)
   - Phase 2-5 完整流程
   - 数据库表结构详解
   - 测试完整性检查清单

2. [🔗 详细调用链](detailed_call_chain.md)
   - 从 PDF 文件读取到数据库的完整流程
   - 单个 PDF 处理详解
   - WFS 板块 OCR 错误修复逻辑

3. [🌳 函数调用树](function_call_tree.md)
   - 14 个核心函数详解
   - 数据流向追踪
   - 执行时间分析

**验证结果**: 
- ✅ 6/6 PDF 成功导入
- ✅ 38 个板块数据完整
- ✅ 0 错误，100% 数据有效性

---

## 📂 目录结构

```
.claude/
├── README.md (本文件)            ← 主索引
│
├── 📘 基础文档
│   ├── CLAUDE.md                  ← 项目协作规范
│   ├── TaskList.md                ← 任务跟踪
│   └── QUICKSTART_DATABASE_V2.md  ← 快速开始
│
├── 📊 核心设计
│   ├── PROJECT_COMPLETION_REPORT.md     ← 项目完成报告
│   ├── DATABASE_V2_COMPLETE_SUMMARY.md  ← V2 完整设计
│   └── DATABASE_INDEX.md                ← 数据库索引
│
├── 🧪 测试文档
│   ├── testing_flow_diagram.md    ← 整体架构
│   ├── detailed_call_chain.md     ← 调用链
│   └── function_call_tree.md      ← 函数树
│
├── 📁 子目录
│   ├── context/                   ← 上下文文档
│   ├── specs/                     ← 规范文档
│   ├── templates/                 ← 模板文件
│   └── archive/                   ← 归档文档
│
└── ⚙️ 配置
    └── settings.local.json        ← 本地设置
```

---

## 🎯 核心功能速查

### 数据库操作
```python
# 初始化数据库
python scripts/init_database_v2.py

# 批量导入 PDF
python scripts/batch_import_v2.py

# 验证查询
python scripts/verify_queries_v2.py
```

### 测试执行
```bash
# 单元测试
pytest backend/tests/unit/ -q

# 集成测试
pytest backend/tests/integration/ -q

# 完整 Pipeline 测试
python scripts/test_full_pipeline_complete.py
```

### 数据查询示例
```sql
-- 查询单个 PDF 的所有板块
SELECT * FROM statements_complete 
WHERE pdf_name = 'MP_01142025_statement_summary.pdf';

-- 按板块类型聚合
SELECT section_name, COUNT(*) as count
FROM section_data
GROUP BY section_name;
```

---

## 🔧 技术栈

| 组件 | 技术 | 版本 |
|------|------|------|
| 后端框架 | FastAPI | Latest |
| 数据库 | SQLite | 3.x |
| OCR 引擎 | Vision OCR / PaddleOCR | - |
| Python | 3.11+ | 3.11.14 |
| 前端 | React (CRA) | Latest |

---

## 📊 项目统计

### 数据库 V2 成果
- ✅ **表数量**: 4 (statements, section_data, field_frequency, db_config)
- ✅ **视图数量**: 2 (statements_complete, sales_refund_summary)
- ✅ **已导入 PDF**: 6 个
- ✅ **板块记录**: 38 条
- ✅ **板块类型**: 8 种（header, 销售, 退款, 调整, 其他活动, WFS商品, WFS配送, footer）
- ✅ **字段频率**: 39 个预定义字段

### 代码统计
- **核心服务**: 10+ 个服务模块
- **测试用例**: 20+ 个单元/集成测试
- **脚本工具**: 15+ 个实用脚本
- **文档数量**: 9 个核心文档

---

## 🐛 常见问题

### Q: WFS 板块识别失败？
**A**: 已修复 OCR 识别错误（WVFS → WFS）。参见 [详细调用链](detailed_call_chain.md#wfs-板块识别修复逻辑)

### Q: 如何查看某个 PDF 的所有数据？
**A**: 使用 `statements_complete` 视图：
```sql
SELECT * FROM statements_complete 
WHERE pdf_name = 'your_file.pdf';
```

### Q: 低频字段如何处理？
**A**: 频率 < 阈值的字段自动合并到 JSON 的 `其他` 字段。详见 [V2 设计文档](DATABASE_V2_COMPLETE_SUMMARY.md)

---

## 📞 联系方式

- **项目位置**: `/Users/jiaxinming/JxmWork/walmart-a`
- **数据库位置**: `backend/data/walmart_pdf_parser.db`
- **文档位置**: `.claude/` 目录

---

## 📝 文档贡献

更新文档时请遵循：
1. 保持中文为主要语言
2. 使用 Markdown 格式
3. 添加清晰的章节标题和跳转链接
4. 包含代码示例和执行结果
5. 更新本 README 的"最后更新"日期

---

## 🗂️ 归档文档

旧版本和历史文档已移至 [archive/](archive/) 目录：
- 旧版 V2 设计文档 (8 个)
- 调试分析报告 (7 个)
- 早期实施指南

如需查阅历史文档，请访问归档目录。

---

<div align="center">

**🎉 感谢使用 Walmart PDF Parser 项目文档！**

</div>
