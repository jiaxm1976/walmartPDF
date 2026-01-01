# PR: Use .venv for dev environment, docs update, add setup/cleanup scripts

## 概要
- 将项目文档中关于虚拟环境的推荐从 `venv` 切换为 `.venv`，并在 README 中添加说明（兼容 legacy `venv`）。
- 更新 `scripts/run_api.sh`：优先激活 `.venv`，若不存在则回退到 `venv` 并打印提示。
- 新增 `scripts/setup_dev.sh`（便捷一键创建 `.venv` 并安装依赖）。
- 新增 `scripts/remove_legacy_venv.sh`（交互式删除本地 legacy `venv`，需手动确认）。

## 改动文件
- 修改: `README_安装说明.txt`, `scripts/run_api.sh`, `.github/copilot-instructions.md`, `.claude/CLAUDE.md`, `todo.md`
- 新增: `scripts/setup_dev.sh`, `scripts/remove_legacy_venv.sh`

## 迁移与使用说明
1. 推荐在开发机中执行：
   ```bash
   ./scripts/setup_dev.sh
   source .venv/bin/activate
   ```
2. 若本地还存在 legacy `venv`，可运行：
   ```bash
   ./scripts/remove_legacy_venv.sh
   ```
   本脚本会要求交互确认以避免误删。

## 测试要点
- 在无 `.venv` 且无 `venv` 的环境下运行 `scripts/run_api.sh` 应报错并提示创建 `.venv`。
- 在存在 `.venv` 时，`scripts/run_api.sh` 应激活 `.venv` 并启动服务。
- 在存在 legacy `venv` 且无 `.venv` 的环境下，`scripts/run_api.sh` 应回退并激活 `venv`，但给出迁移建议。

## 风险/注意
- 本 PR 不删除本地 `venv`，仅新增清理脚本供用户确认执行。删除操作需要用户主动确认（交互式）。

---

请检查文档用语与本地脚本行为是否符合团队的偏好，再合并。