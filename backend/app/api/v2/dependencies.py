from fastapi import HTTPException, Request
import os
import hmac
import hashlib
import base64
import json


def _b64url_decode(inp: str) -> bytes:
    """Decode a base64-url string to bytes.

    JWT uses base64url encoding without padding. This helper adds the
    correct padding and decodes to raw bytes.
    """
    padding = '=' * ((4 - len(inp) % 4) % 4)
    return base64.urlsafe_b64decode(inp + padding)


def _b64url_encode(inp: bytes) -> str:
    """Encode bytes as base64-url string without padding.

    Useful for creating test JWTs when you need to sign header/payload.
    """
    return base64.urlsafe_b64encode(inp).rstrip(b"=").decode()


def _verify_hs256(jwt_token: str, secret: str) -> dict | None:
    """Verify a simple HS256 JWT and return its payload as a dict.

    This is a minimal JWT checker (for learning / dev use). It does NOT
    implement expiration (`exp`) checks or support other algorithms.

    Steps:
    1. split token into header.payload.signature (base64url parts)
    2. compute HMAC-SHA256 over header.payload with the shared secret
    3. compare signature with constant-time compare
    4. decode and return JSON payload on success

    Returns payload dict on success, or `None` on failure.
    """
    try:
        header_b64, payload_b64, sig_b64 = jwt_token.split('.')
    except ValueError:
        return None

    signing_input = f"{header_b64}.{payload_b64}".encode()
    try:
        sig = _b64url_decode(sig_b64)
    except Exception:
        return None

    expected = hmac.new(secret.encode(), signing_input, hashlib.sha256).digest()
    if not hmac.compare_digest(expected, sig):
        # signature mismatch
        return None

    try:
        payload = json.loads(_b64url_decode(payload_b64))
    except Exception:
        return None
    return payload


def get_current_user(request: Request):
    """FastAPI 依赖：从 `Authorization` 头解析并验证用户身份。

    使用方法（在路由中）：
        user = Depends(get_current_user)

    实现要点（便于初学者理解）：
    - 从 `Authorization` 头读取 Bearer token；
    - 如果 token 是开发用的 `test-token`，直接返回一个示例用户（便于本地测试）；
    - 否则使用 `_verify_hs256` 进行简单签名校验（使用环境变量 `API_JWT_SECRET`）；
    - 若校验失败则抛出 401 错误。

    注意：生产中请使用成熟库（例如 `python-jose`）并校验 `exp`、`aud` 等字段。
    """
    auth = request.headers.get("authorization") or request.headers.get("Authorization")
    if not auth:
        raise HTTPException(status_code=401, detail="Missing Authorization header")

    parts = auth.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid Authorization header format")

    token = parts[1]

    # 开发/测试模式快捷令牌：避免每次手工签发 JWT
    if token == "test-token":
        return {"id": "dev", "roles": ["admin"]}

    # 从环境变量读取签名密钥，未设置时使用默认（仅限开发）
    secret = os.environ.get("API_JWT_SECRET", "secret-key")
    payload = _verify_hs256(token, secret)
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    # 返回载荷（通常包含 user id / roles 等）供路由使用
    return payload



