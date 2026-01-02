# API v2 安全指南

**版本**：1.0 | **日期**：2026-01-02 | **分类**：生产级安全规范

---

## 1. 认证与授权

### 1.1 身份验证机制

**JWT Bearer Token**（推荐用于生产）
```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Token 配置**：
- 算法：HS256
- 有效期：1 小时（生产）/ 24 小时（开发）
- 签名密钥：环境变量 `JWT_SECRET`（生产强制，≥ 32 字符）
- Refresh Token：7 天，用于刷新 Access Token

**实现示例**：
```python
from fastapi_jwt_auth import AuthJWT

@app.post("/api/v2/auth/login")
async def login(credentials: LoginRequest, Authorize: AuthJWT = Depends()):
    # 验证凭证
    access_token = Authorize.create_access_token(
        subject=user.id,
        expires_time=timedelta(hours=1)
    )
    return {"access_token": access_token}

@app.get("/api/v2/health")
async def health(Authorize: AuthJWT = Depends()):
    Authorize.jwt_required()  # 验证 token
    return {"status": "ok"}
```

---

### 1.2 RBAC（角色权限控制）

**角色定义**：
```python
class Role(str, Enum):
    VIEWER = "viewer"      # 仅读权限
    EDITOR = "editor"      # 读 + 写
    ADMIN = "admin"        # 全权
```

**权限矩阵**：

| 端点 | Viewer | Editor | Admin |
|------|--------|--------|-------|
| `GET /api/v2/statements` | ✅ | ✅ | ✅ |
| `GET /api/v2/statements/{id}` | ✅* | ✅* | ✅ |
| `PATCH /api/v2/statements/{id}/...` | ❌ | ✅ | ✅ |
| `POST /api/v2/import` | ✅ | ✅ | ✅ |
| `POST /api/v2/statements/{id}/export` | ❌ | ✅ | ✅ |
| `POST /api/v2/statements/{id}/approve` | ❌ | ✅ | ✅ |
| `DELETE /api/v2/statements/{id}` | ❌ | ❌ | ✅ |

*仅能访问自己上传的数据

**权限检查装饰器**：
```python
def require_permission(permission: str):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get("current_user")
            if not has_permission(current_user.role, permission):
                raise HTTPException(status_code=403, detail="Forbidden")
            return await func(*args, **kwargs)
        return wrapper
    return decorator
```

---

## 2. 数据保护

### 2.1 敏感字段脱敏

**脱敏规则**：
```python
SENSITIVE_FIELDS = {
    "ssn": {"pattern": r"\d{3}-\d{2}-(\d{4})", "mask": "XXX-XX-$1"},
    "account_number": {"pattern": r"(\d{4})", "mask": "****$1"},
    "routing_number": {"pattern": r"(\d{3})\d{6}", "mask": "$1***"},
}
```

**实现**：
```python
def mask_sensitive_fields(data: dict) -> dict:
    for field, rule in SENSITIVE_FIELDS.items():
        if field in data:
            data[field] = re.sub(rule["pattern"], rule["mask"], data[field])
    return data
```

---

### 2.2 审计日志

**记录内容**：
- 操作时间、用户 ID、操作类型
- 变更前后的字段值
- 源 IP 地址、User-Agent

**实现**：
```python
@app.middleware("http")
async def audit_middleware(request: Request, call_next):
    if request.method in ["POST", "PATCH", "DELETE"]:
        user_id = request.user.id
        body = await request.body()
        
        response = await call_next(request)
        
        # 记入 change_log 表
        log_entry = ChangeLog(
            user_id=user_id,
            operation=request.method,
            resource=request.url.path,
            changes=body,
            source_ip=request.client.host,
            timestamp=datetime.utcnow()
        )
        db.add(log_entry)
        await db.commit()
    
    return response
```

---

### 2.3 导出安全

**预签名 URL**：
```python
@app.post("/api/v2/statements/{id}/export")
async def export(id: int, export_req: ExportRequest):
    # 后台生成导出文件
    task = schedule_export_task(id, export_req.format)
    
    # 返回临时 URL（1 小时有效期）
    signed_url = generate_signed_url(
        file_path=task.output_path,
        expires_in=3600
    )
    return {"download_url": signed_url, "expires_in": 3600}
```

**签名验证**：
```python
def verify_signed_url(token: str, path: str):
    payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    if payload["path"] != path or payload["exp"] < time.time():
        raise HTTPException(status_code=401, detail="Invalid or expired URL")
    return True
```

---

## 3. API 安全

### 3.1 输入验证

**Pydantic 验证**：
```python
class ImportRequest(BaseModel):
    pdf_path: str = Field(..., regex=r"^[a-zA-Z0-9/_\-\.]+\.pdf$")
    client_request_id: str = Field(..., max_length=50)
    
    @validator("pdf_path")
    def validate_pdf_path(cls, v):
        # 防止目录遍历
        if ".." in v or v.startswith("/"):
            raise ValueError("Invalid PDF path")
        return v
