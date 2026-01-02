# ============================================================
# 文件: backend/app/api/v1/pdfs.py
# 功能: PDF上传和管理API路由
# 作者: 开发团队
# 创建时间: 2025-12-18
# ============================================================

import os
import hashlib
import logging
from pathlib import Path
from typing import Optional, List
from datetime import datetime

from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, status, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from database.config import get_db
from app.config import settings
from app.schemas import pdf_file as schemas
from app.crud import pdf_file as crud

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================
# 辅助函数
# ============================================================

def calculate_file_hash(file_path: str) -> str:
    """计算文件的SHA256哈希值.

    Args:
        file_path: 文件路径

    Returns:
        str: SHA256哈希值
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        # 分块读取文件，避免大文件占用过多内存
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def save_upload_file(upload_file: UploadFile, destination: Path) -> int:
    """保存上传的文件.

    Args:
        upload_file: 上传的文件对象
        destination: 目标路径

    Returns:
        int: 文件大小（字节）
    """
    try:
        # 确保目标目录存在
        destination.parent.mkdir(parents=True, exist_ok=True)

        # 保存文件
        file_size = 0
        with destination.open("wb") as buffer:
            while chunk := upload_file.file.read(8192):
                buffer.write(chunk)
                file_size += len(chunk)

        return file_size
    except Exception as e:
        logger.error(f"保存文件失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"保存文件失败: {str(e)}"
        )


# ============================================================
# 1. PDF上传接口
# ============================================================

@router.post("/upload", response_model=schemas.PDFFileResponse, status_code=status.HTTP_201_CREATED)
async def upload_pdf(
    file: UploadFile = File(..., description="PDF文件"),
    db: Session = Depends(get_db)
):
    """上传PDF文件.

    功能:
    - 接收PDF文件上传
    - 验证文件类型和大小
    - 计算文件哈希
    - 保存文件并创建数据库记录
    - 自动触发PDF解析（异步）

    Args:
        file: 上传的PDF文件
        db: 数据库会话

    Returns:
        PDFFileResponse: 创建的PDF文件信息

    Raises:
        HTTPException: 文件类型不正确、文件过大等错误
    """
    logger.info(f"接收到PDF上传请求: {file.filename}")

    # 1. 验证文件扩展名
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不支持的文件类型: {file_ext}，仅支持: {', '.join(settings.ALLOWED_EXTENSIONS)}"
        )

    # 2. 生成唯一文件名（时间戳 + 原始文件名）
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_filename = f"{timestamp}_{file.filename}"
    file_path = settings.UPLOAD_DIR / safe_filename

    # 3. 保存文件
    try:
        file_size = save_upload_file(file, file_path)
        logger.info(f"文件保存成功: {file_path}, 大小: {file_size} bytes")
    except Exception as e:
        logger.error(f"文件保存失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"文件保存失败: {str(e)}"
        )

    # 4. 验证文件大小
    if file_size > settings.MAX_PDF_SIZE:
        # 删除已保存的文件
        file_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"文件过大: {file_size / 1024 / 1024:.2f}MB，最大限制: {settings.MAX_PDF_SIZE / 1024 / 1024}MB"
        )

    # 5. 计算文件哈希
    try:
        file_hash = calculate_file_hash(str(file_path))
        logger.info(f"文件哈希: {file_hash}")
    except Exception as e:
        logger.error(f"计算文件哈希失败: {e}")
        file_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"计算文件哈希失败: {str(e)}"
        )

    # 6. 检查文件是否已经导入
    existing_pdf = crud.get_pdf_file_by_hash(db, file_hash)
    if existing_pdf:
        logger.warning(f"文件已存在: {file_path}, hash={file_hash}")
        file_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="文件已导入，请勿重复上传"
        )

    # 7. 创建数据库记录
    try:
        pdf_data = schemas.PDFFileCreate(
            filename=safe_filename,
            original_filename=file.filename,
            file_path=str(file_path),
            file_size=file_size,
            file_hash=file_hash
        )
        db_pdf = crud.create_pdf_file(db, pdf_data)
        logger.info(f"PDF文件记录创建成功: id={db_pdf.id}")

        # 7. 自动触发PDF解析（异步）
        try:
            logger.info(f"自动触发PDF解析: id={db_pdf.id}")
            from app.services.pdf_parser_service import PDFParserService
            from app.config import settings as app_settings
            
            parser = PDFParserService(dpi=app_settings.PDF_DPI)
            result = parser.parse_pdf(str(file_path))

            if not result["success"]:
                # 解析失败
                error_msg = result["error"]
                crud.update_pdf_file_status(db, db_pdf.id, "failed", error_msg)
                logger.error(f"PDF解析失败: id={db_pdf.id}, error={error_msg}")
            else:
                # 解析成功，转换并保存数据
                parsed_data = result["data"]
                db_format_data, validation_results = parser.convert_to_database_format(parsed_data)
                
                # 保存到数据库
                crud.save_parsed_data_to_db(db, db_pdf.id, db_format_data)

                # 检查校验结果
                has_validation_errors = any(not result["valid"] for result in validation_results)
                
                if has_validation_errors:
                    # 有校验错误，保存校验问题并更新状态
                    import json
                    validation_issues_json = json.dumps(validation_results)
                    db_pdf.validation_issues = validation_issues_json
                    db_pdf = crud.update_pdf_file_status(db, db_pdf.id, "failed", "数据不完整，需要人工检查")
                    db_pdf.process_time = datetime.now()
                    db.commit()
                    logger.warning(f"⚠️ PDF解析完成但有校验错误: id={db_pdf.id}, 耗时={result['process_time']:.2f}秒")
                else:
                    # 校验通过，更新状态为success
                    db_pdf = crud.update_pdf_file_status(db, db_pdf.id, "success")
                    db_pdf.process_time = datetime.now()
                    db.commit()
                    logger.info(f"✅ PDF自动解析完成: id={db_pdf.id}, 耗时={result['process_time']:.2f}秒")
        except Exception as e:
            logger.error(f"PDF自动解析失败: id={db_pdf.id}, error={e}")
            import traceback
            traceback.print_exc()
            # 更新状态为failed
            crud.update_pdf_file_status(db, db_pdf.id, "failed", str(e))
            db.commit()

        return db_pdf

    except Exception as e:
        logger.error(f"创建数据库记录失败: {e}")
        # 删除已保存的文件
        file_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建数据库记录失败: {str(e)}"
        )


# ============================================================
# 2. PDF列表查询接口
# ============================================================

@router.get("/", response_model=schemas.PaginatedResponse)
async def list_pdfs(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    process_status: Optional[str] = Query(None, description="过滤处理状态"),
    db: Session = Depends(get_db)
):
    """获取PDF文件列表（分页）.

    Args:
        page: 页码
        page_size: 每页数量
        process_status: 过滤处理状态（pending/processing/success/failed）
        db: 数据库会话

    Returns:
        PaginatedResponse: 分页结果
    """
    skip = (page - 1) * page_size

    # 获取PDF列表
    pdfs = crud.get_pdf_files(db, skip=skip, limit=page_size, process_status=process_status)

    # 统计总数
    total = crud.count_pdf_files(db, process_status=process_status)

    # 计算总页数
    total_pages = (total + page_size - 1) // page_size

    return schemas.PaginatedResponse(
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        items=[schemas.PDFFileResponse.model_validate(pdf) for pdf in pdfs]
    )


# ============================================================
# 3. PDF详情查询接口
# ============================================================

@router.get("/{pdf_id}", response_model=schemas.PDFFileResponse)
async def get_pdf(
    pdf_id: int,
    db: Session = Depends(get_db)
):
    """获取PDF文件详情.

    Args:
        pdf_id: PDF文件ID
        db: 数据库会话

    Returns:
        PDFFileResponse: PDF文件信息

    Raises:
        HTTPException: PDF不存在
    """
    db_pdf = crud.get_pdf_file(db, pdf_id)
    if not db_pdf:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"PDF文件不存在: id={pdf_id}"
        )
    return db_pdf


# ============================================================
# 4. PDF删除接口
# ============================================================

@router.delete("/{pdf_id}", response_model=schemas.MessageResponse)
async def delete_pdf(
    pdf_id: int,
    db: Session = Depends(get_db)
):
    """删除PDF文件（级联删除所有关联数据）.

    Args:
        pdf_id: PDF文件ID
        db: 数据库会话

    Returns:
        MessageResponse: 删除结果消息

    Raises:
        HTTPException: PDF不存在
    """
    # 获取PDF文件信息
    db_pdf = crud.get_pdf_file(db, pdf_id)
    if not db_pdf:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"PDF文件不存在: id={pdf_id}"
        )

    # 删除物理文件
    file_path = Path(db_pdf.file_path)
    if file_path.exists():
        try:
            file_path.unlink()
            logger.info(f"删除物理文件: {file_path}")
        except Exception as e:
            logger.warning(f"删除物理文件失败: {e}")

    # 删除数据库记录（级联删除所有关联数据）
    success = crud.delete_pdf_file(db, pdf_id)

    if success:
        return schemas.MessageResponse(
            message="删除成功",
            detail=f"已删除PDF文件: id={pdf_id}"
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="删除失败"
        )


# ============================================================
# 5. PDF解析接口
# ============================================================

@router.post("/{pdf_id}/parse", response_model=schemas.PDFFileResponse)
async def parse_pdf(
    pdf_id: int,
    db: Session = Depends(get_db)
):
    """触发PDF解析流程.

    功能:
    - 调用Phase 2的完整解析pipeline
    - 将解析结果保存到数据库
    - 更新PDF处理状态

    流程:
    1. 验证PDF文件存在
    2. 更新状态为"processing"
    3. 执行解析（Steps 1-6）
    4. 转换为数据库格式
    5. 保存到数据库
    6. 更新状态为"success"或"failed"

    Args:
        pdf_id: PDF文件ID
        db: 数据库会话

    Returns:
        PDFFileResponse: 更新后的PDF文件信息

    Raises:
        HTTPException: PDF不存在或解析失败
    """
    logger.info(f"接收到PDF解析请求: pdf_id={pdf_id}")

    # 1. 验证PDF文件存在
    db_pdf = crud.get_pdf_file(db, pdf_id)
    if not db_pdf:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"PDF文件不存在: id={pdf_id}"
        )

    # 2. 检查文件是否存在
    file_path = Path(db_pdf.file_path)
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"PDF物理文件不存在: {file_path}"
        )

    # 3. 更新状态为processing
    crud.update_pdf_file_status(db, pdf_id, "processing")
    logger.info(f"开始解析PDF: {file_path}")

    try:
        # 4. 执行PDF解析
        from app.services.pdf_parser_service import PDFParserService

        parser = PDFParserService(dpi=settings.PDF_DPI)
        result = parser.parse_pdf(str(file_path))

        if not result["success"]:
            # 解析失败
            error_msg = result["error"]
            crud.update_pdf_file_status(db, pdf_id, "failed", error_msg)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"PDF解析失败: {error_msg}"
            )

        # 5. 转换为数据库格式
        parsed_data = result["data"]
        db_format_data, validation_results = parser.convert_to_database_format(parsed_data)

        # 6. 保存到数据库
        crud.save_parsed_data_to_db(db, pdf_id, db_format_data)

        # 7. 检查校验结果
        has_validation_errors = any(not result["valid"] for result in validation_results)
        
        if has_validation_errors:
            # 有校验错误，保存校验问题并更新状态
            import json
            validation_issues_json = json.dumps(validation_results)
            db_pdf.validation_issues = validation_issues_json
            db_pdf = crud.update_pdf_file_status(db, pdf_id, "failed", "数据不完整，需要人工检查")
            db_pdf.process_time = datetime.now()
            db.commit()
            logger.warning(f"⚠️ PDF解析完成但有校验错误: id={pdf_id}, 耗时={result['process_time']:.2f}秒")
        else:
            # 校验通过，更新状态为success
            db_pdf = crud.update_pdf_file_status(db, pdf_id, "success")
            db_pdf.process_time = datetime.now()
            db.commit()
            logger.info(f"✅ PDF解析完成: pdf_id={pdf_id}, 耗时={result['process_time']:.2f}秒")

        return db_pdf

    except HTTPException:
        # 重新抛出HTTP异常
        raise

    except Exception as e:
        # 捕获其他异常
        logger.error(f"PDF解析失败: {e}")
        import traceback
        traceback.print_exc()

        # 更新状态为failed
        crud.update_pdf_file_status(db, pdf_id, "failed", str(e))

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"PDF解析失败: {str(e)}"
        )


# ============================================================
# 6. 批量解析接口
# ============================================================

@router.post("/batch-parse", response_model=schemas.MessageResponse)
async def batch_parse_pdfs(
    pdf_ids: List[int],
    db: Session = Depends(get_db)
):
    """批量解析PDF文件.

    Args:
        pdf_ids: PDF文件ID列表
        db: 数据库会话

    Returns:
        MessageResponse: 批量解析结果
    """
    logger.info(f"接收到批量解析请求: {len(pdf_ids)} 个PDF")

    success_count = 0
    failed_count = 0
    errors = []

    for pdf_id in pdf_ids:
        try:
            # 调用单个解析接口
            await parse_pdf(pdf_id, db)
            success_count += 1
        except Exception as e:
            failed_count += 1
            errors.append(f"PDF {pdf_id}: {str(e)}")
            logger.error(f"批量解析失败: pdf_id={pdf_id}, error={e}")

    result_msg = f"批量解析完成: 成功 {success_count} 个, 失败 {failed_count} 个"

    if errors:
        result_msg += f"\n错误详情: {'; '.join(errors[:5])}"  # 只显示前5个错误
        if len(errors) > 5:
            result_msg += f" ...还有 {len(errors) - 5} 个错误"

    return schemas.MessageResponse(
        message=result_msg,
        detail=f"总计: {len(pdf_ids)} 个PDF"
    )


# ============================================================
# 重新解析和状态查询端点
# ============================================================

@router.post("/{pdf_id}/re-parse", response_model=schemas.PDFFileResponse)
async def re_parse_pdf(
    pdf_id: int,
    db: Session = Depends(get_db)
):
    """重新触发PDF解析 (parse别名).

    与parse端点功能相同，用于重新对已上传的PDF进行解析或重新解析。

    Args:
        pdf_id: PDF文件ID

    Returns:
        PDFFileResponse: 更新后的PDF文件信息

    Raises:
        HTTPException: PDF不存在或解析失败
    """
    logger.info(f"接收到PDF重新解析请求: pdf_id={pdf_id}")

    # 验证PDF文件存在
    db_pdf = crud.get_pdf_file(db, pdf_id)
    if not db_pdf:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"PDF文件不存在: id={pdf_id}"
        )

    # 检查文件是否存在
    file_path = Path(db_pdf.file_path)
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"PDF物理文件不存在: {file_path}"
        )

    # 更新状态为processing
    crud.update_pdf_file_status(db, pdf_id, "processing")

    try:
        # 执行解析（复用parse_pdf的逻辑）
        logger.info(f"开始重新解析PDF: {file_path}")
        
        # 4. 执行PDF解析
        from app.services.pdf_parser_service import PDFParserService

        parser = PDFParserService(dpi=settings.PDF_DPI)
        result = parser.parse_pdf(str(file_path))

        if not result["success"]:
            # 解析失败
            error_msg = result["error"]
            crud.update_pdf_file_status(db, pdf_id, "failed", error_msg)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"PDF解析失败: {error_msg}"
            )

        # 5. 转换为数据库格式
        parsed_data = result["data"]
        db_format_data, validation_results = parser.convert_to_database_format(parsed_data)

        # 6. 保存到数据库
        crud.save_parsed_data_to_db(db, pdf_id, db_format_data)

        # 7. 检查校验结果
        has_validation_errors = any(not result["valid"] for result in validation_results)
        
        if has_validation_errors:
            # 有校验错误，保存校验问题并更新状态
            import json
            validation_issues_json = json.dumps(validation_results)
            db_pdf.validation_issues = validation_issues_json
            db_pdf = crud.update_pdf_file_status(db, pdf_id, "failed", "数据不完整，需要人工检查")
            db_pdf.process_time = datetime.now()
            db.commit()
            logger.warning(f"⚠️ PDF重新解析完成但有校验错误: id={pdf_id}, 耗时={result['process_time']:.2f}秒")
        else:
            # 校验通过，更新状态为success
            db_pdf = crud.update_pdf_file_status(db, pdf_id, "success")
            db_pdf.process_time = datetime.now()
            db.commit()
            logger.info(f"✅ PDF重新解析完成: pdf_id={pdf_id}, 耗时={result['process_time']:.2f}秒")

        return db_pdf

    except Exception as e:
        logger.error(f"PDF重新解析失败: pdf_id={pdf_id}, error={e}")
        crud.update_pdf_file_status(db, pdf_id, "failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"PDF解析失败: {str(e)}"
        )


@router.get("/{pdf_id}/status", response_model=schemas.PDFFileResponse)
async def get_pdf_status(
    pdf_id: int,
    db: Session = Depends(get_db)
):
    """获取PDF处理状态.

    返回PDF文件的当前处理状态和基本信息。

    Args:
        pdf_id: PDF文件ID

    Returns:
        PDFFileResponse: PDF文件信息（包含process_status状态字段）

    Raises:
        HTTPException: PDF文件不存在
    """
    logger.info(f"查询PDF状态: pdf_id={pdf_id}")

    db_pdf = crud.get_pdf_file(db, pdf_id)
    if not db_pdf:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"PDF文件不存在: id={pdf_id}"
        )

    return {
        "id": db_pdf.id,
        "filename": db_pdf.filename,
        "file_path": db_pdf.file_path,
        "file_size": db_pdf.file_size,
        "upload_date": db_pdf.upload_date,
        "process_status": db_pdf.process_status,
        "parse_duration": getattr(db_pdf, 'parse_duration', 0.0),
        "created_at": db_pdf.created_at,
        "updated_at": db_pdf.updated_at,
    }


# ============================================================
# END OF pdfs.py
# ============================================================
