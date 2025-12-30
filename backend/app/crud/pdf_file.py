# ============================================================
# 文件: backend/app/crud/pdf_file.py
# 功能: PDF文件和对账单数据的CRUD操作
# 作者: 开发团队
# 创建时间: 2025-12-18
# ============================================================

from typing import Optional, List, Dict, Any
from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_
import logging

from database import models
from app.schemas import pdf_file as schemas

logger = logging.getLogger(__name__)


# ============================================================
# 1. PDF文件CRUD操作
# ============================================================

def create_pdf_file(db: Session, pdf_data: schemas.PDFFileCreate) -> models.PDFFile:
    """创建PDF文件记录.

    Args:
        db: 数据库会话
        pdf_data: PDF文件数据

    Returns:
        models.PDFFile: 创建的PDF文件对象
    """
    db_pdf = models.PDFFile(
        filename=pdf_data.filename,
        original_filename=pdf_data.original_filename,
        file_path=pdf_data.file_path,
        file_size=pdf_data.file_size,
        file_hash=pdf_data.file_hash,
        process_status='pending'
    )
    db.add(db_pdf)
    db.commit()
    db.refresh(db_pdf)
    logger.info(f"创建PDF文件记录: id={db_pdf.id}, filename={db_pdf.filename}")
    return db_pdf


def get_pdf_file(db: Session, pdf_id: int) -> Optional[models.PDFFile]:
    """根据ID获取PDF文件.

    Args:
        db: 数据库会话
        pdf_id: PDF文件ID

    Returns:
        Optional[models.PDFFile]: PDF文件对象，不存在则返回None
    """
    return db.query(models.PDFFile).filter(models.PDFFile.id == pdf_id).first()


def get_pdf_files(
    db: Session,
    skip: int = 0,
    limit: int = 10,
    process_status: Optional[str] = None
) -> List[models.PDFFile]:
    """获取PDF文件列表.

    Args:
        db: 数据库会话
        skip: 跳过记录数
        limit: 返回记录数
        process_status: 过滤处理状态

    Returns:
        List[models.PDFFile]: PDF文件列表
    """
    query = db.query(models.PDFFile)

    if process_status:
        query = query.filter(models.PDFFile.process_status == process_status)

    return query.order_by(desc(models.PDFFile.created_at)).offset(skip).limit(limit).all()


def count_pdf_files(db: Session, process_status: Optional[str] = None) -> int:
    """统计PDF文件数量.

    Args:
        db: 数据库会话
        process_status: 过滤处理状态

    Returns:
        int: 文件数量
    """
    query = db.query(models.PDFFile)

    if process_status:
        query = query.filter(models.PDFFile.process_status == process_status)

    return query.count()


def update_pdf_file_status(
    db: Session,
    pdf_id: int,
    status: str,
    error_message: Optional[str] = None
) -> Optional[models.PDFFile]:
    """更新PDF文件处理状态.

    Args:
        db: 数据库会话
        pdf_id: PDF文件ID
        status: 处理状态
        error_message: 错误信息

    Returns:
        Optional[models.PDFFile]: 更新后的PDF文件对象
    """
    db_pdf = get_pdf_file(db, pdf_id)
    if db_pdf:
        db_pdf.process_status = status
        if error_message:
            db_pdf.error_message = error_message
        if status in ['success', 'failed']:
            from datetime import datetime
            db_pdf.process_time = datetime.now()
        db.commit()
        db.refresh(db_pdf)
        logger.info(f"更新PDF文件状态: id={pdf_id}, status={status}")
    return db_pdf


def delete_pdf_file(db: Session, pdf_id: int) -> bool:
    """删除PDF文件（级联删除所有关联数据）.

    Args:
        db: 数据库会话
        pdf_id: PDF文件ID

    Returns:
        bool: 是否删除成功
    """
    db_pdf = get_pdf_file(db, pdf_id)
    if db_pdf:
        db.delete(db_pdf)
        db.commit()
        logger.info(f"删除PDF文件: id={pdf_id}")
        return True
    return False


