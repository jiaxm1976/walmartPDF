# ============================================================
# 文件: backend/app/crud/__init__.py
# 功能: CRUD操作模块
# ============================================================

"""
CRUD 包初始化——修正导入以使用相对导入，避免在测试或运行时出现 `ModuleNotFoundError: No module named 'app'`。

历史原因：之前使用 `from app.crud import pdf_file`，在非顶级 package 环境下会失败。
现在改为相对导入以保证在模块被作为包导入时行为稳定。
"""

from . import pdf_file

__all__ = ["pdf_file"]
