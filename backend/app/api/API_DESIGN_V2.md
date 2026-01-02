# Walmart PDF 解析系统 - API v2 设计规范

**版本**：2.0 | **日期**：2026-01-02 | **状态**：设计完成 | **审查评分**：8.2/10

## 核心特性
- 单文件导入（同步）+ 批量导入（异步）
- 前端人工校验与编辑（乐观锁、审计日志）
- 数据分析、汇总与多格式导出
- 角色权限控制（RBAC）

**基准路径**：`/api/v2/`  
**认证方式**：JWT Bearer Token（生产强制启用）

## 13 核心端点
1. `GET /api/v2/health` — 健康检查
2. `POST /api/v2/import` — 同步导入
3. `POST /api/v2/import/batch` — 批量导入
4. `GET /api/v2/tasks/{task_id}` — 任务查询
5. `GET /api/v2/statements` — 列表（分页）
6. `GET /api/v2/statements/{id}` — 详情
7. `PATCH /api/v2/statements/{id}/sections/{section_name}` — 编辑
8. `POST /api/v2/statements/{id}/sections/{section_name}/validate` — 验证
9. `POST /api/v2/statements/{id}/approve` — 批准
10. `GET /api/v2/analytics/summary` — 分析汇总
11. `POST /api/v2/statements/{id}/export` — 导出
12. `GET /api/v2/statements/{id}/change_log` — 审计日志

## RBAC 权限矩阵
| 角色 | import | edit | export | analytics | admin |
|------|--------|------|--------|-----------|-------|
| Viewer | ✅ | ❌ | ❌ | ✅ | ❌ |
| Editor | ✅ | ✅ | ✅ | ✅ | ❌ |
| Admin | ✅ | ✅ | ✅ | ✅ | ✅ |

## 数据一致性
- 乐观锁：`version` 字段 + `If-Match` header
- 审计日志：所有写操作记入 `change_log`
- 事务：DB 事务保证原子性
- 幂等性：`client_request_id` 支持（24h）

## 安全
- 生产强制 JWT，Token 1h 有效期
- 敏感字段脱敏
- RBAC 细粒度权限
- 导出 URL 签名（1h 有效期）

## 性能
- 缓存：field_frequency (5min), statements (1min), analytics (10min)
- 限流：导入 10/min, 导出 5/min
- 超时：导入 30s, 分析 60s

完整设计文档见 `.claude/API_DEVELOPMENT_ROADMAP.md` 和 `API_SECURITY_GUIDELINES.md`