def get_pdf_file_by_hash(db: Session, file_hash: str) -> Optional[models.PDFFile]:
    """根据文件哈希获取PDF文件.

    Args:
        db: 数据库会话
        file_hash: 文件哈希值

    Returns:
        Optional[models.PDFFile]: PDF文件对象，不存在则返回None
    """
    return db.query(models.PDFFile).filter(models.PDFFile.file_hash == file_hash).first()


# ============================================================
# 2. 对账单头部CRUD操作
# ============================================================

def create_statement_header(
    db: Session,
    header_data: schemas.StatementHeaderCreate
) -> models.StatementHeader:
    """创建对账单头部.

    Args:
        db: 数据库会话
        header_data: 头部数据

    Returns:
        models.StatementHeader: 创建的头部对象
    """
    db_header = models.StatementHeader(**header_data.model_dump())
    db.add(db_header)
    db.commit()
    db.refresh(db_header)
    return db_header


def get_statement_header(db: Session, pdf_id: int) -> Optional[models.StatementHeader]:
    """获取对账单头部.

    Args:
        db: 数据库会话
        pdf_id: PDF文件ID

    Returns:
        Optional[models.StatementHeader]: 头部对象
    """
    return db.query(models.StatementHeader).filter(
        models.StatementHeader.pdf_file_id == pdf_id
    ).first()


def update_statement_header(
    db: Session,
    pdf_id: int,
    header_data: schemas.StatementHeaderUpdate
) -> Optional[models.StatementHeader]:
    """更新对账单头部.

    Args:
        db: 数据库会话
        pdf_id: PDF文件ID
        header_data: 更新的头部数据

    Returns:
        Optional[models.StatementHeader]: 更新后的头部对象
    """
    db_header = get_statement_header(db, pdf_id)
    if db_header:
        update_data = header_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_header, key, value)
        db.commit()
        db.refresh(db_header)
        logger.info(f"更新对账单头部: pdf_id={pdf_id}")
    return db_header


# ============================================================
# 3. 销售明细CRUD操作
# ============================================================

def create_sales_detail(
    db: Session,
    sales_data: schemas.SalesDetailCreate
) -> models.SalesDetail:
    """创建销售明细.

    Args:
        db: 数据库会话
        sales_data: 销售数据

    Returns:
        models.SalesDetail: 创建的销售明细对象
    """
    db_sales = models.SalesDetail(**sales_data.model_dump())
    db.add(db_sales)
    db.commit()
    db.refresh(db_sales)
    return db_sales


def get_sales_detail(db: Session, pdf_id: int) -> Optional[models.SalesDetail]:
    """获取销售明细.

    Args:
        db: 数据库会话
        pdf_id: PDF文件ID

    Returns:
        Optional[models.SalesDetail]: 销售明细对象
    """
    return db.query(models.SalesDetail).filter(
        models.SalesDetail.pdf_file_id == pdf_id
    ).first()


def update_sales_detail(
    db: Session,
    pdf_id: int,
    sales_data: schemas.SalesDetailUpdate
) -> Optional[models.SalesDetail]:
    """更新销售明细.

    Args:
        db: 数据库会话
        pdf_id: PDF文件ID
        sales_data: 更新的销售数据

    Returns:
        Optional[models.SalesDetail]: 更新后的销售明细对象
    """
    db_sales = get_sales_detail(db, pdf_id)
    if db_sales:
        update_data = sales_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_sales, key, value)
        db.commit()
        db.refresh(db_sales)
        logger.info(f"更新销售明细: pdf_id={pdf_id}")
    return db_sales


# ============================================================
# 4. 退款明细CRUD操作
# ============================================================

def create_refund_detail(
    db: Session,
    refund_data: schemas.RefundDetailCreate
) -> models.RefundDetail:
    """创建退款明细.

    Args:
        db: 数据库会话
        refund_data: 退款数据

    Returns:
        models.RefundDetail: 创建的退款明细对象
    """
    db_refund = models.RefundDetail(**refund_data.model_dump())
    db.add(db_refund)
    db.commit()
    db.refresh(db_refund)
    return db_refund


