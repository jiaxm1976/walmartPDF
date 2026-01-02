import sys
import pathlib
import asyncio

# 确保从仓库根导入 `backend` 包
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[5]))

from backend.app.api.v2.routes import import_parsed
from backend.app.api.v2.schemas import ImportParsedRequest
import uuid


def test_import_parsed_direct_call():
    unique_name = f"test_api_import_{uuid.uuid4().hex}.pdf"
    req = ImportParsedRequest(parsed_file_path='backend/tests/output/manual_run_venv2/parsed_data.json', pdf_name=unique_name)
    res = asyncio.run(import_parsed(req, user=None))
    assert res.success is True
    assert isinstance(res.result, dict)
    assert 'statement_id' in res.result
