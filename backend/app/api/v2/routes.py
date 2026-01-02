from fastapi import APIRouter, Depends, HTTPException
from backend.app.api.v2.schemas import ImportRequest, ImportResponse
from backend.app.api.v2.dependencies import get_current_user
from backend.app.services.pdf_parser_service import PDFParserService
from backend.database.structured_importer import StructuredDataImporter
from backend.app.api.v2.schemas import ImportParsedRequest
from pathlib import Path
import json

router = APIRouter()


@router.get("/health")
async def v2_health():
    return {"status": "ok", "version": "v2"}


@router.post("/import", response_model=ImportResponse)
async def import_pdf(req: ImportRequest, user=Depends(get_current_user)):
    parser = PDFParserService()
    res = parser.parse_pdf_direct(req.pdf_path, output_dir=req.output_dir)
    if not res.get("success"):
        raise HTTPException(status_code=500, detail=res.get("error"))
    return ImportResponse(success=True, message="Imported", result=res)


@router.post("/import_parsed", response_model=ImportResponse)
async def import_parsed(req: ImportParsedRequest, user=Depends(get_current_user)):
    """从已解析的 JSON 导入到数据库。默认使用 backend/tests/output/manual_run_venv2/parsed_data.json"""
    # 默认路径
    default_parsed = Path("backend/tests/output/manual_run_venv2/parsed_data.json")
    parsed_path = Path(req.parsed_file_path) if req.parsed_file_path else default_parsed

    if not parsed_path.exists():
        raise HTTPException(status_code=400, detail=f"parsed file not found: {parsed_path}")

    try:
        with open(parsed_path, 'r', encoding='utf-8') as f:
            parsed = json.load(f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"failed to read parsed json: {e}")

    left = parsed.get('left_section') or {}
    right = parsed.get('right_section') or {}

    if 'sections' in left:
        jg_data = left
    else:
        jg_data = {'sections': {}, 'metadata': {}}

    if right:
        jg_data.setdefault('sections', {})
        jg_data['sections']['right_section'] = []
        for k, v in right.items():
            jg_data['sections']['right_section'].append({'field': k, 'value': v, 'raw': str(v), 'line_no': 0})

    db_path = Path('backend/data/walmart_pdf_parser.db')
    importer = StructuredDataImporter(str(db_path))
    importer.connect()

    pdf_name = req.pdf_name or 'imported_parsed.pdf'
    sid = importer.import_jg_data(pdf_name, jg_data)
    importer.disconnect()

    if sid is None:
        raise HTTPException(status_code=500, detail='import failed')

    return ImportResponse(success=True, message='imported', result={'statement_id': sid})
