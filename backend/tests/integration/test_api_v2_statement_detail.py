import sys
from pathlib import Path
project_root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(project_root))

from backend.app.api.v2.routes import get_statement_detail

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FakeDB:
    """伪造 DB，用于返回固定的完整对账单数据"""
    def __init__(self, data_map):
        self.data_map = data_map


class FakeDBRowStatement:
    def __init__(self, id, pdf_name, statement_period, payment_to_you):
        self.id = id
        self.pdf_name = pdf_name
        self.statement_period = statement_period
        self.payment_to_you = payment_to_you
        from datetime import datetime
        self.created_at = datetime.now()


class FakeDBRowSection:
    def __init__(self, id, statement_id, section_name, data):
        self.id = id
        self.statement_id = statement_id
        self.section_name = section_name
        self.data = data


def test_get_statement_detail_monkeypatched():
    # 准备伪造数据：包含 statement 行和对应的 section_data
    stmt = FakeDBRowStatement(42, 'SAMPLE.pdf', '2024-05-01 - 2024-05-31', '500.00')
    section_header = FakeDBRowSection(1, 42, 'header', '{"统计区间": "2024-05-01 - 2024-05-31"}')
    section_sales = FakeDBRowSection(2, 42, 'sales', '{"总计": 123.45}')

    # FakeDB 支持根据传入的 model 类型返回相应的查询对象
    class FakeDBForDetail:
        def __init__(self, stmt_row, sections):
            self.stmt_row = stmt_row
            self.sections = sections

        def query(self, model):
            # 根据 model 的类名判断返回内容
            class Q:
                def __init__(self, stmt_row, sections, model):
                    self.stmt_row = stmt_row
                    self.sections = sections
                    self.model = model

                def filter(self, *args, **kwargs):
                    return self

                def first(self):
                    # Statement 查询返回单条
                    return self.stmt_row

                def all(self):
                    # SectionData 查询返回列表
                    return self.sections

                # 支持 chained calls used in code
                def order_by(self, *args, **kwargs):
                    return self

                def limit(self, n):
                    return self

                def offset(self, o):
                    return self

            return Q(self.stmt_row, self.sections, model)

    fake_db = FakeDBForDetail(stmt, [section_header, section_sales])

    print('[测试] 开始调用 get_statement_detail')
    resp = get_statement_detail(42, db=fake_db, user={'id': 'tester'})
    print(f"[测试] get_statement_detail 返回: {resp}")

    assert resp['success'] is True
    assert resp['item']['id'] == 42
    print('[测试] get_statement_detail 测试通过')
