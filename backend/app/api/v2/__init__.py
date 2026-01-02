# ============================================================
# 文件: backend/app/api/v2/__init__.py
# 功能: API v2 路由汇总（骨架）
# ============================================================
from fastapi import APIRouter
from .routes import router

# 对外暴露用于主入口挂载的 router
api_router = APIRouter()
api_router.include_router(router, prefix="")
