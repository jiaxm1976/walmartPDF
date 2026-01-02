import sys
import pathlib
import asyncio
import uuid

# 确保从仓库根导入 `backend` 包
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[5]))

from backend.main import app
import requests
import subprocess
import socket
import time


def _get_free_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('127.0.0.1', 0))
    addr, port = s.getsockname()
    s.close()
    return port


def test_import_parsed_integration():
    parsed_path = 'backend/tests/output/manual_run_venv2/parsed_data.json'
    unique_name = f'integration_{uuid.uuid4().hex}.pdf'
    payload = {'parsed_file_path': parsed_path, 'pdf_name': unique_name}

    port = _get_free_port()
    cmd = [sys.executable, '-m', 'uvicorn', 'backend.main:app', '--host', '127.0.0.1', '--port', str(port), '--log-level', 'warning']

    env = None
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)

    try:
        # wait for server to be up
        url = f'http://127.0.0.1:{port}/api/v2/health'
        for _ in range(30):
            try:
                r = requests.get(url, timeout=1)
                if r.status_code == 200:
                    break
            except Exception:
                time.sleep(0.2)

        # call import_parsed
        url = f'http://127.0.0.1:{port}/api/v2/import_parsed'
        headers = {'Authorization': 'Bearer devtoken'}
        r = requests.post(url, json=payload, headers=headers, timeout=10)
        assert r.status_code == 200, r.text
        body = r.json()
        assert body.get('success') is True
        assert 'statement_id' in body.get('result')

    finally:
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except Exception:
            proc.kill()
