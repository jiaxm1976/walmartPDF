# ============================================================
# 文件: backend/app/api/v1/statements.py
# 功能: 对账单数据检查和修改API路由
# 作者: 开发团队
# 创建时间: 2025-12-18
# ============================================================

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session

from database.config import get_db
from app.schemas import pdf_file as schemas
from app.crud import pdf_file as crud
from app.services.export_service import ExportService

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================
# 1. 获取完整对账单数据接口
# ============================================================

@router.get("/{pdf_id}/data", response_model=schemas.StatementDataResponse)
async def get_statement_data(
    pdf_id: int,
    db: Session = Depends(get_db)
):
    """获取完整的对账单数据（用于数据检查和修改）.

    功能:
    - 获取PDF文件信息
    - 获取对账单头部信息
    - 获取销售明细
    - 获取退款明细
    - 获取其他所有板块数据

    Args:
        pdf_id: PDF文件ID
        db: 数据库会话

    Returns:
        StatementDataResponse: 完整的对账单数据

    Raises:
        HTTPException: PDF不存在或数据未解析
    """
    logger.info(f"获取对账单数据: pdf_id={pdf_id}")

    # 获取完整数据
    statement_data = crud.get_complete_statement_data(db, pdf_id)

    if not statement_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"PDF文件不存在: id={pdf_id}"
        )

    # 检查是否已解析
    pdf_file = statement_data["pdf_file"]
    if pdf_file.process_status == "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="PDF尚未解析，请先触发解析流程"
        )

    return schemas.StatementDataResponse(
        pdf_file=schemas.PDFFileResponse.model_validate(pdf_file),
        header=schemas.StatementHeaderResponse.model_validate(statement_data["header"]) if statement_data["header"] else None,
        sales=schemas.SalesDetailResponse.model_validate(statement_data["sales"]) if statement_data["sales"] else None,
        refund=schemas.RefundDetailResponse.model_validate(statement_data["refund"]) if statement_data["refund"] else None,
        adjustment=schemas.AdjustmentDetailResponse.model_validate(statement_data["adjustment"]) if statement_data["adjustment"] else None,
        wfs=schemas.WFSDetailResponse.model_validate(statement_data["wfs"]) if statement_data["wfs"] else None,
        other_activity=schemas.OtherActivityDetailResponse.model_validate(statement_data["other_activity"]) if statement_data["other_activity"] else None,
        footer=schemas.StatementFooterResponse.model_validate(statement_data["footer"]) if statement_data["footer"] else None,
        payment=schemas.PaymentDetailResponse.model_validate(statement_data["payment"]) if statement_data["payment"] else None,
    )


# ============================================================
# 2. 更新完整对账单数据接口
# ============================================================

@router.put("/{pdf_id}/data", response_model=schemas.StatementDataResponse)
async def update_statement_data(
    pdf_id: int,
    update_data: schemas.StatementDataUpdate,
    db: Session = Depends(get_db)
):
    """更新完整的对账单数据（用于手工修改扫描结果）.

    功能:
    - 支持部分更新（只更新提供的字段）
    - 更新对账单头部信息
    - 更新销售明细
    - 更新退款明细
    - 更新其他板块数据

    Args:
        pdf_id: PDF文件ID
        update_data: 更新的数据
        db: 数据库会话

    Returns:
        StatementDataResponse: 更新后的完整数据

    Raises:
        HTTPException: PDF不存在
    """
    logger.info(f"更新对账单数据: pdf_id={pdf_id}")

    # 执行更新
    updated_data = crud.update_complete_statement_data(db, pdf_id, update_data)

    if not updated_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"PDF文件不存在: id={pdf_id}"
        )

    # 返回更新后的完整数据
    return schemas.StatementDataResponse(
        pdf_file=schemas.PDFFileResponse.model_validate(updated_data["pdf_file"]),
        header=schemas.StatementHeaderResponse.model_validate(updated_data["header"]) if updated_data["header"] else None,
        sales=schemas.SalesDetailResponse.model_validate(updated_data["sales"]) if updated_data["sales"] else None,
        refund=schemas.RefundDetailResponse.model_validate(updated_data["refund"]) if updated_data["refund"] else None,
        adjustment=schemas.AdjustmentDetailResponse.model_validate(updated_data["adjustment"]) if updated_data["adjustment"] else None,
        wfs=schemas.WFSDetailResponse.model_validate(updated_data["wfs"]) if updated_data["wfs"] else None,
        other_activity=schemas.OtherActivityDetailResponse.model_validate(updated_data["other_activity"]) if updated_data["other_activity"] else None,
        footer=schemas.StatementFooterResponse.model_validate(updated_data["footer"]) if updated_data["footer"] else None,
        payment=schemas.PaymentDetailResponse.model_validate(updated_data["payment"]) if updated_data["payment"] else None,
    )


