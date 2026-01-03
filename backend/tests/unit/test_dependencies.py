import sys
from pathlib import Path
project_root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(project_root))

import os
import json
import hmac
import hashlib
import base64

from backend.app.api.v2.dependencies import _b64url_encode, _b64url_decode
from backend.app.api.v2.dependencies import _verify_hs256, get_current_user
from types import SimpleNamespace
import pytest


def make_jwt(payload: dict, secret: str = "secret-key") -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    hb = _b64url_encode(json.dumps(header).encode())
    pb = _b64url_encode(json.dumps(payload).encode())
    signing_input = f"{hb}.{pb}".encode()
    sig = hmac.new(secret.encode(), signing_input, hashlib.sha256).digest()
    sb = _b64url_encode(sig)
    return f"{hb}.{pb}.{sb}"


def make_request_with_auth(token: str):
    return SimpleNamespace(headers={"authorization": f"Bearer {token}"})


def test_test_token_allows_dev_user():
    req = make_request_with_auth("test-token")
    user = get_current_user(req)
    assert user["id"] == "dev"


def test_valid_jwt_returns_payload():
    payload = {"id": "user1", "roles": ["viewer"]}
    token = make_jwt(payload)
    req = make_request_with_auth(token)
    user = get_current_user(req)
    assert user["id"] == "user1"


def test_invalid_jwt_raises():
    payload = {"id": "user1"}
    token = make_jwt(payload, secret="wrong-secret")
    req = make_request_with_auth(token)
    with pytest.raises(Exception):
        get_current_user(req)
