#!/bin/bash
# 使用系统Python运行，以便访问Vision框架

cd "$(dirname "$0")/.."

echo "========================================"
echo "启动 PDF 调试流程（使用 Vision OCR）"
echo "========================================"
echo ""

# 检查是否在macOS系统
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo "❌ 错误：Vision OCR仅支持 macOS 系统"
    exit 1
fi

# 使用系统Python而非虚拟环境，以便访问Vision框架
SYSTEM_PYTHON="/usr/bin/python3"

if [ ! -f "$SYSTEM_PYTHON" ]; then
    echo "❌ 错误：未找到系统Python ($SYSTEM_PYTHON)"
    exit 1
fi

echo "✓ 使用系统Python: $SYSTEM_PYTHON"
echo "✓ Python版本: $($SYSTEM_PYTHON --version)"
echo ""

# 设置环境变量
export OCR_ENGINE=vision
export PYTHONPATH="$(pwd):$PYTHONPATH"

# 运行脚本并输出到文件
echo "开始执行..."
echo ""

$SYSTEM_PYTHON scripts/test_debug_flow.py 2>&1 | tee backend/tests/output/test_debug_flow.log

exit_code=${PIPESTATUS[0]}

echo ""
echo "========================================"
if [ $exit_code -eq 0 ]; then
    echo "✅ 调试完成"
else
    echo "❌ 调试失败（退出码: $exit_code）"
fi
echo "========================================"

exit $exit_code