# ============================================================
# 3. 更新对账单头部接口
# ============================================================

@router.patch("/{pdf_id}/header", response_model=schemas.StatementHeaderResponse)
async def update_header(
    pdf_id: int,
    header_data: schemas.StatementHeaderUpdate,
    db: Session = Depends(get_db)
):
    """单独更新对账单头部信息.

    Args:
        pdf_id: PDF文件ID
        header_data: 更新的头部数据
        db: 数据库会话

    Returns:
        StatementHeaderResponse: 更新后的头部数据

    Raises:
        HTTPException: PDF或头部数据不存在
    """
    logger.info(f"更新对账单头部: pdf_id={pdf_id}")

    updated_header = crud.update_statement_header(db, pdf_id, header_data)

    if not updated_header:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"对账单头部不存在: pdf_id={pdf_id}"
        )

    return updated_header


# ============================================================
# 4. 更新销售明细接口
# ============================================================

@router.patch("/{pdf_id}/sales", response_model=schemas.SalesDetailResponse)
async def update_sales(
    pdf_id: int,
    sales_data: schemas.SalesDetailUpdate,
    db: Session = Depends(get_db)
):
    """单独更新销售明细.

    Args:
        pdf_id: PDF文件ID
        sales_data: 更新的销售数据
        db: 数据库会话

    Returns:
        SalesDetailResponse: 更新后的销售数据

    Raises:
        HTTPException: PDF或销售数据不存在
    """
    logger.info(f"更新销售明细: pdf_id={pdf_id}")

    updated_sales = crud.update_sales_detail(db, pdf_id, sales_data)

    if not updated_sales:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"销售明细不存在: pdf_id={pdf_id}"
        )

    return updated_sales


# ============================================================
# 5. 更新退款明细接口
# ============================================================

@router.patch("/{pdf_id}/refund", response_model=schemas.RefundDetailResponse)
async def update_refund(
    pdf_id: int,
    refund_data: schemas.RefundDetailUpdate,
    db: Session = Depends(get_db)
):
    """单独更新退款明细.

    Args:
        pdf_id: PDF文件ID
        refund_data: 更新的退款数据
        db: 数据库会话

    Returns:
        RefundDetailResponse: 更新后的退款数据

    Raises:
        HTTPException: PDF或退款数据不存在
    """
    logger.info(f"更新退款明细: pdf_id={pdf_id}")

    updated_refund = crud.update_refund_detail(db, pdf_id, refund_data)

    if not updated_refund:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"退款明细不存在: pdf_id={pdf_id}"
        )

    return updated_refund


# ============================================================
# 6. 数据验证接口
# ============================================================

