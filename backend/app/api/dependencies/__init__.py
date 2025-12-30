# ============================================================
# 文件: backend/app/api/dependencies/__init__.py
# 功能: FastAPI依赖注入模块
# ============================================================

from database.config import get_db

__all__ = ["get_db"]
