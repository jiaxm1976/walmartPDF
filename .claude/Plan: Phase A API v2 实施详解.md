采用交互的方式，列出具体执行的任务清单，任务列表和交互采用中文，任务详细说明，帮助我初学者学习
Plan: Phase A API v2 实施详解

TL;DR：本计划按“清除 v1 → 从零构建 v2 → 逐步验证与提交”的顺序推进。原因是当前工作区存在 v1 引用但缺少 v1 代码，会导致服务启动/测试导入阶段直接失败。为便于初学者执行，本计划把 Phase A 拆成若干可回滚的小步，每步说明：为什么做、目的是什么、具体改哪些文件/符号、怎么验证、怎么回滚。

### Steps（逐步详解）

0. 清除 v1（完全重建前置步骤，必须先做）
- 为什么：当前入口文件会 import/挂载 v1，但工作区没有 `backend/app/api/v1/` 代码（仅归档目录里有旧版示例）。如果不先清除 v1，后续任何“启动 FastAPI / 导入 app / 跑测试”都会在 import 阶段失败，新手会被卡死。
- 目的：让后端服务在“只有 v2 的情况下”也能稳定启动；避免隐形依赖；明确版本边界。
- 范围定义（什么叫“清除 v1”）：
  - 删除或禁用 `backend/main.py` 中对 v1 的 import 与 `app.include_router(..., prefix="/api/v1")`。
  - 迁移 v1 的最小公共端点（如 `/health`）到 v2 或根路由；最终只保留 `/api/v2/*` 作为业务 API。
  - 保留归档目录（`archived/`）不参与运行与测试。
- 示例操作（概念性说明）：
  - 将 `from app.api.v1 import api_router` 改为移除或条件导入；将 v1 的 include_router 删除。
  - 在入口用“条件导入 v2”或“强依赖 v2”两种策略二选一（见步骤 2 的说明）。
- 验证：
  - 仅验证“应用可导入”：在测试中 import `app` 不报错；或启动服务能打开 `/api/docs`。
  - 验证 v1 路由不可访问（请求 `/api/v1/...` 返回 404）。
- 回滚：使用 git 恢复 `backend/main.py` 相关改动。

1. 提交并确认设计文档
- 为什么：把设计快照入版本库，确保团队与 CI 能基于同一规范开展开发；便于审查与回滚。
- 目的：将 API 设计、路线图、安全规范、README 与 `todo.md` 的最终版锁定在 Git 历史中。
- 具体操作：检查并提交下列文件（若任一仍为占位，请先替换内容）：
  - `backend/app/api/API_DESIGN_V2.md`、`.claude/API_DEVELOPMENT_ROADMAP.md`、`.claude/API_SECURITY_GUIDELINES.md`、`README.md`、`todo.md`
- 示例命令（本地执行）：
```
git add backend/app/api/API_DESIGN_V2.md .claude/API_DEVELOPMENT_ROADMAP.md .claude/API_SECURITY_GUIDELINES.md README.md todo.md
git commit -m "docs(api): persist API v2 design & roadmap"
git push origin <branch>
```
- 验证：`git log --oneline -n 1` 查看提交，打开文件确认内容。
- 回滚：若提交有误，使用 `git reset --soft HEAD~1`（撤回最近一次提交）或 `git checkout -- <file>` 恢复单文件。

2. 在主入口挂载 `v2` 路由（从零开始的第一块“可运行代码”）
- 为什么：清除 v1 后，服务需要一个明确的 API 入口；挂载 v2 可以快速验证“路由装载、依赖注入、测试导入路径”都正常。
- 目的：让 `/api/v2/*` 成为唯一业务 API 前缀，并在 Swagger `/api/docs` 中可见。
- 具体修改：编辑 `backend/main.py`，添加 v2 路由挂载：`app.include_router(api_v2_router, prefix="/api/v2")`。
- 两种策略（推荐新手选 A）：
  - A. 条件导入（更稳）：v2 文件不存在时也能启动基础服务（但 `/api/v2` 为空）。适合逐步创建文件。
  - B. 强依赖导入（更严格）：要求 v2 模块必须存在，否则启动失败。适合你已经准备好 v2 骨架文件。
- 关键符号：在 `backend/app/api/v2/__init__.py` 暴露 `api_router`。
- 验证：启动服务后在 `/api/docs` 看到 v2 分组；或测试访问 `/api/v2/health` 返回 200。
- 回滚：恢复 `backend/main.py` 改动。

3. 搭建 v2 骨架（routes / schemas / dependencies）✅ 已完成
- 为什么：分层（路由/模型/依赖）有利于职责分明、单元测试与后续扩展；先做骨架能尽早验证依赖注入与路由结构。
- 目的：创建可独立测试的基础模块，便于在不影响其它代码的情况下实现端点。
- 已创建的文件与符号：
  - ✅ `backend/app/api/v2/__init__.py`（暴露 `api_router`）
  - ✅ `backend/app/api/v2/routes.py`（导出 `router`，已实现 `GET /health`、`POST /import`、`POST /import_parsed`）
  - ✅ `backend/app/api/v2/schemas.py`（Pydantic：`ImportRequest`、`ImportResponse`、`ImportParsedRequest`）
  - ✅ `backend/app/api/v2/dependencies.py`（`get_current_user` 已实现，支持 dev-token）
