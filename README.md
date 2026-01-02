# Walmart PDF 解析系统

现代化的 PDF 智能识别与数据结构化系统，支持 OCR 解析、人工校验、权限管理和多格式导出。

---

## 快速开始

### 1. 后端开发环境配置

```bash
# 克隆仓库
git clone https://github.com/walmart/pdf-parser.git
cd walmart-a

# 创建虚拟环境（macOS/Linux）
python3.9 -m venv .venv
source .venv/bin/activate

# 安装依赖
pip install -r backend/requirements.txt

# 初始化数据库
python -c "from backend.database.config import init_database; init_database()"

# 启动 API 服务（开发模式）
uvicorn backend.main:app --reload --port 8000

# 访问 API 文档
# http://localhost:8000/api/v2/docs
```

### 2. 前端开发环境配置

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm start

# 访问前端应用
# http://localhost:3000
```

---

## 📚 文档

### 核心文档

| 文档 | 说明 |
|------|------|
| [API v2 设计](backend/app/api/API_DESIGN_V2.md) | 13 个核心端点、RBAC 权限、错误处理 |
| [开发路线图](/.claude/API_DEVELOPMENT_ROADMAP.md) | 5 阶段计划（A-E），详细任务分解 |
| [安全指南](/.claude/API_SECURITY_GUIDELINES.md) | JWT 认证、RBAC、敏感数据脱敏、审计日志 |
| [导入服务](/.claude/IMPORT_SERVER_DOCS.md) | PDF 导入、OCR、数据库存储 |
| [数据库设计](/.claude/DATABASE_V2_COMPLETE_SUMMARY.md) | 表结构、关系、查询优化 |

---

## 🏗️ 项目结构

```
walmart-a/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── API_DESIGN_V2.md          # API 规范
│   │   │   └── v2/                       # 新 API 实现（待开发）
│   │   ├── services/
│   │   │   ├── pdf_parser_service.py     # PDF 解析
│   │   │   ├── ocr_engine.py             # OCR 引擎
│   │   │   └── right_section_ocr.py      # 右侧识别
│   │   ├── models/                       # SQLAlchemy 模型
│   │   ├── schemas/                      # Pydantic 验证
│   │   └── crud/                         # 数据库操作
│   ├── database/
│   │   ├── config.py                     # 数据库配置
│   │   └── structured_importer.py        # 数据导入
│   ├── tests/
│   │   ├── unit/                         # 单元测试
│   │   └── integration/                  # 集成测试
│   ├── main.py                           # FastAPI 应用入口
│   └── requirements.txt
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── components/                   # React 组件
│   │   ├── pages/                        # 页面
│   │   └── App.jsx
│   └── package.json
├── scripts/                              # 工具脚本
├── .claude/                              # 项目文档与规范
│   ├── CLAUDE.md                         # AI 协作规范
│   ├── API_DEVELOPMENT_ROADMAP.md        # 开发计划
│   └── API_SECURITY_GUIDELINES.md        # 安全指南
└── README.md
```

---

## 🚀 核心功能

### 📊 PDF 解析与 OCR
- **支持引擎**：Apple Vision（macOS）、PaddleOCR（通用）
- **识别范围**：左侧标准表单 + 右侧自由版式
- **处理结果**：结构化 JSON，包含字段值 + 置信度

### ✏️ 人工校验与编辑
- **前端校验界面**：展示 OCR 结果、支持手动修改
- **乐观锁防冲突**：版本号 + If-Match 头，并发编辑安全
- **审计日志记录**：所有修改可追溯

### 🔐 权限与安全
- **角色权限控制**（RBAC）：Viewer / Editor / Admin
- **JWT 认证**：1 小时 Token 有效期（生产）
- **敏感字段脱敏**：社保号、银行账户自动掩码
- **速率限制**：防止 API 滥用（导入 10/min，导出 5/min）

### 📤 数据导出
- **多格式支持**：CSV、JSON、Excel
- **后台异步处理**：大文件非阻塞导出
- **预签名 URL**：1 小时有效期，安全下载

### 📈 数据分析
- **汇总统计**：总数据量、平均值、字段频率
- **时间范围过滤**：支持自定义查询周期
- **缓存优化**：结果缓存 10 分钟

---

## 🛠️ API 端点快览

### 基础端点

```http
# 健康检查
GET /api/v2/health

# 查看所有 Statements
GET /api/v2/statements?page=1&size=20

# 查看单个 Statement 详情
GET /api/v2/statements/{id}
```

### 导入端点

```http
# 同步导入单个 PDF
POST /api/v2/import
{"pdf_path": "PdfData/file.pdf"}

# 批量导入（异步）
POST /api/v2/import/batch
{"pdf_paths": ["A.pdf", "B.pdf"]}

# 查询异步任务状态
GET /api/v2/tasks/{task_id}
```

### 编辑端点

```http
# 编辑板块数据（支持乐观锁）
PATCH /api/v2/statements/{id}/sections/left_section
If-Match: "v5"
{"fields": {"payment_date": "2026-01-15"}}

