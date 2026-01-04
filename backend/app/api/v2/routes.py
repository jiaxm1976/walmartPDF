"""
简单的 API v2 路由实现（供初学者阅读）。

文件说明：
- 使用 FastAPI 的 `APIRouter` 组织 v2 版本的端点。
- 提供了两个示例端点：
  1. `GET /api/v2/health`：基础健康检查，返回服务状态；
  2. `POST /api/v2/import`：演示如何同步调用解析器并将数据写入数据库（简化流程）。

注意：本实现为最小可运行示例，真实生产代码中会考虑异步、鉴权、更严格的输入校验、幂等及错误处理。
"""

from fastapi import APIRouter, Depends
from typing import Dict, Any

# 导入请求/响应的 Pydantic 模型（用于自动校验与文档）
from .schemas import ImportRequest, ImportResponse
# 导入我们实现的认证依赖（见 dependencies.py）
from .dependencies import get_current_user

# 解析器与导入器：项目中已有的功能模块，路由调用它们组成完整流程
from backend.app.services.pdf_parser import parse_pdf_file
from backend.database.structured_importer import StructuredDataImporter
from backend.app.schemas.v2 import JGData, ImportResult
from backend.database.config import get_db
from backend.database import models
from .schemas import StatementSummary, StatementsListResponse
from sqlalchemy.orm import Session
from typing import Optional
from fastapi import HTTPException
from backend.app.services.pdf_parser_service import PDFParserService
from backend.app.schemas.v2 import ParseResult


router = APIRouter()


@router.get("/health", tags=["Health"])
async def v2_health_check():
    """健康检查端点（示例）

    - 返回一个简单的 JSON，用于确认 API 正常运行。
    - `tags` 用于 OpenAPI/Swagger 文档分组。
    """
    return {"status": "ok", "version": "v2"}



@router.post(
    "/import",
    response_model=ImportResult,
    tags=["Import"],
    responses={
        200: {
            "content": {
                "application/json": {
                    "example": {"success": True, "statement_id": 123, "message": "imported"}
                }
            }
        }
    },
)
def import_pdf(request: ImportRequest, user: Dict[str, Any] = Depends(get_current_user)):
    """同步导入示例端点（最小实现，便于初学者理解）

    流程说明：
    1. 接收 `ImportRequest`（由 Pydantic 校验 `pdf_path` 字段）；
    2. 使用 `parse_pdf_file()` 将 PDF 解析为结构化字典；
    3. 将解析结果封装为 `jg_structured_data`（结构化导入器期望的格式）；
    4. 使用 `StructuredDataImporter` 将数据写入本地 SQLite（或配置的 DB）；
    5. 返回 `ImportResponse`，包含导入的 `statement_id` 或错误信息。

    参数说明（简化）：
    - `request`: 已经被 FastAPI 转换为 `ImportRequest` 的对象，可通过 `request.pdf_path` 访问。
    - `user`: 通过 `Depends(get_current_user)` 注入的当前用户信息（用于权限检查），此处仅示例使用。
    """

    # ----------------
    # 1. 基本输入校验
    # ----------------
    pdf_path = request.pdf_path
    if not pdf_path:
        # 使用 Pydantic 模型作为响应模板，保持 API 文档一致性
        return ImportResponse(success=False, message="pdf_path required", result=None)

    # ----------------
    # 2. 调用解析器
    # ----------------
    try:
        parsed = parse_pdf_file(pdf_path)
    except Exception as e:
        # 解析失败时返回错误信息（真实场景可记录日志并返回更多上下文）
        return ImportResult(success=False, statement_id=None, message=f"parse error: {e}")

    # ----------------
    # 3. 将解析结果转换为导入器期望的结构（示例）
    # ----------------
    sections = {}
    header = []
    period = None
    if parsed.get('period_start') or parsed.get('period_end'):
        period = f"{parsed.get('period_start')} - {parsed.get('period_end')}"
        header.append({'field': '统计区间', 'value': period})

    if parsed.get('payment_to_you'):
        header.append({'field': '向您支付的金额', 'value': parsed.get('payment_to_you')})

    sections['header'] = header

    # 将完整解析字典打平成 field/value 列表，方便导入器示例处理
    parsed_items = []
    for k, v in parsed.items():
        parsed_items.append({'field': str(k), 'value': v})
    sections['parsed'] = parsed_items

    jg_structured_data = {'sections': sections, 'metadata': {'source': 'api_v2_import'}}

    # ----------------
    # 4. 同步写入数据库（演示）
    # ----------------
    importer = StructuredDataImporter()
    try:
        importer.connect()
        # 尝试先用 JGData 验证并使用 import_from_model
        try:
            jg_model = JGData.model_validate(jg_structured_data)
            import_res: ImportResult = importer.import_from_model(parsed.get('file_name', 'unknown.pdf'), jg_model)
        except Exception:
            # 验证失败，回退到原始导入方法
            statement_id = importer.import_jg_data(parsed.get('file_name', 'unknown.pdf'), jg_structured_data)
            import_res = ImportResult(success=bool(statement_id), statement_id=statement_id, message="imported" if statement_id else "import failed")
    finally:
        importer.disconnect()

    return import_res