def get_refund_detail(db: Session, pdf_id: int) -> Optional[models.RefundDetail]:
    """获取退款明细.

    Args:
        db: 数据库会话
        pdf_id: PDF文件ID

    Returns:
        Optional[models.RefundDetail]: 退款明细对象
    """
    return db.query(models.RefundDetail).filter(
        models.RefundDetail.pdf_file_id == pdf_id
    ).first()


def update_refund_detail(
    db: Session,
    pdf_id: int,
    refund_data: schemas.RefundDetailUpdate
) -> Optional[models.RefundDetail]:
    """更新退款明细.

    Args:
        db: 数据库会话
        pdf_id: PDF文件ID
        refund_data: 更新的退款数据

    Returns:
        Optional[models.RefundDetail]: 更新后的退款明细对象
    """
    db_refund = get_refund_detail(db, pdf_id)
    if db_refund:
        update_data = refund_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_refund, key, value)
        db.commit()
        db.refresh(db_refund)
        logger.info(f"更新退款明细: pdf_id={pdf_id}")
    return db_refund


# ============================================================
# 5. 完整对账单数据操作
# ============================================================

def get_complete_statement_data(db: Session, pdf_id: int) -> Optional[Dict[str, Any]]:
    """获取完整的对账单数据（包括所有板块）.

    Args:
        db: 数据库会话
        pdf_id: PDF文件ID

    Returns:
        Optional[Dict]: 完整的对账单数据，包括:
            - pdf_file: PDF文件信息
            - header: 头部信息
            - sales: 销售明细
            - refund: 退款明细
            - adjustment: 调整明细
            - wfs: WFS明细
            - other_activity: 其他活动
            - footer: 对账单尾部
            - payment: 付款详情
    """
    # 获取PDF文件
    pdf_file = get_pdf_file(db, pdf_id)
    if not pdf_file:
        return None

    # 获取各个板块数据
    return {
        "pdf_file": pdf_file,
        "header": get_statement_header(db, pdf_id),
        "sales": get_sales_detail(db, pdf_id),
        "refund": get_refund_detail(db, pdf_id),
        "adjustment": db.query(models.AdjustmentDetail).filter(
            models.AdjustmentDetail.pdf_file_id == pdf_id
        ).first(),
        "wfs": db.query(models.WFSDetail).filter(
            models.WFSDetail.pdf_file_id == pdf_id
        ).first(),
        "other_activity": db.query(models.OtherActivityDetail).filter(
            models.OtherActivityDetail.pdf_file_id == pdf_id
        ).first(),
        "footer": db.query(models.StatementFooter).filter(
            models.StatementFooter.pdf_file_id == pdf_id
        ).first(),
        "payment": db.query(models.PaymentDetail).filter(
            models.PaymentDetail.pdf_file_id == pdf_id
        ).first(),
    }


def update_complete_statement_data(
    db: Session,
    pdf_id: int,
    update_data: schemas.StatementDataUpdate
) -> Optional[Dict[str, Any]]:
    """更新完整的对账单数据.

    Args:
        db: 数据库会话
        pdf_id: PDF文件ID
        update_data: 更新数据

    Returns:
        Optional[Dict]: 更新后的完整数据
    """
    # 验证PDF文件存在
    pdf_file = get_pdf_file(db, pdf_id)
    if not pdf_file:
        return None

    # 更新各个板块
    if update_data.header:
        update_statement_header(db, pdf_id, update_data.header)

    if update_data.sales:
        update_sales_detail(db, pdf_id, update_data.sales)

    if update_data.refund:
        update_refund_detail(db, pdf_id, update_data.refund)

    if update_data.adjustment:
        adjustment = db.query(models.AdjustmentDetail).filter(
            models.AdjustmentDetail.pdf_file_id == pdf_id
        ).first()
        if adjustment:
            for key, value in update_data.adjustment.dict(exclude_unset=True).items():
                setattr(adjustment, key, value)

    if update_data.wfs:
        wfs = db.query(models.WFSDetail).filter(
            models.WFSDetail.pdf_file_id == pdf_id
        ).first()
        if wfs:
            for key, value in update_data.wfs.dict(exclude_unset=True).items():
                setattr(wfs, key, value)

    if update_data.other_activity:
        other = db.query(models.OtherActivityDetail).filter(
            models.OtherActivityDetail.pdf_file_id == pdf_id
        ).first()
        if other:
            for key, value in update_data.other_activity.dict(exclude_unset=True).items():
                setattr(other, key, value)

    if update_data.footer:
        footer = db.query(models.StatementFooter).filter(
            models.StatementFooter.pdf_file_id == pdf_id
        ).first()
        if footer:
            for key, value in update_data.footer.dict(exclude_unset=True).items():
                setattr(footer, key, value)

    if update_data.payment:
        payment = db.query(models.PaymentDetail).filter(
            models.PaymentDetail.pdf_file_id == pdf_id
        ).first()
        if payment:
            for key, value in update_data.payment.dict(exclude_unset=True).items():
                setattr(payment, key, value)

    db.commit()
    logger.info(f"更新完整对账单数据: pdf_id={pdf_id}")

    # 返回更新后的完整数据
    return get_complete_statement_data(db, pdf_id)