@router.post("/{pdf_id}/validate", response_model=schemas.MessageResponse)
async def validate_statement_data(
    pdf_id: int,
    db: Session = Depends(get_db)
):
    """验证对账单数据的完整性和一致性.

    功能:
    - 检查必填字段是否存在
    - 验证总计是否匹配
    - 检查日期范围合理性
    - 检查金额逻辑一致性

    Args:
        pdf_id: PDF文件ID
        db: 数据库会话

    Returns:
        MessageResponse: 验证结果消息

    Raises:
        HTTPException: PDF不存在
    """
    logger.info(f"验证对账单数据: pdf_id={pdf_id}")

    # 获取完整数据
    statement_data = crud.get_complete_statement_data(db, pdf_id)

    if not statement_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"PDF文件不存在: id={pdf_id}"
        )

    errors = []
    warnings = []

    # 1. 检查必填板块
    if not statement_data["header"]:
        errors.append("缺少对账单头部信息")

    if not statement_data["sales"] and not statement_data["refund"]:
        warnings.append("销售和退款数据都为空")

    # 2. 验证日期范围（如果header存在）
    header = statement_data["header"]
    if header and header.start_date >= header.end_date:
        errors.append(f"日期范围不合理: 开始日期({header.start_date}) >= 结束日期({header.end_date})")

    # 3. 验证销售总计（简单示例，实际可能需要更复杂的计算）
    sales = statement_data["sales"]
    if sales:
        calculated_total = (
            sales.product_price +
            sales.shipping +
            sales.wfs_shipping_refund +
            sales.net_tax_collected +
            sales.net_commission +
            sales.withholding_tax +
            sales.wfs_shipping_tax_refund +
            sales.walmart_funded_savings +
            sales.other_total  # 其他低频字段汇总
        )
        # 允许小数点误差
        if abs(calculated_total - sales.total) > 0.02:
            warnings.append(
                f"销售总计可能不匹配: 计算值={calculated_total:.2f}, 记录值={sales.total:.2f}, 差值={abs(calculated_total - sales.total):.2f}"
            )

    # 4. 生成验证结果
    if errors:
        return schemas.MessageResponse(
            message="验证失败",
            detail=f"发现 {len(errors)} 个错误, {len(warnings)} 个警告\n错误: {'; '.join(errors)}\n警告: {'; '.join(warnings)}"
        )
    elif warnings:
        return schemas.MessageResponse(
            message="验证通过（有警告）",
            detail=f"发现 {len(warnings)} 个警告: {'; '.join(warnings)}"
        )
    else:
        return schemas.MessageResponse(
            message="验证通过",
            detail="所有数据验证通过，未发现问题"
        )


# ============================================================
# 7. 数据导出接口
# ============================================================

