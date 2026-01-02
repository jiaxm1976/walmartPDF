from pydantic import BaseModel
from typing import Optional, Any, Dict


class ImportRequest(BaseModel):
    pdf_path: str
    output_dir: Optional[str] = None


class ImportResponse(BaseModel):
    success: bool
    message: str
    result: Optional[Dict[str, Any]] = None


class ImportParsedRequest(BaseModel):
    # 可选：解析后的 JSON 文件路径（默认使用测试输出目录中的 manual_run_venv2/parsed_data.json）
    parsed_file_path: Optional[str] = None
    # 导入时使用的 pdf_name（可选，用于写入 statements.pdf_name）
    pdf_name: Optional[str] = None