- 新增功能（超出原计划）：
  - ✅ `POST /api/v2/import_parsed`（读取已解析 JSON，合并右侧数据，导入 DB）
  - ✅ `scripts/import_parsed_json.py`（手动导入脚本）
- 验证结果：
  - ✅ `/api/v2/health` 可访问，返回版本信息
  - ✅ `/api/v2/import_parsed` 成功导入 DB（statement_id 1-3 已写入）
- 回滚方案：使用 `git reset HEAD~<n>` 恢复

4. 实现最小认证依赖（先 dev-mode，再替换为生产 JWT）
- 为什么：认证依赖将来是安全边界；先实现简易 dev-token 能保证本地调试不受阻并为未来替换留接口。
- 目的：提供统一的 `get_current_user` 依赖以注入路由；为 RBAC 做扩展点（`require_permission`）。
- 具体修改：在 `backend/app/api/v2/dependencies.py` 提供函数 `get_current_user(credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer(auto_error=False)))`：
  - 若无 token → 返回 `{"username":"dev","role":"admin"}`（便于调试）
  - token == `devtoken` → 返回 dev 用户；否则抛 401
- 示例（调用/验证）：在 `routes.py` 的 `import` 路由中添加参数 `user=Depends(get_current_user)`；用 `TestClient` 测试带/不带 `Authorization` header 的行为。
- 验证：带 `Authorization: Bearer devtoken` 时通过；无 header 时也可通过（视策略决定）；错误 token 返回 401。
- 回滚：恢复依赖文件或在 commit 中单独回滚该改动。

5. 实现 Phase A 端点（health / import / statements list/detail）
- 为什么：这些端点构成最小可用 API，能验证服务链（API → 服务层 → DB/存储/ocr），且为前端与集成测试提供契约。
- 目的：实现可校验的功能入口，使团队能开始集成测试并迭代改进。
- 具体实现细节：
  - `GET /api/v2/health`：返回 `{status, version}`；用于路由挂载验证。
  - `POST /api/v2/import`：请求体 `ImportRequest(pdf_path, output_dir)`，注入 `user`，同步调用 `PDFParserService.parse_pdf_direct(pdf_path, output_dir)`，根据返回抛 5xx 或返回 `ImportResponse`。文件：`backend/app/api/v2/routes.py`、`schemas.py`。
  - `GET /api/v2/statements`：最小实现返回空列表或从现有 DB 表查询（若尚无模型，先返回 mock/空数据以完成 API contract）。
  - `GET /api/v2/statements/{id}`：返回 statement 详情或 404。若实现 DB，请在 `backend/database/config.py` 确保 `init_database()` 创建必要表。
- 示例（调用示意）：向 `POST /api/v2/import` 发送 `pdf_path=/path/to/small.pdf`（测试时建议用项目内小样本或 mock）。
- 验证：使用 `TestClient` 或 curl 调用 `import`（若同步执行时间长，可在测试中 mock `PDFParserService.parse_pdf_direct`）。观察返回结构与 HTTP code。
- 回滚：移除或禁用路由、恢复旧代码。

6. 编写并运行测试（单元 + 基本集成，OCR mock）✅ 已完成
- 为什么：测试减少回归风险，特别 OCR 与 PDF 处理为外部/重依赖（慢且大）必须 mock。
- 目的：验证路由、依赖、service 调用的正确性；在 CI 中保证基础功能不被破坏。
- 已实现的测试：
  - ✅ `backend/app/api/v2/tests/test_v2_basic.py`（直接调用 `v2_health()`）
  - ✅ `backend/app/api/v2/tests/test_import_parsed_endpoint.py`（单元测试，直接调用 `import_parsed`）
  - ✅ `backend/app/api/v2/tests/test_import_parsed_integration.py`（集成测试，真实 uvicorn + requests）
- 验证结果：
  - ✅ `pytest backend/app/api/v2 -q` 结果：4 passed
  - ✅ 集成测试耗时 ~3.38s（含服务器启动/停止）
  - ✅ 使用 UUID 避免 DB 唯一约束冲突
- 回滚方案：使用 `git reset` 恢复

补充：测试导入路径的“新手保险丝”（强烈建议加入本计划并执行）
- 为什么：你之前已经遇到 `ModuleNotFoundError: No module named 'backend'`，这通常不是业务代码错，而是 pytest 的运行目录/导入路径导致的“假失败”。
- 建议做法（二选一即可）：
  - 做法 1（推荐）：统一从仓库根目录运行 pytest，不要 `cd backend` 后再跑。
  - 做法 2：在测试执行命令里显式指定 `PYTHONPATH=.`（适用于你理解环境变量后再用）。
- 目的：保证 `from backend.main import app` 或其它模块导入稳定可复现。

7. 分次提交并推送（小步快推，便于审查）📋 待执行

