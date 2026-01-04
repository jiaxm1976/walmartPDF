目标：
- 统一解析返回格式，拆耦数据库导入接口，规范右侧 OCR 流程，为 V2 API 重构打基础。

核心设计（一句话）：
- `PDFParserService` 输出稳定的 `ParseResult`；`StructuredDataImporter` 暴露 `exists()` 与 `get_statistics()`；右侧 OCR 与处理统一由服务层合并为 `sections['right_section']`。

最小迁移步骤：
1. 创建 `backend/app/schemas/v2.py`（Pydantic 模型草案）。
2. 修改 `PDFParserService.parse_pdf_direct` 返回并校验 `ParseResult`（兼容旧 keys）。
3. 在 `StructuredDataImporter` 添加 `exists(pdf_name)->bool` 和 `get_statistics()->Dict`，保留 `import_jg_data()`。
4. 更新 `scripts/batch_import_v2.py` 使用 `importer.exists()` 与 `ParseResult.data`，并去除脚本直接读 `importer.conn` 的 SQL。
5. 小范围单元测试覆盖模型、`exists()` 和导入逻辑。

简洁接口契约（概念）：
- ParseResult: { status: 'SUCCESS'|'ERROR', success: bool, data?: { left_section: JGStructuredData, right_section?: Dict }, error?: str, process_time?: float }
- JGStructuredData: { sections: Dict[str, List<Item>], metadata?: Dict }
- Item: { field: str, value: Any, raw?: str }
- StructuredDataImporter: exists(pdf_name)->bool, import_jg_data(pdf_name, jg_data)->Optional[int], get_statistics()->Dict

关键数据流（ASCII 结构化）：
PDF 文件
  ↓
`PDFParserService.parse_pdf_direct(pdf_path)`
  ↓ left_image → `LeftImageProcessor.process_left_image` → left_data (jg_structured_data)
  ↓ right_image → `RightSectionOCR.process_right_image` → right_raw_dict
  ↓ 合并 → jg_data (sections + metadata，包含 `right_section`)
  ↓ 脚本读取 `ParseResult.data`，可选 `RightSectionProcessor.format_right_section_for_db` 进行格式化
  ↓ `StructuredDataImporter.import_jg_data(pdf_name, jg_data)` 写入 DB (`statements` / `section_data`)
  ↓ verify_database() 读取统计并生成报告

立即可做的一件事：
- 在 `StructuredDataImporter` 添加 `exists()` 并立即替换脚本中直接读取 `importer.conn` 的部分，快速降低耦合，便于后续改造。

兼容与降级策略（一句话）：
- 在短期内在 `ParseResult` 中同时支持旧字段（`status` 与 `success`），右侧识别失败时允许只导入左侧并将错误写入日志/返回值。

交付物（我可以生成）：
- `backend/app/schemas/v2.py`（Pydantic 草案）
- 小补丁列表（分步提交）
- 可选：把 ASCII 图存为 `docs/flow_ascii.txt` 或写入 README

下一步：是否将此计划文件保存到仓库（`docs/plan-v2-refactor.md`）或我直接开始实现第 1 步创建 Pydantic 模型？
