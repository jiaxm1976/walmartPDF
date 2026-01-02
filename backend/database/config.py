# ============================================================
# 文件: backend/database/config.py
# 功能: 数据库配置（支持SQLite/MySQL/PostgreSQL）
# 作者: 开发团队
# 创建时间: 2025-12-18
# ============================================================

import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


# ============================================================
# 数据库配置
# ============================================================

# 数据库类型：'sqlite', 'mysql', 'postgresql'
DB_TYPE = os.getenv("DB_TYPE", "sqlite")

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent.parent

# SQLite配置
SQLITE_DB_PATH = PROJECT_ROOT / "backend" / "data" / "walmart_pdf_parser.db"

# MySQL配置（从环境变量读取）
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "walmart_pdf_parser")

# PostgreSQL配置（从环境变量读取）
PG_HOST = os.getenv("PG_HOST", "localhost")
PG_PORT = int(os.getenv("PG_PORT", "5432"))
PG_USER = os.getenv("PG_USER", "postgres")
PG_PASSWORD = os.getenv("PG_PASSWORD", "")
PG_DATABASE = os.getenv("PG_DATABASE", "walmart_pdf_parser")


def get_database_url() -> str:
    """获取数据库连接URL.

    根据DB_TYPE环境变量选择数据库类型。

    Returns:
        str: 数据库连接URL

    支持的数据库:
        - SQLite: sqlite:///path/to/database.db
        - MySQL: mysql+pymysql://user:password@host:port/database
        - PostgreSQL: postgresql://user:password@host:port/database
    """
    if DB_TYPE == "mysql":
        return (
            f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}"
            f"@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}"
            f"?charset=utf8mb4"
        )
    elif DB_TYPE == "postgresql":
        return (
            f"postgresql://{PG_USER}:{PG_PASSWORD}"
            f"@{PG_HOST}:{PG_PORT}/{PG_DATABASE}"
        )
    else:  # 默认使用SQLite
        return f"sqlite:///{SQLITE_DB_PATH}"


# 创建数据库引擎
engine = create_engine(
    get_database_url(),
    pool_pre_ping=True,  # 连接前检查有效性
    echo=False,  # 设置为True可以看到SQL语句
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建ORM基类
Base = declarative_base()


def get_db():
    """获取数据库会话（用于FastAPI依赖注入）.

    自动管理数据库会话的生命周期。

    Yields:
        Session: 数据库会话对象

    Example:
        ```python
        from fastapi import Depends
        from database.config import get_db

        @app.get("/statements")
        def get_statements(db: Session = Depends(get_db)):
            return db.query(PDFFile).all()
        ```
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_database():
    """初始化数据库（创建所有表）.

    注意：生产环境建议使用Alembic进行数据库迁移。
    """
    # 导入所有模型（确保模型被注册）
    from backend.database import models  # noqa
    Base.metadata.create_all(bind=engine)
    print(f"✓ 数据库初始化完成 ({DB_TYPE})")
    print(f"✓ 数据库URL: {get_database_url()}")


# ============================================================
# END OF config.py
# ============================================================
