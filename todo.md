# Walmart PDF 解析系统 - API v2 开发任务清单

<<<<<<< HEAD
**更新日期**：2026-01-02 | **阶段**：API v2 设计完成，准备开始实现
=======
> **更新时间**: 2026-01-01 23:59 | **当前焦点**: V2 完成 + 文档整理 | **今日完成**: V2 实施 + WFS修复 + 文档整理
>>>>>>> 28b8e1f6342da6913199c0551ceba7975bdf3a7b

---

## 📊 项目状态概览

| 指标 | 状态 |
|------|------|
| **后端核心功能** | ✅ 完成（PDF 解析、右侧识别、数据导入） |
| **API v2 设计** | ✅ 完成（13 端点、RBAC、安全） |
| **开发路线图** | ✅ 完成（5 阶段计划） |
| **安全指南** | ✅ 完成 |
| **当前阶段** | 🔄 阶段 A（基础 API 实现） |
| **阻塞项** | 无 |

---

## 🎯 阶段 A：基础 API 实现（周 1）

**开始时间**：2026-01-06  
**完成目标**：5 个核心端点 + JWT 认证

### A1 项目结构初始化
- [ ] 创建 `backend/app/api/v2/` 目录结构
- [ ] 创建 `backend/app/api/v2/__init__.py`
- [ ] 创建 `backend/app/api/v2/schemas.py` — Pydantic 模型
- [ ] 创建 `backend/app/api/v2/routes.py` — 路由定义
- [ ] 创建 `backend/app/api/v2/dependencies.py` — 认证、日志
- [ ] 创建 `backend/app/api/v2/middleware.py` — 中间件
- [ ] 创建 `tests/integration/test_api_v2.py` — 集成测试
- **验证标准**：导入无报错，目录结构符合规范
- **时间估算**：2h

### A2 JWT 认证集成
- [ ] 在 `dependencies.py` 中实现 JWT Token 验证
- [ ] 实现 `get_current_user()` 依赖
- [ ] 支持测试 token（开发模式）
- [ ] 创建 Bearer Token 验证装饰器
- [ ] 实现权限检查装饰器 `@require_permission()`
- **验证标准**：
  ```bash
  curl -H "Authorization: Bearer test-token" http://localhost:8000/api/v2/health
  # 应返回 200 OK
  
  curl http://localhost:8000/api/v2/health
  # 应返回 401 Unauthorized
  ```
- **时间估算**：4h

### A3 健康检查端点
- [ ] 实现 `GET /api/v2/health`
- [ ] 检查 app、database、queue 组件状态
- [ ] 返回 JSON 格式的状态信息
- [ ] 编写单元测试
- **验证标准**：返回 {"status": "ok", "components": {...}}
- **时间估算**：1h

### A4 导入端点（同步）
- [ ] 实现 `POST /api/v2/import`
- [ ] 调用现有 PDFParserService
- [ ] 存储结果到 statements + section_data 表
- [ ] 支持 client_request_id 幂等性
- [ ] 返回 statement_id 与处理摘要
- [ ] 编写单元测试
- **验证标准**：
  ```bash
  curl -X POST http://localhost:8000/api/v2/import \
    -H "Authorization: Bearer test-token" \
    -H "Content-Type: application/json" \
    -d '{"pdf_path": "PdfData/test.pdf"}'
  # 应返回 {"status": "success", "statement_id": 1, ...}
  ```
- **时间估算**：6h

### A5 Statements 列表端点
- [ ] 实现 `GET /api/v2/statements`
- [ ] 支持分页（page, size）和排序（sort）
- [ ] 返回摘要信息（id, created_at, status）
- [ ] 权限检查（Viewer+ 可读）
- [ ] 缓存优化（TTL 1 min）
- [ ] 编写单元测试
- **验证标准**：
  ```bash
  curl "http://localhost:8000/api/v2/statements?page=1&size=20" \
    -H "Authorization: Bearer test-token"
  # 应返回分页结果
  ```
- **时间估算**：4h

### A6 Statement 详情端点
- [ ] 实现 `GET /api/v2/statements/{id}`
- [ ] 返回完整数据（所有板块、字段）
- [ ] 包含 version 字段（用于乐观锁）
- [ ] 权限验证（用户仅能访问自己上传的数据）
- [ ] 编写单元测试
- **验证标准**：
  ```bash
  curl http://localhost:8000/api/v2/statements/1 \
    -H "Authorization: Bearer test-token"
  # 应返回包含 version、left_section、right_section 的完整数据
  ```
- **时间估算**：3h

### 阶段 A 总结
- **总工作量**：20h 开发 + 8h 测试 = 28h
- **预计完成日期**：2026-01-10
- **成果物**：
  - 5 个核心端点
  - JWT 认证系统
  - Swagger API 文档自动生成
  - 完整单元 + 集成测试

---

## 🎯 阶段 B：编辑、权限、审计（周 2-3）

**开始时间**：2026-01-13  
**完成目标**：PATCH/POST 端点、权限控制、审计日志

### B1 编辑端点（PATCH）
- [ ] 实现 `PATCH /api/v2/statements/{id}/sections/{section_name}`
- [ ] 乐观锁机制（If-Match header）
- [ ] 版本冲突返回 409
- [ ] 更新 change_log 表
- [ ] 编写测试（包括版本冲突场景）

### B2 板块验证端点
- [ ] 实现 `POST /api/v2/statements/{id}/sections/{section_name}/validate`
- [ ] 字段完整性检查
- [ ] 格式验证
- [ ] 返回验证结果与错误列表

### B3 权限系统完善
- [ ] 实现 RBAC 细粒度权限检查
- [ ] 创建权限检查装饰器
- [ ] 定义 Viewer/Editor/Admin 角色
- [ ] 为所有端点应用权限检查

