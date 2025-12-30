# ============================================================
# 文件: backend/app/config/__init__.py
# 功能: 应用配置管理
# 作者: 开发团队
# 创建时间: 2025-12-18
# 说明: 使用环境变量管理应用配置
# ============================================================

import os
from pathlib import Path


class Settings:
    """应用配置类.

    使用环境变量管理应用配置。
    """

    # ========== 基本信息 ==========
    APP_NAME: str = "Walmart PDF解析系统"
    APP_VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api/v1"

    # ========== 服务器配置 ==========
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True
    RELOAD: bool = True  # 开发模式自动重载

    # ========== 项目路径 ==========
    PROJECT_ROOT: Path = Path(__file__).parent.parent.parent.parent
    UPLOAD_DIR: Path = PROJECT_ROOT / "uploads"
    DATA_DIR: Path = PROJECT_ROOT / "backend" / "data"
    PDF_DATA_DIR: Path = PROJECT_ROOT / "PdfData"
    OUTPUT_DIR: Path = PROJECT_ROOT / "output"

    # ========== 数据库配置 ==========
    # 由database/config.py管理，此处仅声明
    DB_TYPE: str = os.getenv("DB_TYPE", "sqlite")

    # ========== PDF处理配置 ==========
    # PDF转图片DPI设置
    PDF_DPI: int = 300
    # 最大PDF文件大小（字节）
    MAX_PDF_SIZE: int = 50 * 1024 * 1024  # 50MB
    # 支持的文件扩展名
    ALLOWED_EXTENSIONS: set = {".pdf"}

    # ========== OCR配置 ==========
    # OCR引擎类型
    OCR_ENGINE: str = "vision"  # 可选: paddleocr, vision
    # OCR语言
    OCR_LANG: str = "ch"  # 中文

    # ========== 日志配置 ==========
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # ========== 安全配置 ==========
    # CORS允许的源（生产环境应限制）
    CORS_ORIGINS: list = ["*"]
    # 是否允许凭证
    CORS_ALLOW_CREDENTIALS: bool = True

    # ========== 功能开关 ==========
    # 是否启用文件上传
    ENABLE_FILE_UPLOAD: bool = True
    # 是否启用批量处理
    ENABLE_BATCH_PROCESSING: bool = True
    # 是否启用数据导出
    ENABLE_DATA_EXPORT: bool = True

    def __init__(self):
        """初始化配置并创建必要的目录."""
        # 确保必要目录存在
        self.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        self.DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# 创建全局配置实例
settings = Settings()

__all__ = ['settings', 'Settings']
