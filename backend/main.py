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

from database.config import init_database
from app.api.v1 import api_router

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

    # 初始化数据库
    try:
        init_database()
        logger.info("✓ 数据库连接成功")
    except Exception as e:
        logger.error(f"❌ 数据库初始化失败: {e}")
        raise


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
app.include_router(api_router, prefix="/api/v1")


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
