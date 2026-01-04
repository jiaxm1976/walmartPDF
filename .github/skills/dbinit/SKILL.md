# ---
# name: dbinit
# title: "dbinit — 数据库初始化 Skill"
# ---

# dbinit — 数据库初始化 Skill

简述
- 名称：dbinit
- 目标：在本地开发环境中安全、可重复地初始化 V2 数据库（备份 → 删除旧 DB → 应用 V2 schema → 初始化右侧字段 → 验证）。

触发方式
- 本地在开发者机器或受控 CI 环境中执行（需人工确认或管理员批准）。

能力：初始化数据库（破坏性）
- 描述：运行 `scripts/init_database_v2.py`，对 `backend/data/walmart_pdf_parser.db` 进行备份并重建 V2 schema，初始化右侧字段并进行 schema 验证。
- 实现/引用：脚本实现位于 [scripts/init_database_v2.py](scripts/init_database_v2.py)。
- 安全标签：危险（会删除/重建本地数据库）。默认不在生产或主分支自动执行。

运行命令（示例，使用项目虚拟环境解释器）
```bash
.venv/bin/python scripts/init_database_v2.py        # 直接执行（脚本当前无 simulate/force 参数）
# 建议先在 dry-run/模拟模式运行（若脚本增加了 --simulate 支持）：
.venv/bin/python scripts/init_database_v2.py --simulate
```

推荐的环境准备
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
```

建议参数与安全控制（Skill 层面约定）
- `--simulate`：干运行，打印将执行的操作但不写入（Skill 建议默认启用 dry-run）。
- `--force`：跳过交互确认直接执行破坏性操作（必须显式提供）。
- `--backup-dir <path>`：指定备份目录，默认 `backend/data/backups/`。
- `--confirm-admin`：由管理员确认（在自动化环境中可以用管理员令牌或 PR 批准替代交互）。

Smoke-test（验证点示例）
- 文件与备份检查：
```bash
.venv/bin/python scripts/init_database_v2.py --simulate
# 执行后（实际运行），检查退出码与备份文件：
echo $?  # 期望 0
ls backend/data/backups | tail -n 5
```
- SQL 断言（示例）：
```bash
sqlite3 backend/data/walmart_pdf_parser.db "SELECT name FROM sqlite_master WHERE type='table' AND name='field_frequency';"
sqlite3 backend/data/walmart_pdf_parser.db "SELECT COUNT(*) FROM field_frequency;"
# 期望返回表存在且记录数等于脚本日志中给出的期望值（常见示例：40）
```

回滚示例
```bash
cp backend/data/backups/walmart_pdf_parser_YYYYMMDD_HHMMSS.db backend/data/walmart_pdf_parser.db
```

CI 与运行限制
- 在 CI 中仅允许非破坏性运行（`--simulate`）。
- 任何在受控环境中执行真实初始化的步骤需通过 PR 审批并由维护者或管理员触发。

参考文件
- 初始化脚本： [scripts/init_database_v2.py](scripts/init_database_v2.py)
- 默认 DB： [backend/data/walmart_pdf_parser.db](backend/data/walmart_pdf_parser.db)
- 备份目录示例： `backend/data/backups/`
- 相关测试参考： [backend/tests/integration/test_full_pipeline.py](backend/tests/integration/test_full_pipeline.py)

维护与贡献建议
- 变更 Skill 或 init 脚本时：先在 `backend/tests` 添加复现用例并在本地运行 smoke-test。
- 将破坏性脚本改为支持 `--simulate` 与 `--backup-dir` 后再在 Skill 中标注为可运行。