**待提交的改动清单**：

**Commit 1 - 功能实现（API v2 导入端点 + 脚本）**
```
feat(api/v2): add /import_parsed endpoint + manual import script
```
改动文件：
- `backend/app/api/v2/routes.py`：新增 `import_parsed` 端点（读取 parsed JSON，合并 right_section，调用 StructuredDataImporter）
- `backend/app/api/v2/schemas.py`：新增 `ImportParsedRequest` 模型
- `scripts/import_parsed_json.py`：新增手动导入脚本（本地验证工具）

**Commit 2 - 测试实现（单元 + 集成测试）**
```
test(api/v2): add import_parsed unit & integration tests (4 passed)
```
改动文件：
- `backend/app/api/v2/tests/test_v2_basic.py`：修复 TestClient 兼容问题，改为直接调用 `v2_health()`
- `backend/app/api/v2/tests/test_import_parsed_endpoint.py`：新增单元测试（UUID-based pdf_name）
- `backend/app/api/v2/tests/test_import_parsed_integration.py`：新增集成测试（真实 uvicorn + HTTP 请求）

**Commit 3 - 文档更新**
```
docs: update Phase A API v2 implementation plan (mark complete + add commit guide)
```
改动文件：
- `.claude/Plan: Phase A API v2 实施详解.md`：标记步骤 3、6 完成，添加实现总结与下一步展望
- `README.md`（可选）：添加 `/api/v2/import_parsed` 使用文档示例

- 为什么：分功能提交便于 Code Review、定位回滚点并减少冲突；每次提交只包含一类改动（docs、路由、认证、端点、测试）。
- 目的：保持清晰的 Git 历史与可回溯性。
- 验证：`git show --name-only HEAD`、Push 后检查远端分支与 CI（若存在）。
- 回滚：使用 `git revert <commit>` 或 `git reset`（本地）按需恢复。

---

### Apple Vision（OCR）相关注意（你已可用）
- 为什么强调：OCR 模型大/慢，不同环境差异大，Vision 在 macOS 上速度快且测试友好。
- 目的：用最可靠/快速的 OCR 在本地开发，CI 用 mock 或在 macOS runner 执行集成测试。
- 实践建议：通过环境变量控制引擎，代码读取 `OCR_ENGINE=vision|paddle|mock`，测试阶段设置为 `mock`：`OCR_ENGINE=mock pytest ...`。在代码中实现 `OCREngine(engine_type)` 的工厂模式以便替换。
- 示例说明：开发时 `OCREngine(engine_type="vision")`；测试时用 `monkeypatch` 将 `OCREngine` 替换为返回固定识别结果的 stub。

补充：Vision 已可用时的推荐分层（避免测试依赖 OCR）
- 为什么：Vision 适合本机开发验证，但不适合作为默认自动化测试依赖（平台限制 + 耗时）。
- 建议：
  - 单元测试：永远 mock `PDFParserService.parse_pdf_direct`（最快、最稳定）。
  - 本机手工集成验证：再用真实 PDF + Vision 跑一次 import（用于信心验证，不进入 CI 默认路径）。

---

### 初学者小贴士
- 先做“可运行的最小实现”（MVP）：先让 `GET /api/v2/health` 工作，再逐步添加 `import`（先用 mock），最后连接真实的 `PDFParserService`。
- 调试顺序：routes → dependencies → service 调用（从外到内）。遇到错误先看日志与堆栈，并用小样本重现。
- 使用版本控制：每做一组改动就 commit；若不确定，开一个临时分支做实验（`git checkout -b feat/api-v2-scaffold`）。

如果你同意这份包含"为什么/目的/操作/示例/验证/回滚"的详尽计划，我可以按上述 3 个 commit 分组执行提交并推送到 `fix/pdf-ocr-db` 分支。你确认现在开始执行提交与推送吗？

---

### 实现总结（Phase A 核心部分已完成）✅

**已实现功能**：
- ✅ v2 基础骨架（routes/schemas/dependencies）
- ✅ `/api/v2/health` 端点（已测试）
- ✅ `/api/v2/import` 端点（已实现，支持 dev-token 认证）
- ✅ **新增** `/api/v2/import_parsed` 端点（核心功能：从 parsed JSON 导入到 DB）
- ✅ 手动导入脚本 `scripts/import_parsed_json.py`（本地验证工具）
- ✅ 单元测试 + 集成测试（4 个测试全部通过）
- ✅ 数据库导入验证（已成功写入 statements 和 section_data）

**下一步操作**：
1. 执行 3 个分组 commit（见上方提交清单）
2. 推送到分支 `fix/pdf-ocr-db`
3. 可选：创建 PR 并请求审查

**Phase B 展望**（推荐后续工作）：
- 实现 `GET /api/v2/statements` 端点（查询已导入的 PDF 数据）
- 实现 `GET /api/v2/statements/{id}` 端点（获取单个 statement 详情）
- 前端集成（React 调用 v2 API）
- 生产环保安全措施（JWT 替换 dev-token、RBAC、速率限制）
