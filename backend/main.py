#!/usr/bin/env python3
# ============================================================
# 文件: backend/main.py
# 功能: FastAPI主应用入口
# 作者: 开发团队
# 创建时间: 2025-12-18
# 说明: Walmart PDF解析系统 - Web API服务
# ============================================================

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

# 注意：自 2026-01-06 起，不再使用 backend.database.config.init_database()
# 请使用标准脚本初始化数据库：python scripts/init_database_v2.py

try:
    # 优先尝试以包名方式导入（通过 `import backend.main` 时生效）
    from backend.app.api.v2 import api_router as api_v2_router
except Exception:
    try:
        # 回退到原始的相对运行时导入方式（通过直接运行 main.py 时生效）
        from app.api.v2 import api_router as api_v2_router
    except Exception:
        api_v2_router = None

# 导入导出路由
try:
    from backend.app.routes.export_router import router as export_router
except Exception:
    try:
        from app.routes.export_router import router as export_router
    except Exception:
        export_router = None

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(
    title="Walmart PDF解析系统",
    description="自动化处理沃尔玛市场财务对账单的PDF报表识别和数据分析系统",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# 配置CORS（跨域资源共享）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """应用启动时执行的操作."""
    logger.info("=" * 60)
    logger.info("启动Walmart PDF解析系统API服务")
    logger.info("=" * 60)
    
    # 注意：数据库初始化不再在此进行
    # 请提前运行：python scripts/init_database_v2.py
    logger.info("✓ 应用启动成功")
    logger.info("📚 API文档: http://localhost:8000/api/docs")
    logger.info("⚠️  初次使用请运行：python scripts/init_database_v2.py")


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时执行的操作."""
    logger.info("关闭Walmart PDF解析系统API服务")


@app.get("/", tags=["Root"])
async def root():
    """根路径 - API健康检查."""
    return {
        "service": "Walmart PDF解析系统",
        "status": "running",
        "version": "1.0.0",
        "docs": "/api/docs"
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """健康检查接口."""
    return {
        "status": "healthy",
        "service": "walmart-pdf-parser"
    }


# 注册API路由
if api_v2_router is not None:
    # 挂载 /api/v2 路由（若 v2 已就位）
    app.include_router(api_v2_router, prefix="/api/v2")

# 注册导出路由
if export_router is not None:
    app.include_router(export_router)


if __name__ == "__main__":
    import uvicorn

    # 开发环境运行配置
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # 开发模式：代码变更自动重载
        log_level="info"
    )


# ============================================================
# END OF main.py
# ============================================================