@router.get("/{pdf_id}/export")
async def export_statement_data(
    pdf_id: int,
    format: str = Query("json", regex="^(json|csv|excel)$"),
    db: Session = Depends(get_db)
):
    """导出对账单数据为指定格式（JSON、CSV、Excel）.

    功能:
    - 支持JSON格式导出
    - 支持CSV格式导出
    - 支持Excel格式导出
    - 自动生成时间戳文件名

    Args:
        pdf_id: PDF文件ID
        format: 导出格式（json/csv/excel）
        db: 数据库会话

    Returns:
        FileResponse: 格式化的导出文件

    Raises:
        HTTPException: PDF不存在或数据未解析
    """
    logger.info(f"导出对账单数据: pdf_id={pdf_id}, format={format}")

    # 获取完整数据
    statement_data = crud.get_complete_statement_data(db, pdf_id)

    if not statement_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"PDF文件不存在: id={pdf_id}"
        )

    pdf_file = statement_data["pdf_file"]

    # 检查是否已解析
    if pdf_file.process_status == "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="PDF尚未解析，请先触发解析流程"
        )

    # 准备导出数据（转换为字典）
    export_data = {
        "pdf_file": schemas.PDFFileResponse.model_validate(pdf_file).model_dump(),
        "header": schemas.StatementHeaderResponse.model_validate(statement_data["header"]).model_dump() if statement_data["header"] else None,
        "sales": schemas.SalesDetailResponse.model_validate(statement_data["sales"]).model_dump() if statement_data["sales"] else None,
        "refund": schemas.RefundDetailResponse.model_validate(statement_data["refund"]).model_dump() if statement_data["refund"] else None,
        "adjustment": schemas.AdjustmentDetailResponse.model_validate(statement_data["adjustment"]).model_dump() if statement_data["adjustment"] else None,
        "wfs": schemas.WFSDetailResponse.model_validate(statement_data["wfs"]).model_dump() if statement_data["wfs"] else None,
        "other_activity": schemas.OtherActivityDetailResponse.model_validate(statement_data["other_activity"]).model_dump() if statement_data["other_activity"] else None,
        "footer": schemas.StatementFooterResponse.model_validate(statement_data["footer"]).model_dump() if statement_data["footer"] else None,
        "payment": schemas.PaymentDetailResponse.model_validate(statement_data["payment"]).model_dump() if statement_data["payment"] else None,
    }

    # 执行导出
    if format == 'excel':
        file_content = ExportService.export_excel(export_data, export_data["pdf_file"])
        filename = ExportService.get_export_filename(pdf_file.original_filename, format)
        return StreamingResponse(
            content=iter([file_content]),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    elif format == 'csv':
        file_content = ExportService.export_csv(export_data, export_data["pdf_file"])
        filename = ExportService.get_export_filename(pdf_file.original_filename, format)
        return StreamingResponse(
            content=iter([file_content]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    else:  # json
        file_content = ExportService.export_json(export_data)
        filename = ExportService.get_export_filename(pdf_file.original_filename, format)
        return StreamingResponse(
            content=iter([file_content]),
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )


@router.post("/batch-export")
async def batch_export_statements(
    pdf_ids: list[int],
    format: str = Query("json", regex="^(json|csv|excel)$"),
    db: Session = Depends(get_db)
):
    """批量导出多个对账单数据为ZIP文件.

    功能:
    - 支持批量导出多个PDF
    - 自动打包为ZIP文件
    - 包含所有选定的对账单

    Args:
        pdf_ids: PDF文件ID列表
        format: 导出格式（json/csv/excel）
        db: 数据库会话

    Returns:
        StreamingResponse: ZIP文件的二进制流

    Raises:
        HTTPException: 没有有效的PDF找到
    """
    logger.info(f"批量导出对账单: pdf_ids={pdf_ids}, format={format}")

    # 收集所有对账单数据
    statements_data = []

    for pdf_id in pdf_ids:
        statement_data = crud.get_complete_statement_data(db, pdf_id)

        if not statement_data or statement_data["pdf_file"].process_status != "success":
            continue

        pdf_file = statement_data["pdf_file"]

        export_data = {
            "pdf_file": schemas.PDFFileResponse.model_validate(pdf_file).model_dump(),
            "header": schemas.StatementHeaderResponse.model_validate(statement_data["header"]).model_dump() if statement_data["header"] else None,
            "sales": schemas.SalesDetailResponse.model_validate(statement_data["sales"]).model_dump() if statement_data["sales"] else None,
            "refund": schemas.RefundDetailResponse.model_validate(statement_data["refund"]).model_dump() if statement_data["refund"] else None,
            "adjustment": schemas.AdjustmentDetailResponse.model_validate(statement_data["adjustment"]).model_dump() if statement_data["adjustment"] else None,
            "wfs": schemas.WFSDetailResponse.model_validate(statement_data["wfs"]).model_dump() if statement_data["wfs"] else None,
            "other_activity": schemas.OtherActivityDetailResponse.model_validate(statement_data["other_activity"]).model_dump() if statement_data["other_activity"] else None,
            "footer": schemas.StatementFooterResponse.model_validate(statement_data["footer"]).model_dump() if statement_data["footer"] else None,
            "payment": schemas.PaymentDetailResponse.model_validate(statement_data["payment"]).model_dump() if statement_data["payment"] else None,
        }

        statements_data.append({
            "pdf_file_info": export_data["pdf_file"],
            "statement_data": export_data
        })

    if not statements_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="没有找到有效的对账单数据"
        )

    # 生成ZIP文件
    zip_content = ExportService.export_batch_zip(statements_data, format)
    timestamp = __import__('datetime').datetime.now().strftime('%Y%m%d_%H%M%S')
    zip_filename = f"{timestamp}_statements_batch.zip"

    return StreamingResponse(
        content=iter([zip_content]),
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename={zip_filename}"}
    )


# ============================================================
# 补充缺失的PATCH端点
# ============================================================

@router.patch("/{pdf_id}/adjustment", response_model=schemas.AdjustmentDetailResponse)
async def update_adjustment(
    pdf_id: int,
    adjustment_data: schemas.AdjustmentDetailUpdate,
    db: Session = Depends(get_db)
):
    """单独更新调整明细.

    Args:
        pdf_id: PDF文件ID
        adjustment_data: 更新的调整数据
        db: 数据库会话

    Returns:
        AdjustmentDetailResponse: 更新后的调整数据

    Raises:
        HTTPException: PDF或调整数据不存在
    """
    logger.info(f"更新调整明细: pdf_id={pdf_id}")

    updated_adjustment = crud.update_adjustment_detail(db, pdf_id, adjustment_data)

    if not updated_adjustment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"调整明细不存在: pdf_id={pdf_id}"
        )

    return updated_adjustment


@router.patch("/{pdf_id}/wfs", response_model=schemas.WFSDetailResponse)
async def update_wfs(
    pdf_id: int,
    wfs_data: schemas.WFSDetailUpdate,
    db: Session = Depends(get_db)
):
    """单独更新WFS费用明细.

    Args:
        pdf_id: PDF文件ID
        wfs_data: 更新的WFS数据
        db: 数据库会话

    Returns:
        WFSDetailResponse: 更新后的WFS数据

    Raises:
        HTTPException: PDF或WFS数据不存在
    """
    logger.info(f"更新WFS费用: pdf_id={pdf_id}")

    updated_wfs = crud.update_wfs_detail(db, pdf_id, wfs_data)

    if not updated_wfs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"WFS明细不存在: pdf_id={pdf_id}"
        )

    return updated_wfs