@router.post(
    "/parse",
    response_model=ParseResult,
    tags=["Parse"],
    responses={
        200: {
            "content": {
                "application/json": {
                    "example": {
                        "status": "SUCCESS",
                        "success": True,
                        "data": {
                            "sections": {
                                "header": [{"field": "统计区间", "value": "2025-12-01 - 2025-12-31"}],
                                "right_section": [{"field": "待付款金额", "value": "$1,234.56", "raw": "$1,234.56"}]
                            },
                            "metadata": {"source": "parser"}
                        },
                        "right_section_raw": {"待付款金额": "$1,234.56"},
                        "error": None,
                        "process_time": 0.45
                    }
                }
            }
        }
    },
)
def parse_pdf_endpoint(request: ImportRequest, user: Dict[str, Any] = Depends(get_current_user)):
    """直接解析 PDF 并返回解析结果（ParseResult）。

    用途：调试和前端预览解析结果，随后可调用 /import 将数据写入数据库。
    """
    parser = PDFParserService()
    result = parser.parse_pdf_direct(request.pdf_path, output_dir=request.output_dir)
    try:
        parsed = ParseResult.model_validate(result)
        return parsed
    except Exception as e:
        # 验证失败时返回错误结构，避免抛出 500
        return ParseResult.model_validate({
            "status": "ERROR",
            "success": False,
            "data": None,
            "right_section_raw": {},
            "error": f"validation error: {e}",
            "process_time": result.get("process_time") if isinstance(result, dict) else None,
        })


@router.get("/statements", response_model=StatementsListResponse, tags=["Statements"])
def list_statements(
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(get_db),
    user: Dict[str, Any] = Depends(get_current_user),
):
    """
    列出对账单（分页）。

    逐行注释说明（中文，便于初学者理解）：

    1) 函数签名部分
    - `limit`/`offset`：用于简单分页，默认每页 20 条，从偏移 0 开始。
    - `db`：通过 FastAPI 的 `Depends(get_db)` 获取数据库会话（SQLAlchemy Session）。
    - `user`：通过鉴权依赖 `get_current_user` 注入的当前用户信息（用于权限控制或审计）。

    2) 查询实现（示例，使用 SQLAlchemy ORM）
    - 我们查询 `Statement` 表并按 `created_at` 降序排列，便于展示最近导入的对账单。
    """

    # ------- 查询总数（用于分页元数据）
    # 使用简单 SQLAlchemy 查询获取 statements 表的总记录数
    total = 0
    try:
        # 查询计数：db.query(models.Statement).count()
        total = db.query(models.Statement).count()
    except Exception:
        # 如果数据库不可用或查询失败，返回一个友好的响应
        return StatementsListResponse(success=False, message="无法读取数据库", total=None, items=[])

    # ------- 拉取当前页数据
    # 使用 limit/offset 控制分页。按 created_at 倒序展示最新记录。
    stmt_rows = db.query(models.Statement).order_by(models.Statement.created_at.desc()).limit(limit).offset(offset).all()

    # ------- 将 ORM 对象转换为 Pydantic 模型列表
    items = []
    for s in stmt_rows:
        # 每一项都取出需要对外展示的字段
        summary = StatementSummary(
            id=s.id,
            pdf_name=s.pdf_name,
            statement_period=s.statement_period,
            payment_to_you=s.payment_to_you,
        )
        items.append(summary)

    # ------- 返回统一响应
    return StatementsListResponse(success=True, message="ok", total=total, items=items)


@router.get("/statements/{statement_id}", response_model=Optional[dict], tags=["Statements"])
def get_statement_detail(
    statement_id: int,
    db: Session = Depends(get_db),
    user: Dict[str, Any] = Depends(get_current_user),
):
    """
    获取单条对账单的完整详情（示例实现，中文逐行注释）

    说明：
    - 我们优先使用 `get_complete_statement_data`（位于 `backend.app.crud.pdf_file`）
      该函数封装了从多个表读取完整对账单数据的逻辑，返回字典结构。
    - 返回格式为一个字典，包含 header、sales、refund 等板块信息，或在找不到时返回 404。
    """

    # 直接使用 SQLAlchemy ORM 查询 Statement 和对应的 SectionData，避免依赖复杂的 CRUD 导入链。
    try:
        # 查询主表记录
        stmt = db.query(models.Statement).filter(models.Statement.id == statement_id).first()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"数据库查询失败: {e}")

    if not stmt:
        raise HTTPException(status_code=404, detail="statement not found")

    # 查询所有板块数据并构建字典 {section_name: parsed_json}
    try:
        section_rows = db.query(models.SectionData).filter(models.SectionData.statement_id == statement_id).all()
        sections = {}
        for row in section_rows:
            # SectionData.data 存储为 JSON 字符串（models 定义为 Text），尝试解析为 dict
            try:
                import json
                sections[row.section_name] = json.loads(row.data)
            except Exception:
                # 如果解析失败，直接返回原始字符串
                sections[row.section_name] = row.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"读取板块数据失败: {e}")

    # 组装返回结构
    item = {
        'id': stmt.id,
        'pdf_name': stmt.pdf_name,
        'statement_period': stmt.statement_period,
        'payment_to_you': stmt.payment_to_you,
        'sections': sections,
    }

    return {"success": True, "message": "ok", "item": item}