# 验证板块数据
POST /api/v2/statements/{id}/sections/left_section/validate

# 批准 Statement
POST /api/v2/statements/{id}/approve
```

### 分析导出端点

```http
# 数据汇总分析
GET /api/v2/analytics/summary?start_date=2026-01-01

# 导出为 CSV/JSON/Excel
POST /api/v2/statements/{id}/export
{"format": "csv"}

# 查看审计日志
GET /api/v2/statements/{id}/change_log
```

**完整 API 文档**：见 [API_DESIGN_V2.md](backend/app/api/API_DESIGN_V2.md)

---

## 🧪 测试

### 运行测试

```bash
# 运行所有测试
pytest backend/tests -q

# 运行单个测试文件
pytest backend/tests/unit/test_pdf_parser.py -q

# 运行集成测试
pytest backend/tests/integration/test_full_pipeline.py -q

# 查看覆盖率
pytest --cov=backend backend/tests
```

### 测试数据

测试用例 PDF 文件位于 `backend/tests/test_data/`，包括：
- 标准财务报表
- 手写表单
- 复杂版式文档

---

## 📋 数据库

### 初始化

```bash
# SQLite（默认，开发用）
python -c "from backend.database.config import init_database; init_database()"

# PostgreSQL（生产）
export DB_TYPE=postgresql
export DB_URL=postgresql://user:pass@host:5432/walmart
python -c "from backend.database.config import init_database; init_database()"
```

### 核心表

| 表 | 说明 |
|-----|------|
| `statements` | 导入的 PDF 文档记录 |
| `section_data` | 各板块解析结果（left_section, right_section） |
| `change_log` | 所有编辑操作的审计日志 |
| `tasks` | 异步任务（导入、导出）状态 |
| `exports` | 导出文件记录与下载链接 |
| `field_frequency` | 字段出现频率统计 |

---

## 🔧 常见问题

### Q: 如何切换 OCR 引擎？

```python
from backend.app.services.ocr_engine import OCREngine

# 使用 Apple Vision（macOS）
ocr = OCREngine(engine_type="vision")

# 使用 PaddleOCR（通用，需下载模型）
ocr = OCREngine(engine_type="paddle")
```

### Q: 如何在开发环境禁用 JWT 认证？

编辑 `backend/main.py`：
```python
JWT_ENABLED = False  # 开发模式，禁用认证
```

### Q: 如何导出超大数据量？

使用批量导出 API（后台异步处理）：
```http
POST /api/v2/statements/export
{"format": "csv", "ids": [1, 2, ..., 1000]}
```

---

## 📅 开发路线图

**详见** [API 开发路线图](/.claude/API_DEVELOPMENT_ROADMAP.md)

- **阶段 A**（周 1）：核心 API 端点（导入、列表、详情）
- **阶段 B**（周 2-3）：编辑、权限、审计
- **阶段 C**（周 4）：分析、导出、批量任务
- **阶段 D**（2 月）：性能优化、安全加固
- **阶段 E**（3 月）：测试、文档、上线

---

## 🔒 安全

**重要**：生产环境必须启用以下安全措施：

- ✅ JWT 强制认证（见 [安全指南](/.claude/API_SECURITY_GUIDELINES.md)）
- ✅ HTTPS 传输
- ✅ RBAC 权限检查
- ✅ 敏感字段脱敏
- ✅ 审计日志记录
- ✅ 速率限制
- ✅ 依赖包漏洞扫描

详细检查清单见 [API_SECURITY_GUIDELINES.md](/.claude/API_SECURITY_GUIDELINES.md#8-清单)

---

## 💡 开发指南

### 代码风格

- 后端遵循 PEP 8
- 前端遵循 React Best Practices
- 所有函数必须有文档字符串（docstring）
- 使用类型提示（Type Hints）

### 文件头注释规范

```python
"""
模块说明

功能描述...
"""
# 导入、实现...
```

### 提交 PR 要求

1. 代码修改范围精简
2. 所有功能变更必须附带测试用例
3. 更新相关文档（README 或 .claude/ 下的文档）
4. 通过 CI/CD 自动测试
5. 至少一人代码审查

---

## 📞 支持

- **问题提交**：GitHub Issues
- **功能建议**：Discussions
- **安全问题**：请邮件至 security@walmart.com（勿在 Issue 中公开）

---

## 📄 许可证

MIT License - 详见 LICENSE 文件

---

## 更新日志

### 2026-01-02
- ✅ API v2 设计规范完成（13 端点，RBAC）
- ✅ 5 阶段开发路线图确定
- ✅ 安全指南与最佳实践文档完成
- ⏳ 开始实现阶段 A（基础 API）

### 2025-12-25
- ✅ 后端核心模块完成（PDFParserService, RightSectionOCR, StructuredDataImporter）
- ✅ 数据库 v2 迁移完成
- ✅ 批量导入与右侧识别功能验证通过

---

**最后更新**：2026-01-02  
**维护者**：Walmart PDF 解析团队