@router.patch("/{pdf_id}/other-activity", response_model=schemas.OtherActivityDetailResponse)
async def update_other_activity(
    pdf_id: int,
    other_activity_data: schemas.OtherActivityDetailUpdate,
    db: Session = Depends(get_db)
):
    """单独更新其他活动明细.

    Args:
        pdf_id: PDF文件ID
        other_activity_data: 更新的其他活动数据
        db: 数据库会话

    Returns:
        OtherActivityDetailResponse: 更新后的其他活动数据

    Raises:
        HTTPException: PDF或其他活动数据不存在
    """
    logger.info(f"更新其他活动: pdf_id={pdf_id}")

    updated_other_activity = crud.update_other_activity_detail(db, pdf_id, other_activity_data)

    if not updated_other_activity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"其他活动明细不存在: pdf_id={pdf_id}"
        )

    return updated_other_activity


@router.patch("/{pdf_id}/footer", response_model=schemas.StatementFooterResponse)
async def update_footer(
    pdf_id: int,
    footer_data: schemas.StatementFooterUpdate,
    db: Session = Depends(get_db)
):
    """单独更新对账单尾部.

    Args:
        pdf_id: PDF文件ID
        footer_data: 更新的尾部数据
        db: 数据库会话

    Returns:
        StatementFooterResponse: 更新后的尾部数据

    Raises:
        HTTPException: PDF或尾部数据不存在
    """
    logger.info(f"更新对账单尾部: pdf_id={pdf_id}")

    updated_footer = crud.update_statement_footer(db, pdf_id, footer_data)

    if not updated_footer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"对账单尾部不存在: pdf_id={pdf_id}"
        )

    return updated_footer


@router.patch("/{pdf_id}/payment", response_model=schemas.PaymentDetailResponse)
async def update_payment(
    pdf_id: int,
    payment_data: schemas.PaymentDetailUpdate,
    db: Session = Depends(get_db)
):
    """单独更新付款详情.

    Args:
        pdf_id: PDF文件ID
        payment_data: 更新的付款数据
        db: 数据库会话

    Returns:
        PaymentDetailResponse: 更新后的付款数据

    Raises:
        HTTPException: PDF或付款数据不存在
    """
    logger.info(f"更新付款详情: pdf_id={pdf_id}")

    updated_payment = crud.update_payment_detail(db, pdf_id, payment_data)

    if not updated_payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"付款详情不存在: pdf_id={pdf_id}"
        )

    return updated_payment


# ============================================================
# END OF statements.py
# ============================================================
