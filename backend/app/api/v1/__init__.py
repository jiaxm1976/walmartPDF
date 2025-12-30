# ============================================================
# 文件: backend/app/api/v1/__init__.py
# 功能: API v1路由汇总
# ============================================================

from fastapi import APIRouter
from app.api.v1 import pdfs, statements, analytics

# 创建v1版本的主路由
api_router = APIRouter()

# 注册各个模块的路由
api_router.include_router(
    pdfs.router,
    prefix="/pdfs",
    tags=["PDFs - PDF文件管理"]
)

api_router.include_router(
    statements.router,
    prefix="/statements",
    tags=["Statements - 对账单数据"]
)

api_router.include_router(
    analytics.router,
    prefix="/analytics",
    tags=["Analytics - 数据分析"]
)

# 健康检查接口
@api_router.get("/health", tags=["Health"])
async def v1_health():
    """API v1健康检查."""
    return {
        "status": "ok",
        "version": "v1",
        "endpoints": {
            "pdfs": "/api/v1/pdfs",
            "statements": "/api/v1/statements",
            "analytics": "/api/v1/analytics"
        }
    }
