#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据导出 API 端点
提供 HTTP 接口来导出数据到 Excel
"""

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse
from pathlib import Path
from datetime import datetime
import sys
import os

# 添加脚本目录到 Python 路径
SCRIPT_DIR = Path(__file__).parent.parent / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

# 导入导出脚本
from export_data_to_excel import export_to_excel

router = APIRouter(prefix="/api/export", tags=["导出"])


@router.post("/data-to-excel")
async def export_data(
    start_date: str = Query(..., description="开始日期，格式为 YYYY-MM-DD，如 2025-09-06"),
    end_date: str = Query(None, description="结束日期（可选），格式为 YYYY-MM-DD；若提供则必须与 PDF 的统计结束日期匹配")
):
    """
    导出数据到 Excel 文件。
    
    Args:
        start_date: 开始日期，格式为 YYYY-MM-DD
        
    Returns:
        Excel 文件流
        
    Raises:
        HTTPException: 如果日期格式错误或导出失败
    """
    # 验证 start_date 格式
    try:
        datetime.strptime(start_date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail=f"开始日期格式错误，应为 YYYY-MM-DD，您输入的是 '{start_date}'")

    # 验证 end_date 格式（若提供）
    if end_date is not None:
        try:
            datetime.strptime(end_date, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(status_code=400, detail=f"结束日期格式错误，应为 YYYY-MM-DD，您输入的是 '{end_date}'")

    try:
        # 执行导出（export_to_excel 会在提供 end_date 时强制要求匹配）
        output_file = export_to_excel(start_date, end_date)

        if not output_file:
            # 说明没有符合条件的数据
            msg = f"没有找到符合条件的数据（开始日期 >= {start_date}"
            if end_date is not None:
                msg += f" 且统计结束日期 = {end_date}")"
            else:
                msg += ")"
            raise HTTPException(status_code=404, detail=msg)

        output_path = Path(output_file)
        return FileResponse(
            path=output_path,
            filename=output_path.name,
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导出失败：{str(e)}")


@router.get("/data-to-excel/status")
async def get_export_status(
    start_date: str = Query(..., description="开始日期，格式为 YYYY-MM-DD"),
    end_date: str = Query(None, description="结束日期（可选），格式为 YYYY-MM-DD；若提供则要求与统计结束日期匹配")
):
    """
    检查导出数据的状态（不生成文件，只返回统计信息）。
    
    Args:
        start_date: 开始日期，格式为 YYYY-MM-DD
        
    Returns:
        导出数据的统计信息
    """
    try:
        # 验证日期格式
        datetime.strptime(start_date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"日期格式错误，应为 YYYY-MM-DD，您输入的是 '{start_date}'"
        )
    
    try:
        import sqlite3
        from pathlib import Path

        # 获取数据库路径
        PROJECT_ROOT = Path(__file__).resolve().parent.parent
        DB_PATH = PROJECT_ROOT / "backend" / "data" / "walmart_pdf_parser.db"

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # 获取所有 statements 并在 Python 中按规则过滤（便于处理结束日期精确匹配）
        cursor.execute("SELECT id, statement_period FROM statements ORDER BY statement_period ASC")
        stmt_rows = cursor.fetchall()

        matched_stmt_ids = []
        for sid, period in stmt_rows:
            if not period or " - " not in period:
                continue
            period_start = period.split(" - ")[0].strip()
            period_end = period.split(" - ")[1].strip()
            if period_start >= start_date:
                if end_date is not None:
                    if period_end == end_date:
                        matched_stmt_ids.append(sid)
                else:
                    matched_stmt_ids.append(sid)

        if not matched_stmt_ids:
            return {
                "status": "success",
                "start_date": start_date,
                "end_date": end_date,
                "pdf_count": 0,
                "section_count": 0,
                "message": "没有找到符合条件的 PDF"
            }

        # 查询 section_data 数量
        placeholders = ','.join('?' * len(matched_stmt_ids))
        cursor.execute(f"SELECT COUNT(*) FROM section_data WHERE statement_id IN ({placeholders})", matched_stmt_ids)
        section_count = cursor.fetchone()[0]

        conn.close()

        return {
            "status": "success",
            "start_date": start_date,
            "end_date": end_date,
            "pdf_count": len(matched_stmt_ids),
            "section_count": section_count,
            "message": f"找到 {len(matched_stmt_ids)} 个 PDF，{section_count} 个 section 记录"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询失败：{str(e)}")