### B4 审计日志记录
- [ ] 创建中间件拦截写操作
- [ ] 记录：用户 ID、操作类型、变更前后、时间戳、源 IP
- [ ] 实现 `GET /api/v2/statements/{id}/change_log`
- [ ] 编写审计日志查询测试

### B5 Statement 批准端点
- [ ] 实现 `POST /api/v2/statements/{id}/approve`
- [ ] 验证所有板块已验证
- [ ] 更新 status = "approved"
- [ ] 记入审计日志

**总工作量**：60h 开发 + 12h 测试 = 72h  
**预计完成日期**：2026-01-27

---

## 🎯 阶段 C：分析、导出、批量任务（周 4）

**开始时间**：2026-01-27  
**完成目标**：异步任务、分析、导出端点

### C1 分析与汇总端点
- [ ] 实现 `GET /api/v2/analytics/summary`
- [ ] 支持时间范围过滤
- [ ] 返回统计数据（总数、平均值、趋势）
- [ ] 缓存结果（TTL 10 min）

### C2 导出端点（异步）
- [ ] 实现 `POST /api/v2/statements/{id}/export`
- [ ] 支持 CSV、JSON、Excel 格式
- [ ] 后台异步处理（任务队列）
- [ ] 返回预签名 URL（1h 有效期）

### C3 批量导入端点
- [ ] 实现 `POST /api/v2/import/batch`
- [ ] 异步后台处理
- [ ] 进度追踪

### C4 任务查询端点
- [ ] 实现 `GET /api/v2/tasks/{task_id}`
- [ ] 返回进度信息

**总工作量**：50h 开发 + 10h 测试 = 60h  
**预计完成日期**：2026-02-03

---

## 🎯 阶段 D：性能优化、安全加固（2 月）

**开始时间**：2026-02-03  
**完成目标**：性能基准达成、安全审计通过

### D1 缓存层集成
- [ ] 集成 Redis 客户端
- [ ] 缓存 field_frequency（TTL 5 min）
- [ ] 缓存 statements 列表（TTL 1 min）
- [ ] 缓存失效策略

### D2 限流与速率控制
- [ ] 实现限流中间件
- [ ] 导入：10 次/分钟
- [ ] 导出：5 次/分钟

### D3 安全加固
- [ ] HTTPS 强制
- [ ] 敏感字段脱敏
- [ ] 输入校验加强
- [ ] CORS 配置

### D4 性能基准测试
- [ ] 导入 100 个 PDF < 5 min
- [ ] 列表查询 1000 条 < 1 s
- [ ] 详情查询 < 500 ms
- [ ] 分析聚合 < 3 s

**总工作量**：30h 开发 + 8h 测试 = 38h

---

## 🎯 阶段 E：测试、文档、上线（3 月）

**开始时间**：3 月初  
**完成目标**：完整测试覆盖、文档齐全、部署就绪

### E1 单元测试覆盖
- [ ] 路由层测试 > 90%
- [ ] 权限检查测试
- [ ] 错误处理测试

### E2 集成测试套件
- [ ] 完整工作流测试
- [ ] 版本冲突场景
- [ ] 权限场景
- [ ] 审计日志验证

### E3 API 文档完善
- [ ] Swagger 文档
- [ ] 开发者指南
- [ ] 部署指南

**总工作量**：20h 开发 + 10h 测试 = 30h

---

## 📋 关键里程碑

| 日期 | 里程碑 | 验证方式 |
|------|--------|---------|
| 2026-01-10 | 阶段 A 完成 | 5 个端点 + 集成测试通过 |
| 2026-01-27 | 阶段 B 完成 | 编辑+权限+审计功能通过 |
| 2026-02-03 | 阶段 C 完成 | 异步任务、导出功能通过 |
| 2026-02-20 | 阶段 D 完成 | 性能基准达成、安全审计通过 |
| 2026-03-10 | 阶段 E 完成 | 测试覆盖 > 95%，文档完成 |
| 2026-03-15 | 📦 v2 上线 | 生产环境正式运行 |

---

## 📌 每日进度检查清单

**每日检查**（开发期间）：

- [ ] 代码修改范围精简
- [ ] 新增功能附带测试用例
- [ ] 更新关联文档
- [ ] CI/CD 测试通过
- [ ] 代码审查完成

---

## 🔧 资源与依赖

### 开发资源
- **开发人员**：1-2 人
- **测试人员**：1 人
- **总工作量**：~250 小时（5 周）

### 外部依赖
- FastAPI 框架
- SQLAlchemy ORM
- Redis（可选，用于缓存）
- Celery（可选，用于异步任务）

### 环境要求
- Python 3.9+
- PostgreSQL 12+（生产）
- Redis 6.0+（可选）

---

## 🎁 可交付物

| 交付物 | 完成日期 |
|--------|---------|
| API v2 完整实现 | 2026-02-03 |
| Swagger API 文档 | 2026-03-10 |
| 开发者指南 | 2026-03-10 |
| 部署指南 | 2026-03-10 |
| 测试覆盖报告 | 2026-03-10 |
| 性能基准报告 | 2026-02-20 |
| 安全审计报告 | 2026-02-20 |

---

## 📝 更新日志

### 2026-01-02
- ✅ 创建 API v2 完整设计文档
- ✅ 制定 5 阶段开发路线图
- ✅ 编写安全指南和最佳实践
- ⏳ 准备开始阶段 A（基础 API）

### 2025-12-25
- ✅ 后端核心功能完成
- ✅ 数据库 v2 迁移完成
- ✅ 批量导入和右侧识别验证通过

---

**维护者**：开发团队  
**最后更新**：2026-01-02
