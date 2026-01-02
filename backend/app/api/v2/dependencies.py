from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer(auto_error=False)


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    # 开发阶段简易认证：无 token 或 token == 'devtoken' 都视为 dev 用户
    if credentials is None:
        return {"username": "dev", "role": "admin"}
    token = credentials.credentials
    if token == "devtoken":
        return {"username": "dev", "role": "admin"}
    raise HTTPException(status_code=401, detail="Invalid auth token")
