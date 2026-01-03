import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(project_root))

import asyncio

from backend.app.api.v2.routes import v2_health_check


def test_api_v2_health():
    data = asyncio.get_event_loop().run_until_complete(v2_health_check())
    assert isinstance(data, dict)
    assert data.get("status") == "ok"