# ============================================================
# 6. 保存解析结果到数据库
# ============================================================

def save_parsed_data_to_db(
    db: Session,
    pdf_id: int,
    parsed_data: Dict[str, Any]
) -> bool:
    """将解析结果保存到数据库.

    Args:
        db: 数据库会话
        pdf_id: PDF文件ID
        parsed_data: 解析后的数据
            {
                "header": {...},
                "sales": {...},
                "refund": {...},
                ...
            }

    Returns:
        bool: 是否保存成功
    """
    try:
        # 1. 保存header
        if "header" in parsed_data and parsed_data["header"]:
            header_data = parsed_data["header"]
            # 检查是否已存在
            existing_header = get_statement_header(db, pdf_id)
            if existing_header:
                # 更新
                for key, value in header_data.items():
                    setattr(existing_header, key, value)
            else:
                # 创建新记录
                db_header = models.StatementHeader(
                    pdf_file_id=pdf_id,
                    **header_data
                )
                db.add(db_header)

        # 2. 保存sales
        if "sales" in parsed_data and parsed_data["sales"]:
            sales_data = parsed_data["sales"]
            existing_sales = get_sales_detail(db, pdf_id)
            if existing_sales:
                for key, value in sales_data.items():
                    setattr(existing_sales, key, value)
            else:
                db_sales = models.SalesDetail(
                    pdf_file_id=pdf_id,
                    **sales_data
                )
                db.add(db_sales)

        # 3. 保存refund
        if "refund" in parsed_data and parsed_data["refund"]:
            refund_data = parsed_data["refund"]
            existing_refund = get_refund_detail(db, pdf_id)
            if existing_refund:
                for key, value in refund_data.items():
                    setattr(existing_refund, key, value)
            else:
                db_refund = models.RefundDetail(
                    pdf_file_id=pdf_id,
                    **refund_data
                )
                db.add(db_refund)

        # 4. 保存adjustment
        if "adjustment" in parsed_data and parsed_data["adjustment"]:
            adjustment_data = parsed_data["adjustment"]
            existing = db.query(models.AdjustmentDetail).filter(
                models.AdjustmentDetail.pdf_file_id == pdf_id
            ).first()
            if existing:
                for key, value in adjustment_data.items():
                    setattr(existing, key, value)
            else:
                db_adjustment = models.AdjustmentDetail(
                    pdf_file_id=pdf_id,
                    **adjustment_data
                )
                db.add(db_adjustment)

        # 5. 保存wfs
        if "wfs" in parsed_data and parsed_data["wfs"]:
            wfs_data = parsed_data["wfs"]
            existing = db.query(models.WFSDetail).filter(
                models.WFSDetail.pdf_file_id == pdf_id
            ).first()
            if existing:
                for key, value in wfs_data.items():
                    setattr(existing, key, value)
            else:
                db_wfs = models.WFSDetail(
                    pdf_file_id=pdf_id,
                    **wfs_data
                )
                db.add(db_wfs)

        # 6. 保存other_activity
        if "other_activity" in parsed_data and parsed_data["other_activity"]:
            other_data = parsed_data["other_activity"]
            existing = db.query(models.OtherActivityDetail).filter(
                models.OtherActivityDetail.pdf_file_id == pdf_id
            ).first()
            if existing:
                for key, value in other_data.items():
                    setattr(existing, key, value)
            else:
                db_other = models.OtherActivityDetail(
                    pdf_file_id=pdf_id,
                    **other_data
                )
                db.add(db_other)

        # 7. 保存footer
        if "footer" in parsed_data and parsed_data["footer"]:
            footer_data = parsed_data["footer"]
            existing = db.query(models.StatementFooter).filter(
                models.StatementFooter.pdf_file_id == pdf_id
            ).first()
            if existing:
                for key, value in footer_data.items():
                    setattr(existing, key, value)
            else:
                db_footer = models.StatementFooter(
                    pdf_file_id=pdf_id,
                    **footer_data
                )
                db.add(db_footer)

        # 8. 保存payment
        if "payment" in parsed_data and parsed_data["payment"]:
            payment_data = parsed_data["payment"]
            existing = db.query(models.PaymentDetail).filter(
                models.PaymentDetail.pdf_file_id == pdf_id
            ).first()
            if existing:
                for key, value in payment_data.items():
                    setattr(existing, key, value)
            else:
                db_payment = models.PaymentDetail(
                    pdf_file_id=pdf_id,
                    **payment_data
                )
                db.add(db_payment)

        # 提交事务
        db.commit()
        logger.info(f"解析结果已保存到数据库: pdf_id={pdf_id}")
        return True

    except Exception as e:
        logger.error(f"保存解析结果失败: {e}")
        db.rollback()
        raise


