#!/bin/bash
# ============================================================
# 文件: scripts/run_api.sh
# 功能: 启动FastAPI服务
# 使用: ./scripts/run_api.sh
# ============================================================

# 获取项目根目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# 优先使用 .venv；若不存在则回退到 legacy venv（venv）
if [ -f "$PROJECT_ROOT/.venv/bin/activate" ]; then
    echo "Activating .venv"
    source "$PROJECT_ROOT/.venv/bin/activate"
elif [ -f "$PROJECT_ROOT/venv/bin/activate" ]; then
    echo "⚠️ Legacy venv detected. Activating venv; please consider migrating to .venv"
    source "$PROJECT_ROOT/venv/bin/activate"
else
    echo "虚拟环境未找到。请运行: python -m venv .venv && source .venv/bin/activate"
    exit 1
fi

# 进入backend目录
cd "$PROJECT_ROOT/backend"

# 启动服务
echo "=========================================="
echo "启动Walmart PDF解析系统API服务"
echo "=========================================="
echo "API文档: http://localhost:8000/api/docs"
echo "健康检查: http://localhost:8000/health"
echo "=========================================="
echo ""

# 使用uvicorn启动（开发模式，支持热重载）
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# ============================================================
# END OF run_api.sh
# ============================================================
