Walmart-a 项目的 Copilot/AI 代理使用说明

**默认交互语言：简体中文（zh-CN）**。请使用中文回答所有交互、注释与文档，除非有明确说明需要使用其它语言。

所有交互和文档使用中文
目标
帮助 AI 编码代理快速熟悉本仓库并高效开展工作。操作应保持轻量化、有测试支撑且可回退。
项目概览 ✅
技术栈：Python 后端（3.9 及以上版本，已适配 3.11）+ React 前端（基于 CRA 创建）。
核心模块：backend/（OCR 识别、PDF 解析、FastAPI 接口）、frontend/（React 应用）、scripts/（脚本工具）和.claude/（项目 / 上下文文档）。
注意事项：大型机器学习模型（PaddleOCR）将在运行时自动下载，请勿提交模型文件、虚拟环境或其他大文件至仓库。
环境配置与常用命令 🔧
创建并激活虚拟环境（macOS/Linux 系统）：
python -m venv .venv && source ./ .venv/bin/activate

（注：仓库脚本已兼容 legacy `venv`，推荐使用 `.venv`）
安装 Python 依赖：
pip install -r backend/requirements.txt
启动后端 API 服务（开发环境）：
uvicorn backend.main:app --reload --port 8000（接口文档地址：http://localhost:8000/api/docs）
或执行 python backend/main.py（该模块内置了 uvicorn 运行器）。
运行测试：
批量运行测试：pytest backend/tests -q；运行单个测试文件：pytest backend/tests/unit/test_pdf_parser.py -q
启动前端（开发环境）：
cd frontend && npm install && npm start
实用脚本工具：
python scripts/quick_visualize.py <pdf> 或 python scripts/create_calibration.py（详见scripts/目录下说明）
架构概览（优先阅读文件）📚
backend/app/services/ — 核心业务逻辑层（包含 ocr_engine.py、pdf_parser.py、image_splitter.py、keyword_extractor/locator 等模块）
backend/main.py — FastAPI 应用实例与启动钩子（调用database.config.init_database()初始化数据库）
backend/database/config.py — 数据库配置：默认使用 SQLite 数据库，文件路径为backend/data/walmart_pdf_parser.db，可通过DB_TYPE环境变量切换数据库类型
backend/tests/ — 单元测试与集成测试；测试用例 PDF 文件存放在backend/tests/test_data/
.claude/CLAUDE.md — 项目级开发者与 AI 助手协作规范（如需了解现有约定和文档格式要求，请优先阅读此文件）
修改核心功能时，请优先阅读以下文件：backend/app/services/pdf_parser.py、backend/app/services/ocr_engine.py，以及对应的测试文件：backend/tests/integration/test_full_pipeline.py 和 backend/tests/unit/*。
项目特定规范与注意事项 ⚠️
文件头部注释规范：许多文件要求添加标准化的头部注释段落（详见.claude/CLAUDE.md），新增文件时请保持格式统一。
测试输出存储：测试日志和中间输出文件将存储在测试专属目录中（详见test_*辅助函数）。部分测试用例会将输出结果写入test_results/ 或 backend/tests/output/目录。
OCR 引擎选择：PaddleOCR 模型初始化耗时较长（需下载约 1-2GB 文件）。在 macOS 系统中，测试用例通常使用 Apple Vision OCR 引擎以提升速度，示例代码见test_pdf_to_json.py：OCREngine(engine_type="vision")。
数据库初始化：通过init_database()完成数据库初始化；生产环境建议使用 Alembic 进行数据库迁移（本仓库暂未实现全自动化迁移流程）。
代码提交规范：提交 Pull Request（PR）时，请保持改动范围精简，所有功能变更需附带对应的测试用例，并更新 README 或相关文档。
PR 与自动化操作示例 👇
本地运行单个集成测试用例：
pytest backend/tests/integration/test_full_pipeline.py -q
初始化数据库（本地开发环境，使用 SQLite）：
python -c "from backend.database.config import init_database; init_database()"
本地开发时用 Vision 引擎替换 PaddleOCR（macOS 系统）：
在测试代码或脚本中添加：OCREngine(engine_type="vision")（详见test_pdf_to_json.py示例）。
何时需要咨询人工 / 提交问题工单 ❗
如需修改数据模型或数据库迁移策略：在实现前请先提交问题工单讨论。
如需引入重量级第三方模型或修改模型运行时下载逻辑。
如需变更.claude/CLAUDE.md中的协作规范或测试日志存储要求。
变更文档记录位置 ✍️
若变更影响 AI 助手行为或项目文档，请更新.claude/context/目录下的相关文件。
若新增基础设施或修改环境配置命令，请更新README_安装说明.txt，或在项目根目录添加README.md，简要记录开发环境快速搭建步骤。
AI 代理代码合并指南 🔁
保留维护者编写的原有内容，新增说明请添加在## 更新日志章节下，并标注日期和修改原因。
所有功能变更需添加最简测试用例和可复现的场景示例。