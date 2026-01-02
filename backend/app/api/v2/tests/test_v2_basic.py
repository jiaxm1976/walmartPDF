import sys
import pathlib

# 确保从仓库根导入 `backend` 包
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[5]))

import asyncio
from backend.app.api.v2.routes import v2_health


def test_v2_health():
    body = asyncio.run(v2_health())
    assert isinstance(body, dict)
    assert body.get('version') == 'v2'
