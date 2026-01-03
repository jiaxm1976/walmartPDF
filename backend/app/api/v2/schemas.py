"""
Pydantic 模型集合：用于定义 API 的输入/输出结构。

Pydantic 的好处：
- 自动做类型校验（请求到达路由前自动验证）；
- 自动生成 OpenAPI / Swagger 文档（字段名和注释会反映在文档中）；
- 使得路由实现更简洁，路由函数可以直接接收已验证的模型对象。
"""

from pydantic import BaseModel
from typing import Optional, Any, Dict


class HealthResponse(BaseModel):
    """健康检查的响应模型。

    - `status`: 服务状态字符串，例如 "ok" 或 "healthy"；
    - `version`: 可选的 API 版本字符串。
    """
    status: str
    version: Optional[str]


class ImportRequest(BaseModel):
    """导入请求模型（POST /api/v2/import 的请求体）。

    字段：
    - `pdf_path` (str): 要解析的 PDF 文件路径（相对或绝对），必填；
    - `output_dir` (Optional[str]): 可选的解析输出目录，便于调试。
    """
    pdf_path: str
    output_dir: Optional[str] = None


class ImportResponse(BaseModel):
    """导入响应模型。

    - `success`：是否成功（布尔）；
    - `message`：简短的状态/错误说明；
    - `result`：可选的额外信息，例如 `statement_id`。
    """
    success: bool
    message: str
    result: Optional[Dict[str, Any]] = None


class ImportParsedRequest(BaseModel):
    """从已经解析好的 JSON 导入的请求模型。

    - `parsed_file_path`：解析器产生的 JSON 文件路径，默认测试目录下的示例文件；
    - `pdf_name`：导入时写入数据库的 PDF 文件名（可选，默认会生成或使用占位名）。
    """
    parsed_file_path: Optional[str] = None
    pdf_name: Optional[str] = None


class StatementSummary(BaseModel):
    """对账单列表项的简要模型。

    字段说明：
    - `id`: 报表ID
    - `pdf_name`: PDF 文件名
    - `statement_period`: 报表统计周期
    - `payment_to_you`: 向您支付的金额（字符串格式，可能为空）
    """
    id: int
    pdf_name: Optional[str]
    statement_period: Optional[str]
    payment_to_you: Optional[str]


class StatementsListResponse(BaseModel):
    """对账单列表查询的响应模型（支持分页）。

    - `success`: 是否成功
    - `message`: 状态描述
    - `total`: 总记录数（可选）
    - `items`: 当前页的 `StatementSummary` 列表
    """
    success: bool
    message: str
    total: Optional[int] = None
    items: Optional[list[StatementSummary]] = None


class StatementDetail(BaseModel):
    """对账单详情响应模型。

    包含：
    - `id`、`pdf_name`、`statement_period` 基本信息
    - `sections`：以字典形式返回各板块的 JSON 数据（方便前端直接展示）
    """
    id: int
    pdf_name: Optional[str]
    statement_period: Optional[str]
    payment_to_you: Optional[str]
    sections: Optional[Dict[str, Any]] = None


class StatementDetailResponse(BaseModel):
    """GET /statements/{id} 的统一响应模型。"""
    success: bool
    message: str
    item: Optional[StatementDetail] = None
