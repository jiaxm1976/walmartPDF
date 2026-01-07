## PR 草案：V2 类型、API 示例与导入器改进

摘要
-------
本次 PR 为解析/导入流水线引入 Pydantic v2 模型、在服务间增加更严格的类型约束、为 v2 路由添加 OpenAPI 示例，并增加一个带类型的导入封装。另增前端调试用的 curl 示例脚本，并更新相关文档。

主要变更
-----------
- 新增 Pydantic 模型：`backend/app/schemas/v2.py`（`PaymentItem`、`JGData`、`ParseResult`、`ImportResult`）。
- 在 `PDFParserService.parse_pdf_direct` 中使用 `ParseResult` 对解析输出做验证/规范化。
- 在 `backend/database/structured_importer.py` 中新增 `import_from_model(pdf_name: str, jg_data: JGData) -> ImportResult`，并使 `import_jg_data` 支持接收/验证 `JGData`。
- 添加并暴露了 `StructuredDataImporter.exists()`、`get_statistics()` 与 `get_field_frequency()`（用于脚本支持，已在文件历史中存在）。
- 更新 `scripts/batch_import_v2.py`：在解析后尝试用 `JGData` 验证并优先调用 `import_from_model`。
- 为 API v2 添加端点示例与响应示例：`backend/app/api/v2/routes.py`（新增 `/parse`、调整 `/import` 响应）。
- 在 `backend/app/schemas/v2.py` 中通过 `model_config.json_schema_extra` 添加 OpenAPI 示例。
- 新增 CLI 脚本 `scripts/api_examples.sh`（curl 示例），并在 `README.md` 与 `backend/app/api/API_DESIGN_V2.md` 中增加用法示例。

改动文件（概要）
-----------------
- backend/app/schemas/v2.py（新增/更新）
- backend/app/services/pdf_parser_service.py（校验并返回 `ParseResult`）
- backend/app/services/right_section_ocr.py（类型注解）
- backend/database/structured_importer.py（新增 `import_from_model`，验证逻辑）
- backend/app/api/v2/routes.py（新增 `/parse`，调整 `/import` 响应）
- scripts/batch_import_v2.py（使用 `JGData` + `import_from_model`）
- scripts/api_examples.sh（新增）
- README.md（curl 示例）
- backend/app/api/API_DESIGN_V2.md（示例）

测试
-------
- 已执行后端测试：`PYTHONPATH=. pytest backend/tests -q`，结果 `30 passed, 10 warnings`。

说明
-----
- 如果没有权限或未配置远程仓库，`git push` 可能失败；若失败我可以把分支保存在本地或按需重试推送。
- 若需要指定分支名，请告知，我会在推送前替换分支名称。

建议的 PR 标题
------------------
feat(v2): 添加 Pydantic 模型、类型安全、API 示例与导入封装

-- 草案结束
