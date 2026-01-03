
# Walmart-a 开发助手（Skill）

简述
- 名称：Walmart-a 开发助手
- 目标：帮助工程师快速理解、调试、测试和扩展本项目（后端 PDF/OCR 解析 + 前端 React），并提供常见操作的示例命令与安全注意事项。

触发方式
- 在代码审查或 Issue/PR 评论中请求具体操作建议（示例提示见“使用示例”）。
- 本地使用时，通过复制/粘贴提示到本地 AI 工具或命令窗口获取建议。
- 可集成于 CI 注释机器人或开发者聊天助手（需额外授权与 CI 集成配置）。

能力（Skills）
- 项目导航
	- 解释仓库结构与关键模块，指引到核心文件如：后端入口与服务实现（参见下方参考文件）。
- 快速复现与运行指南
	- 提供创建虚拟环境、安装依赖、启动后端/前端的逐步命令。
- 常见任务模板
	- 添加新解析规则（PDF 解析、OCR 后处理）
	- 编写或更新单元/集成测试
	- 调试 OCR/解析流水线并定位失败样例
- 代码更改建议
	- 给出最小可行改动、示例补丁片段与关联测试建议
- 测试与 CI 辅助
	- 生成本地复现命令，建议的测试组合（单元/集成/快速 smoke test）
- 文档与发布说明
	- 撰写变更日志、README 更新、迁移说明模板
- 安全与性能提示
	- 提醒关于大型模型下载、数据库初始化与敏感信息（如生产 DB）操作的注意事项

范围与限制
- 不会直接访问或更改生产系统；所有运行/写入步骤需人工批准或在 CI/受控环境中执行。
- 不提供或嵌入受版权保护的大段外部文档；会给出引用和摘要。
- 不会自动下载/提交大型模型文件到仓库（例如 PaddleOCR 模型），会给出替代方案与提示。

使用示例（提示模板）
- “帮我在项目中定位 PDF 解析流程的入口文件并说明各模块职责。”
- “根据 test_pdf_to_database.py 的失败输出，给出可能的修复方向并提供最小补丁。”
- “如何在 macOS 上使用 Vision 引擎替代 PaddleOCR 来加速测试？列出需要修改的测试或示例用法。”
- “为新增字段 X 到解析结果添加数据库字段与导入流程，给出迁移示例和测试用例模板。”

常用命令（本地开发）
- 创建并激活虚拟环境（macOS/Linux）：
	```bash
	python -m venv .venv
	source .venv/bin/activate
	pip install -r backend/requirements.txt
	```
- 启动后端（开发、热重载）：
	```bash
	uvicorn backend.main:app --reload --port 8000
	```
	或
	```bash
	python backend/main.py
	```
- 运行后端测试（全部或单个）：
	```bash
	pytest backend/tests -q
	pytest backend/tests/unit/test_pdf_parser.py -q
	```
- 启动前端（开发）：
	```bash
	cd frontend
	npm install
	npm start
	```

测试与验证策略
- 提交功能更改前，务必添加或更新对应的单元/集成测试：位置参见 `backend/tests/`。
- 推荐在 macOS 上的快速流程使用 Vision OCR（见示例 test_pdf_to_json.py），避免在 CI 中触发大型模型下载。
- 本地验证步骤：初始化数据库 -> 运行目标测试 -> 手动检查 `backend/tests/output/` 或 `test_results/` 生成的工件。

参考文件（快速跳转）
- 后端启动与 API： [backend/main.py](backend/main.py)
- PDF 解析核心： [backend/app/services/pdf_parser.py](backend/app/services/pdf_parser.py)
- OCR 引擎实现： [backend/app/services/ocr_engine.py](backend/app/services/ocr_engine.py)
- 测试目录： [backend/tests](backend/tests)
- 常用脚本： [scripts](scripts)

维护与贡献建议
- 修改解析逻辑或数据模型时：先在 `backend/tests` 添加复现用例，再实现最小改动并确保测试通过。
- 新增大型依赖或修改模型下载逻辑：先开 issue 讨论，并在 PR 中明确回退/缓存方案。
- 文档随改动同步更新：README、README_安装说明.txt 或 .clause/context 相关文件。

安全与隐私
- 避免将模型权重、虚拟环境、或敏感数据库凭证提交到仓库。
- 在共享 PDF 或测试样例时注意脱敏（含 PII 的扫描件）。

维护者联系人
- 默认联系人/审核人：项目维护者列表（请参阅仓库根目录 README 或团队管理系统以获取具体人员）。

