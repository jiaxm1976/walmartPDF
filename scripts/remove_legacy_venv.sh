#!/bin/bash
set -e
# 清理 legacy `venv` 目录（本脚本会删除项目根下的 venv 目录）
# 使用前请确保你不再需要该虚拟环境或已备份相关配置

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

if [ -d "$PROJECT_ROOT/venv" ]; then
    echo "检测到 legacy venv: $PROJECT_ROOT/venv"
    read -p "是否确认删除该目录？(y/N): " confirm
    if [[ "$confirm" =~ ^[Yy]$ ]]; then
        rm -rf "$PROJECT_ROOT/venv"
        echo "已删除 $PROJECT_ROOT/venv"
    else
        echo "已取消删除"
    fi
else
    echo "未发现 legacy venv（$PROJECT_ROOT/venv 不存在）"
fi
