import sys
from pathlib import Path
project_root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(project_root))

from backend.app.api.v2.routes import list_statements
from backend.app.api.v2.schemas import StatementsListResponse

import logging

# 简单日志配置，方便在测试输出中看到中文信息
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FakeStatement:
    """用于测试的简单伪造 ORM 对象"""
    def __init__(self, id, pdf_name, statement_period, payment_to_you):
        self.id = id
        self.pdf_name = pdf_name
        self.statement_period = statement_period
        self.payment_to_you = payment_to_you
        # created_at 用不到，但 ORM 查询可能期望该属性存在
        from datetime import datetime
        self.created_at = datetime.now()


class FakeDB:
    """用于测试的简单伪造 DB 会话对象，支持 query(...).count() 和 .all()"""
    def __init__(self, items):
        self._items = items

    def query(self, model):
        # 返回一个简单的 QueryBuilder-like 对象
        class Q:
            def __init__(self, items):
                self._items = items

            def count(self):
                return len(self._items)

            def order_by(self, *args, **kwargs):
                return self

            def limit(self, n):
                self._limit = n
                return self

            def offset(self, o):
                self._offset = o
                return self

            def all(self):
                # 模拟切片
                start = getattr(self, '_offset', 0)
                end = start + getattr(self, '_limit', len(self._items))
                return self._items[start:end]

        return Q(self._items)


def test_list_statements_monkeypatched_prints():
    """测试 `list_statements` 路由的基本行为并打印中文输出点"""
    # 准备伪造数据：3 条对账单
    items = [
        FakeStatement(1, 'A.pdf', '2024-01-01 - 2024-01-31', '100.00'),
        FakeStatement(2, 'B.pdf', '2024-02-01 - 2024-02-28', '200.00'),
        FakeStatement(3, 'C.pdf', '2024-03-01 - 2024-03-31', '300.00'),
    ]

    fake_db = FakeDB(items)

    # 打印一个中文信息点，指示测试开始
    print('[测试] 开始调用 list_statements（使用 FakeDB）')

    # 直接调用 handler，传入 fake_db 和简化的 user
    resp = list_statements(limit=2, offset=0, db=fake_db, user={'id': 'tester'})

    # 打印返回结果以便观察
    print(f"[测试] 返回 success={resp.success}, total={resp.total}, items_count={len(resp.items or [])}")

    assert isinstance(resp, StatementsListResponse)
    assert resp.success is True
    assert resp.total == 3
    assert len(resp.items) == 2

    print('[测试] list_statements 测试通过')