# ============================================================
# 7. 日期范围查询操作
# ============================================================

def get_statements_by_date_range(
    db: Session,
    start_date: date,
    end_date: date
) -> List[Dict[str, Any]]:
    """查询指定日期范围内的完整对账单数据.

    Args:
        db: 数据库会话
        start_date: 开始日期（包含）
        end_date: 结束日期（包含）

    Returns:
        List[Dict]: 完整对账单数据列表，每项包含所有8个板块的数据
    """
    headers = db.query(models.StatementHeader).filter(
        and_(
            models.StatementHeader.start_date >= start_date,
            models.StatementHeader.end_date <= end_date
        )
    ).all()

    statements_data = []
    for header in headers:
        pdf_id = header.pdf_file_id
        statement = get_complete_statement_data(db, pdf_id)
        if statement:
            statements_data.append(statement)

    logger.info(f"查询日期范围对账单: {start_date} 到 {end_date}, 找到 {len(statements_data)} 条")
    return statements_data


def get_statements_grouped_by_period(
    db: Session,
    start_date: date,
    end_date: date,
    granularity: str = "monthly"
) -> Dict[str, List[Dict[str, Any]]]:
    """按时间粒度分组查询对账单数据.

    Args:
        db: 数据库会话
        start_date: 开始日期
        end_date: 结束日期
        granularity: 时间粒度 ("monthly" | "weekly" | "statement")

    Returns:
        Dict: 按时期分组的对账单数据
            - monthly: {"2024-12": [...], "2025-01": [...]}
            - weekly: {"2024-W50": [...], "2024-W51": [...]}
            - statement: {"statement_1": [...], "statement_2": [...]}
    """
    statements = get_statements_by_date_range(db, start_date, end_date)

    if granularity == "monthly":
        grouped = {}
        for stmt in statements:
            header = stmt["header"]
            if header:
                period_key = header.start_date.strftime("%Y-%m")
                if period_key not in grouped:
                    grouped[period_key] = []
                grouped[period_key].append(stmt)
        return dict(sorted(grouped.items()))

    elif granularity == "weekly":
        grouped = {}
        for stmt in statements:
            header = stmt["header"]
            if header:
                iso_year, iso_week, _ = header.start_date.isocalendar()
                period_key = f"{iso_year}-W{iso_week:02d}"
                if period_key not in grouped:
                    grouped[period_key] = []
                grouped[period_key].append(stmt)
        return dict(sorted(grouped.items()))

    else:  # statement
        grouped = {}
        for idx, stmt in enumerate(statements, 1):
            period_key = f"statement_{idx}"
            grouped[period_key] = [stmt]
        return grouped


# ============================================================
# END OF pdf_file.py
# ============================================================
