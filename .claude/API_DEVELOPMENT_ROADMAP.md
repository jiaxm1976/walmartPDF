# API v2 开发路线图

**计划周期**：5 周（2026-01-06 ~ 2026-02-06）| **目标**：完整、安全、生产级 API

## 📅 阶段概览

| 阶段 | 时间 | 目标 | 端点数 | 优先级 |
|------|------|------|--------|--------|
| **A** | 周 1 | 核心导入、列表、详情 | 5 | 🔴 P0 |
| **B** | 周 2-3 | 编辑、权限、审计 | 4 | 🔴 P0 |
| **C** | 周 4 | 分析、导出、批量 | 3 | 🟡 P1 |
| **D** | 2 月 | 性能、安全、监控 | - | 🟡 P1 |
| **E** | 3 月 | 测试、文档、上线 | - | 🟡 P2 |

---

## 阶段 A：基础 API（周 1）

**目标**：实现 5 个核心端点，支持同步导入单个 PDF

### 任务分解

#### 🔧 Task A1: 项目结构初始化
- [ ] 创建 `backend/app/api/v2/` 目录结构
  - `__init__.py`
  - `schemas.py` — Pydantic 模型
  - `routes.py` — 路由定义
  - `dependencies.py` — 认证、日志
- [ ] 创建 `tests/integration/test_api_v2.py`

**验证标准**：
- 目录结构完成
- 导入无错误

---

#### 🔐 Task A2: 认证与 JWT 集成
- [ ] 实现 JWT Token 生成与验证
- [ ] 创建 `get_current_user()` 依赖
- [ ] 支持测试 token（开发模式）
- [ ] 实现 Bearer Token 验证装饰器

**验证标准**：
```bash
# 有效 token
curl -H "Authorization: Bearer test-token" http://localhost:8000/api/v2/health

# 无效 token → 401
curl http://localhost:8000/api/v2/health
```

---

#### 📍 Task A3: 健康检查端点
- [ ] 实现 `GET /api/v2/health`
- [ ] 检查数据库连接、队列状态
- [ ] 返回组件状态

**响应示例**：
```json
{
  "status": "ok",
  "components": {
    "app": "ok",
    "database": "ok",
    "queue": "connecting"
  }
}
```

---

#### 📤 Task A4: 导入端点（同步）
- [ ] 实现 `POST /api/v2/import`
- [ ] 接收 pdf_path，调用 PDFParserService
- [ ] 存储到数据库（statements + section_data）
- [ ] 返回 statement_id 与处理摘要

**请求**：
```json
{"pdf_path": "PdfData/file.pdf", "client_request_id": "cli-001"}
```

**响应**：
```json
{
  "status": "success",
  "statement_id": 123,
  "processed_sections": ["left_section", "right_section"],
  "created_at": "2026-01-06T10:30:00Z"
}
```

---

#### 📋 Task A5: Statements 列表端点
- [ ] 实现 `GET /api/v2/statements`
- [ ] 支持分页（page, size）、排序（sort）
- [ ] 返回摘要（id, created_at, status）
- [ ] 验证权限（Viewer+ 可读）

**请求**：
```http
GET /api/v2/statements?page=1&size=20&sort=created_at:desc
```

**响应**：
```json
{
  "items": [
    {"id": 1, "created_at": "...", "status": "draft", "sections_count": 2}
  ],
  "total": 100,
  "page": 1
}
```

---

#### 📊 Task A6: Statement 详情端点
- [ ] 实现 `GET /api/v2/statements/{id}`
- [ ] 返回完整数据（所有板块、字段）
- [ ] 包含 version 字段（用于乐观锁）
- [ ] 权限验证

**验证标准**：
- ✅ 返回 left_section、right_section 数据
- ✅ 包含 version 字段
- ✅ Viewer 可访问自己上传的数据

---

### 阶段 A 验证标准

