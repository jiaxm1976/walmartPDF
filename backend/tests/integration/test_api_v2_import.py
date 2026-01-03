import sys
from pathlib import Path
project_root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(project_root))

from backend.app.api.v2.routes import import_pdf
from backend.app.api.v2.schemas import ImportRequest

import logging
import os

# Configure simple logging so test run shows informative messages.
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class DummyImporter:
    def __init__(self):
        self.connected = False

    def connect(self):
        self.connected = True

    def disconnect(self):
        self.connected = False

    def import_jg_data(self, pdf_name, data):
        return 999


def test_import_endpoint_monkeypatched(monkeypatch):
    # Patch parse_pdf_file to return a predictable dict
    logger.info("test_import_endpoint_monkeypatched: 开始设置")
    print("[测试] 应用 monkeypatch：parse_pdf_file 和 StructuredDataImporter")
    def fake_parse(pdf_path):
        return {
            'file_name': 'TEST.pdf',
            'period_start': '2024-01-01',
            'period_end': '2024-01-31',
            'payment_to_you': '123.45',
            'sales': {'subtotal': 100.0}
        }

    monkeypatch.setattr('backend.app.api.v2.routes.parse_pdf_file', fake_parse)
    monkeypatch.setattr('backend.app.api.v2.routes.StructuredDataImporter', lambda: DummyImporter())
    logger.info("Monkeypatches 已应用")
    print("[测试] Monkeypatch 应用完成")

    # Optional breakpoint: set environment variable TEST_BREAKPOINT=1 to stop here
    if os.getenv('TEST_BREAKPOINT') == '1':
        print('[测试] 断点触发（环境变量 TEST_BREAKPOINT=1）')
        import pdb
        pdb.set_trace()

    req = ImportRequest(pdf_path='somewhere/TEST.pdf')
    print(f"[测试] 调用 import_pdf，pdf_path={req.pdf_path}")
    resp = import_pdf(req, user={'id': 'dev'})
    print(f"[测试] import_pdf 返回：success={resp.success}, result={getattr(resp, 'result', None)}")
    logger.info("test_import_endpoint_monkeypatched: 执行完成")

    assert resp.success is True, 'import_pdf 应返回 success True'
    assert resp.result['statement_id'] == 999, '期望 DummyImporter 返回 999'
