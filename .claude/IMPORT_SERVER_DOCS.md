# 服务端：PDF 导入与处理（文档）

本文件说明仓库中“文件导入 / 批量导入”相关的服务端代码、脚本和运行方法，便于开发者快速上手、排查问题与维护。

---

## 目标

- 描述导入流程（从 PDF 到结构化数据到入库）的各个模块与调用链。
- 提供常用命令、运行示例与调试步骤。
- 列出建议归档/删除的旧文档以保持仓库整洁。

---

## 架构概览（关键模块）

- PDF 解析与板块提取
  - `backend/app/services/pdf_parser_service.py`：解析流程主入口（`parse_pdf_direct` 等），负责 PDF->图片->左右切分->左侧结构化与右侧 OCR。
  - `backend/app/services/keyword_locator.py`：定位横向切分点与关键字定位工具。

- 左侧数据处理
  - `backend/app/services/left_image_processor_service.py`：获取左侧图片处理器的工厂函数（`get_left_image_processor()`）。
  - 左侧处理器实现位于 `backend/app/services/` 下（以 `left_...` 命名）。

- 右侧 OCR 与后处理
  - `backend/app/services/right_section_ocr.py`：右侧付款详情 OCR 与字段提取器（`RightSectionOCR`），可以在内部初始化 `OCREngine`，提供 `process_right_image(image)` 返回 `{"payment_details": {...}}`。
  - `backend/app/services/right_section_processor.py`：将 `right_section` 格式化并合并到主结构化数据（若存在）。

- OCR 引擎封装
  - `backend/app/services/ocr_engine.py`：封装不同 OCR 后端（Apple Vision / PaddleOCR），提供 `recognize_image`、`recognize_image_text` 等方法。

- 入库与结构化导入
  - **`backend/database/structured_importer.py`**：`StructuredDataImporter.import_jg_data()`，接收 `jg_data` 并写入 `statements` 与 `section_data` 表。
    - **更新** (2026-01-02)：添加了输入验证、数据结构检查、错误恢复与事务回滚逻辑（详见代码审计报告）。
    - 保留 `right_section` 为独立板块，避免被低频合并。
    - 现在能够跟踪部分失败情况并报告失败的板块。

- 启动/维护脚本
  - `scripts/init_database_v2.py`：初始化 V2 schema 与 `field_frequency`。
  - `scripts/batch_import_v2.py`：批量导入脚本，遍历 `PdfData/` 下 PDF 并调用解析+入库流程。
  - `scripts/test_single_pdf_import.py` / `scripts/test_parse_pipeline.py`：单文件或子流程测试脚本。

---

## 常用运行命令（推荐在项目 `.venv` 中运行）

```bash
# 1. 初始化数据库（会备份旧库）
python scripts/init_database_v2.py

# 2. 测试单个 PDF 导入（快速验证）
python scripts/test_single_pdf_import.py

# 3. 批量导入（所有 PdfData 下的 PDF）
.venv/bin/python scripts/batch_import_v2.py
# 或在激活虚拟环境后直接
python scripts/batch_import_v2.py

# 4. 验证查询（可选）
python scripts/verify_queries.py
```

> 注意：若强制使用 Apple Vision，请在运行环境（虚拟环境）中确保 `Vision` 导入可用（macOS）。否则配置 `OCREngine` 以回退到 PaddleOCR。

---

## 运行时注意事项与调试

- 环境依赖：确保 `backend/requirements.txt` 所列依赖已安装；对于 Apple Vision，需在 macOS 且 pyobjc 可用。
- 日志与中间结果：批量导入脚本会打印每个 PDF 的 4 步状态（解析、左侧提取、右侧提取、入库）。若右侧提取被跳过，请查看 `RightSectionOCR` 的日志（`extract_text_lines` / `merge_text_blocks` 输出）。
- 常见错误：
  - "No module named 'Vision'": 在非 macOS 或未安装 pyobjc 时常见。解决：切换 OCR 引擎或安装依赖。
  - "'str' object has no attribute 'center_y'": 表示 `merge_text_blocks` 或 OCR 返回的数据格式异常。已在 `right_section_ocr.py` 添加防御性逻辑；若再次出现，请把识别的 `ocr_results` 输出保存用于排查。

---

## 测试与回归

- 单元测试目录：`backend/tests/`。建议为 `RightSectionOCR` 新增单元测试覆盖 `extract_text_lines` 与 `extract_payment_details`。
- 快速运行单测（仅后端）：

```bash
pytest backend/tests -q
```

---

## 建议的文档清理候选（请确认后我会执行归档或删除）

下面列出仓库中发现的潜在过期/冗余文档或脚本，建议先移动到 `.claude/archive/` 或 `archived/`，确认无用后再删除：

- `backend/database/schema_design_v1.sql`  — 旧的 v1 schema 初始化脚本，仓库现在使用 V2 动态 schema。
- `.claude/archive/` 下的历史实现文档（如 `DATABASE_IMPLEMENTATION_SUMMARY.md`, `DATABASE_SCHEMA_DESIGN.md` 等），若已在新版文档中覆盖，可归档。
- `backend/.claude/context/phase3-api-integration-summary.md`（若重复或已过时可归档）。

我不会直接删除这些文件，除非你回复确认“现在删除”或指定要删除的文件清单。建议先把它们移动到 `archived/` 或 `.claude/archive/`。

---

## 变更记录

- 2026-01-02: 添加 `IMPORT_SERVER_DOCS.md`（本文件），并列出候选过期文档供确认。

---

如需我现在：
- a) 将候选文件移动到 `archived/`（会在仓库保留一份），或
- b) 立即删除指定文件（请明确文件清单），或
- c) 把本文件合并到 README 并创建变更 PR。

请回复你的选择。