```

**文件上传限制**：
- 仅允许 `.pdf` 文件
- 最大 100 MB
- 恶意内容扫描（病毒、隐写）

---

### 3.2 HTTPS 强制

```python
@app.middleware("http")
async def https_middleware(request: Request, call_next):
    # 生产环境强制 HTTPS
    if os.getenv("ENV") == "production":
        proto = request.headers.get("X-Forwarded-Proto", "http")
        if proto != "https":
            raise HTTPException(status_code=403, detail="HTTPS required")
    
    return await call_next(request)
```

---

### 3.3 CORS 配置

**生产白名单**：
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://walmart-pdfs.example.com"],  # 生产
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH"],
    allow_headers=["Content-Type", "Authorization"],
    max_age=3600,
)
```

---

### 3.4 速率限制

**限流规则**：
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/api/v2/import")
@limiter.limit("10/minute")
async def import_pdf(request: Request, ...):
    pass

@app.post("/api/v2/statements/{id}/export")
@limiter.limit("5/minute")
async def export(request: Request, ...):
    pass
```

---

### 3.5 错误信息脱敏

**开发模式**（完整错误）：
```json
{"error": "Database connection failed: host=db, port=5432"}
```

**生产模式**（通用错误）：
```json
{"error": "An error occurred. Please contact support."}
```

**实现**：
```python
@app.exception_handler(Exception)
async def exception_handler(request: Request, exc: Exception):
    logger.error(f"Error: {exc}", exc_info=True)  # 记录完整信息
    
    if os.getenv("ENV") == "production":
        return JSONResponse(
            status_code=500,
            content={"error": "Internal server error"}
        )
    else:
        return JSONResponse(
            status_code=500,
            content={"error": str(exc)}
        )
```

---

## 4. 加密与编码

### 4.1 密钥管理

**环境变量**（不能提交到版本控制）：
```bash
# .env (生产)
JWT_SECRET=your-very-secret-key-min-32-chars
DATABASE_URL=postgresql://user:pass@db:5432/walmart
API_KEY=api-key-for-third-party-services
```

**密钥轮换**：
- JWT 密钥每 6 个月轮换
- 支持多个有效密钥（旧 + 新）用于过渡期
- 记录密钥版本与变更时间

---

### 4.2 传输加密

```python
# 强制 HTTPS + HSTS
from fastapi.middleware import Middleware

app.add_middleware(
    Middleware(
        middleware.trustedhost.TrustedHostMiddleware,
        allowed_hosts=["walmart-pdfs.example.com"]
    )
)

app.add_middleware(
    Middleware(
        middleware.httpsredirect.HTTPSRedirectMiddleware
    )
)
```

---

## 5. 监测与审计

### 5.1 日志记录

**生产级日志配置**：
```python
import logging

logger = logging.getLogger(__name__)

# 不记录敏感信息
def safe_log(message: str, **kwargs):
    safe_kwargs = {k: v for k, v in kwargs.items() 
                   if k not in SENSITIVE_FIELDS}
    logger.info(message, extra=safe_kwargs)
```

### 5.2 监测告警

**关键事件告警**：
- 登录失败 ≥ 5 次（可能被暴力破解）
- 导出 > 100 条记录（可能数据泄露）
- 无效 token ≥ 10 次（可能被攻击）
- 来自不同 IP 的多次请求

---

## 6. 依赖关系安全

### 6.1 依赖检查

```bash
# 定期审计依赖
pip install pip-audit
pip-audit

# 更新依赖
pip install --upgrade pip
```

### 6.2 已知漏洞排查

- 使用 GitHub Dependabot 自动检查
- 定期更新关键库（FastAPI, SQLAlchemy, Pydantic）

---

## 7. 部署安全

### 7.1 环境隔离

- 开发 ≠ 测试 ≠ 生产
- 使用 `.env` 文件隔离配置
- 生产不允许调试模式

### 7.2 数据库安全

```python
# SQLAlchemy connection string with SSL
SQLALCHEMY_DATABASE_URI = (
    "postgresql://user:pass@db:5432/walmart?"
    "sslmode=require"
)
```

---

## 8. 清单

### 上线前检查

- [ ] JWT Secret ≥ 32 字符且随机
- [ ] HTTPS 启用、HSTS 配置
- [ ] CORS 白名单配置
- [ ] 敏感字段脱敏规则完整
- [ ] 审计日志记录完整
- [ ] 速率限制部署
- [ ] 错误信息脱敏
- [ ] 环境变量不提交到 Git
- [ ] 依赖包扫描通过
- [ ] 安全测试通过

---

**维护者**：安全团队  
**最后更新**：2026-01-02
