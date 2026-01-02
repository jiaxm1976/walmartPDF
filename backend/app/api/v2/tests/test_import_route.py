import sys
import pathlib
import asyncio

# 确保从仓库根可以导入 `backend` 包
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[5]))


def test_v2_health_direct():
    # 直接调用路由函数，避免 TestClient 兼容性问题
    from backend.app.api.v2.routes import v2_health

    result = asyncio.run(v2_health())
    assert isinstance(result, dict)
    assert result.get("version") == "v2"


def test_import_route_mock():
    # 使用简单的 Dummy 替换 PDFParserService，验证 import_pdf 处理逻辑
    from backend.app.api.v2 import routes as routes_module
    from backend.app.api.v2.schemas import ImportRequest

    class DummyParser:
        def parse_pdf_direct(self, pdf_path, output_dir=None):
            return {"success": True, "data": {"left_section": {"meta": "ok"}, "right_section": {}}, "process_time": 0.1}

    orig = getattr(routes_module, "PDFParserService", None)
    routes_module.PDFParserService = DummyParser

    try:
        req = ImportRequest(pdf_path="/tmp/dummy.pdf")
        res = asyncio.run(routes_module.import_pdf(req, user={"username": "dev", "role": "admin"}))
        # import_pdf 返回 Pydantic ImportResponse
        assert getattr(res, "success", False) is True
        assert "result" in res.__dict__
    finally:
        if orig is not None:
            routes_module.PDFParserService = orig