| 检查项 | 标准 |
|--------|------|
| 功能测试 | 5 个端点全部可用 |
| 单元测试 | ≥ 95% 行覆盖 |
| 集成测试 | 完整导入→列表→详情流程可重现 |
| API 文档 | Swagger 自动生成可用 |
| 性能 | 导入 < 5s，列表查询 < 1s |

---

## 阶段 B：编辑、权限、审计（周 2-3）

**目标**：支持前端编辑、权限控制、审计日志

### 任务分解

#### ✏️ Task B1: 编辑端点（PATCH）
- [ ] 实现 `PATCH /api/v2/statements/{id}/sections/{section_name}`
- [ ] 乐观锁（If-Match header）
- [ ] 校验版本冲突，返回 409
- [ ] 更新 change_log

**请求**：
```http
PATCH /api/v2/statements/1/sections/left_section
If-Match: "v5"
Content-Type: application/json

{"fields": {"payment_date": "2026-01-15", "total_amount": "1234.56"}}
```

**响应**（200）：
```json
{
  "statement_id": 1,
  "section": "left_section",
  "updated_fields": 2,
  "new_version": 6
}
```

---

#### ✅ Task B2: 板块验证端点
- [ ] 实现 `POST /api/v2/statements/{id}/sections/{section_name}/validate`
- [ ] 检查字段完整性、格式正确
- [ ] 返回验证结果与错误列表

**响应示例**：
```json
{
  "valid": false,
  "errors": [
    {"field": "payment_date", "message": "date format invalid"}
  ]
}
```

---

#### 🔐 Task B3: 权限检查装饰器
- [ ] 创建 `@require_permission("import:write")` 装饰器
- [ ] 支持多权限检查（OR 逻辑）
- [ ] 权限不足返回 403
- [ ] 维护权限矩阵（见 API_DESIGN_V2.md）

---

#### 📝 Task B4: 审计日志记录
- [ ] 拦截所有写操作（POST/PATCH/DELETE）
- [ ] 记录：用户、操作类型、变更前后、时间戳
- [ ] 实现 `GET /api/v2/statements/{id}/change_log`

**change_log 样式**：
```json
[
  {
    "operation": "UPDATE",
    "user_id": "user-1",
    "field": "payment_date",
    "old_value": "2026-01-01",
    "new_value": "2026-01-15",
    "timestamp": "2026-01-06T11:00:00Z"
  }
]
```

---

#### 🔐 Task B5: Statement 批准端点
- [ ] 实现 `POST /api/v2/statements/{id}/approve`
- [ ] 验证所有板块已验证
- [ ] 更新 status = "approved"
- [ ] 记入审计日志，需 Editor+ 权限

---

### 阶段 B 验证标准

| 检查项 | 标准 |
|--------|------|
| 编辑功能 | 版本冲突正确返回 409 |
| 权限检查 | 每个端点正确验证权限 |
| 审计日志 | 每个写操作都记录 |
| 集成测试 | 编辑→验证→批准流程可重现 |

---

## 阶段 C：分析、导出、批量任务（周 4）

**目标**：支持数据分析、多格式导出、后台批量任务

### 任务分解

#### 📊 Task C1: 分析与汇总端点
- [ ] 实现 `GET /api/v2/analytics/summary`
- [ ] 支持时间范围过滤（start_date, end_date）
- [ ] 返回：总数据量、平均值、趋势
- [ ] 缓存结果（TTL 10 min）

**响应**：
```json
{
  "total_statements": 150,
  "avg_amount": 5432.10,
  "date_range": "2026-01-01 ~ 2026-01-06",
  "top_fields": [...]
}
```

---

#### 💾 Task C2: 导出端点
- [ ] 实现 `POST /api/v2/statements/{id}/export`
- [ ] 支持格式：csv, json, excel
- [ ] 后台异步处理（任务队列）
- [ ] 返回任务 ID，轮询状态
- [ ] 导出完成返回预签名 URL

