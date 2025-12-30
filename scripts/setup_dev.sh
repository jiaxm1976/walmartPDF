#!/bin/bash
set -e
# 简单开发环境初始化脚本：创建 .venv 并安装依赖
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
PYTHON=${PYTHON:-python}

echo "创建并激活 .venv（Python 可通过环境变量 PYTHON 指定）..."
$PYTHON -m venv "$PROJECT_ROOT/.venv"
source "$PROJECT_ROOT/.venv/bin/activate"

echo "安装依赖..."
pip install --upgrade pip
pip install -r "$PROJECT_ROOT/requirements.txt"

echo "开发环境搭建完成。要激活： source .venv/bin/activate"
