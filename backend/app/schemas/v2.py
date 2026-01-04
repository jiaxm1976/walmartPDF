from __future__ import annotations

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field, ConfigDict


class PaymentItem(BaseModel):
    field: str
    value: Any
    raw: Optional[str] = None
    model_config = ConfigDict(
        json_schema_extra={
            "example": {"field": "待付款金额", "value": "$1,234.56", "raw": "$1,234.56"}
        }
    )


class JGData(BaseModel):
    sections: Dict[str, List[PaymentItem]] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "sections": {
                    "header": [{"field": "统计区间", "value": "2025-12-01 - 2025-12-31"}],
                    "right_section": [{"field": "待付款金额", "value": "$1,234.56", "raw": "$1,234.56"}]
                },
                "metadata": {"source": "api_v2_import"}
            }
        }
    )


class ImportResult(BaseModel):
    success: bool
    statement_id: Optional[int] = None
    message: Optional[str] = None
    model_config = ConfigDict(
        json_schema_extra={
            "example": {"success": True, "statement_id": 123, "message": "imported"}
        }
    )


class ParseResult(BaseModel):
    status: str
    success: bool
    data: Optional[JGData] = None
    right_section_raw: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None
    process_time: Optional[float] = None
    model_config = ConfigDict(
        json_schema_extra={
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
    )