**请求**：
```json
{"format": "csv", "include_fields": ["left_section", "right_section"]}
```

---

#### 🔄 Task C3: 批量导入端点
- [ ] 实现 `POST /api/v2/import/batch`
- [ ] 接收 pdf_paths 列表
- [ ] 异步后台处理（任务队列）
- [ ] 返回任务 ID 与进度查询端点

**请求**：
```json
{"pdf_paths": ["A.pdf", "B.pdf", "C.pdf"]}
```

---

#### ⏳ Task C4: 任务查询端点
- [ ] 实现 `GET /api/v2/tasks/{task_id}`
- [ ] 返回：status, progress, created_at, completed_at
- [ ] 支持状态：queued, processing, completed, failed

**响应**：
```json
{
  "task_id": "task-001",
  "status": "processing",
  "progress": 45,
  "total": 100,
  "message": "Processing: B.pdf"
}
```

---

### 阶段 C 验证标准

| 检查项 | 标准 |
|--------|------|
| 分析功能 | 数据聚合正确、缓存有效 |
| 导出功能 | CSV/JSON/Excel 格式正确 |
| 批量任务 | 后台异步处理、进度可追踪 |

---

## 阶段 D：性能优化、安全加固（2 月）

**目标**：性能达到生产标准，安全审计通过

### 任务分解

#### ⚡ Task D1: 缓存层集成（Redis）
- [ ] 集成 Redis 客户端
- [ ] 缓存 field_frequency（TTL 5 min）
- [ ] 缓存 statements 列表（TTL 1 min）
- [ ] 缓存失效策略（写时更新）

---

#### 🚦 Task D2: 限流与速率控制
- [ ] 实现基于 IP 的限流中间件
- [ ] 导入：10 次/分钟
- [ ] 导出：5 次/分钟
- [ ] 返回 429 + Retry-After 头

---

#### 🔐 Task D3: 安全加固
- [ ] HTTPS 强制（X-Forwarded-Proto 检查）
- [ ] 敏感字段脱敏（日志、响应）
- [ ] 输入校验加强（文件类型、大小）
- [ ] CORS 配置（生产白名单）

---

#### 📊 Task D4: 性能基准测试
- [ ] 导入 100 个 PDF：< 5 min（异步）
- [ ] 列表查询 1000 条：< 1 s
- [ ] 详情查询：< 500 ms
- [ ] 分析聚合：< 3 s

---

## 阶段 E：测试、文档、上线（3 月）

**目标**：完整测试覆盖、文档齐全、可上线部署

### 任务分解

#### 🧪 Task E1: 单元测试覆盖
- [ ] 所有路由层测试（> 90% 覆盖）
- [ ] 权限检查测试
- [ ] 错误处理测试

---

#### 📚 Task E2: 集成测试套件
- [ ] 完整导入→编辑→批准→导出流程
- [ ] 版本冲突场景
- [ ] 权限检查场景
- [ ] 审计日志验证

---

#### 📖 Task E3: API 文档完善
- [ ] Swagger 文档完成
- [ ] 开发者指南（认证、错误处理、示例）
- [ ] 部署指南

---

## 资源分配

| 阶段 | 开发人数 | 工作量 | 测试 |
|------|--------|--------|------|
| A | 1 | 40h | 8h |
| B | 1-2 | 60h | 12h |
| C | 1-2 | 50h | 10h |
| D | 1 | 30h | 8h |
| E | 1 | 20h | 10h |

---

## 风险及缓解措施

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|---------|
| 版本冲突频繁 | 中 | 高 | 前端刷新机制，实时通知 |
| 导入超时 | 中 | 中 | 大文件自动转异步，超时告知 |
| 缓存一致性 | 低 | 高 | 写时主动失效，定期检查 |

---

**文档完成**：2026-01-02  
**下次更新**：2026-01-10 (阶段 A 完成后)
