# 数据库设计详细说明

> **适用阶段**: Phase 3 - Web开发
> **数据库**: PostgreSQL 15+
> **ORM**: SQLAlchemy 2.0
> **最后更新**: 2025-12-16

---

## 🗄️ 核心表结构（8张表）

### 设计原则
- **规范化**: 遵循第三范式（3NF），减少数据冗余
- **扩展性**: 使用JSONB存储未知字段
- **完整性**: 外键约束 + 级联删除
- **审计**: 所有表包含created_at，主表包含updated_at
- **防重**: 使用file_hash防止重复上传

---

### 1. users - 用户表

```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 索引
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_username ON users(username);
```

**字段说明**:
- `id`: 自增主键
- `username`: 用户名，唯一
- `email`: 邮箱，唯一，用于登录
- `password_hash`: 密码哈希（使用bcrypt）
- `created_at`: 创建时间
- `updated_at`: 最后更新时间

---

### 2. statements - 报表主表

```sql
CREATE TABLE statements (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    filename VARCHAR(255) NOT NULL,
    file_hash VARCHAR(64) UNIQUE NOT NULL,  -- MD5防重复
    statement_date DATE NOT NULL,
    total_sales DECIMAL(12,2),
    total_refunds DECIMAL(12,2),
    total_fees DECIMAL(12,2),
    net_amount DECIMAL(12,2),
    status VARCHAR(20) DEFAULT 'pending',  -- pending/processing/completed/failed
    extra_fields JSONB,  -- 存储未知字段
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 索引
CREATE INDEX idx_statements_user_id ON statements(user_id);
CREATE INDEX idx_statements_date ON statements(statement_date);
CREATE INDEX idx_statements_status ON statements(status);
CREATE UNIQUE INDEX idx_statements_file_hash ON statements(file_hash);
```

**字段说明**:
- `file_hash`: MD5哈希，防止重复上传
- `statement_date`: 报表日期（从PDF文件名提取）
- `total_sales`: 总销售额
- `total_refunds`: 总退款额
- `total_fees`: 总费用
- `net_amount`: 净收入（sales - refunds - fees）
- `status`: 处理状态
  - `pending`: 等待处理
  - `processing`: 处理中
  - `completed`: 处理完成
  - `failed`: 处理失败
- `extra_fields`: JSONB字段，存储未知字段（扩展性）

---

### 3. sales_details - 销售明细

```sql
CREATE TABLE sales_details (
    id SERIAL PRIMARY KEY,
    statement_id INTEGER REFERENCES statements(id) ON DELETE CASCADE,
    order_id VARCHAR(50),
    product_name VARCHAR(255),
    quantity INTEGER,
    unit_price DECIMAL(12,2),
    total_amount DECIMAL(12,2),
    currency VARCHAR(3) DEFAULT 'USD',
    sale_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 索引
CREATE INDEX idx_sales_statement_id ON sales_details(statement_id);
CREATE INDEX idx_sales_order_id ON sales_details(order_id);
CREATE INDEX idx_sales_date ON sales_details(sale_date);
```

**字段说明**:
- `statement_id`: 关联到statements表
- `order_id`: 订单ID（Walmart订单号）
- `product_name`: 商品名称
- `quantity`: 数量
- `unit_price`: 单价
- `total_amount`: 总金额（quantity × unit_price）
- `currency`: 币种（默认USD）
- `sale_date`: 销售日期

---

### 4. refund_details - 退款明细

```sql
CREATE TABLE refund_details (
    id SERIAL PRIMARY KEY,
    statement_id INTEGER REFERENCES statements(id) ON DELETE CASCADE,
    order_id VARCHAR(50),
    refund_amount DECIMAL(12,2),
    refund_reason VARCHAR(255),
    refund_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 索引
CREATE INDEX idx_refunds_statement_id ON refund_details(statement_id);
CREATE INDEX idx_refunds_order_id ON refund_details(order_id);
CREATE INDEX idx_refunds_date ON refund_details(refund_date);
```

**字段说明**:
- `order_id`: 原订单ID
- `refund_amount`: 退款金额
- `refund_reason`: 退款原因（从PDF提取或用户输入）
- `refund_date`: 退款日期

---

### 5. adjustments - 调整费用

```sql
CREATE TABLE adjustments (
    id SERIAL PRIMARY KEY,
    statement_id INTEGER REFERENCES statements(id) ON DELETE CASCADE,
    adjustment_type VARCHAR(50),
    amount DECIMAL(12,2),
    description TEXT,
    adjustment_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 索引
CREATE INDEX idx_adjustments_statement_id ON adjustments(statement_id);
CREATE INDEX idx_adjustments_type ON adjustments(adjustment_type);
CREATE INDEX idx_adjustments_date ON adjustments(adjustment_date);
```

**字段说明**:
- `adjustment_type`: 调整类型（如：promotion, penalty, correction）
- `amount`: 调整金额（可正可负）
- `description`: 详细说明
- `adjustment_date`: 调整日期

---

### 6. wfs_fees - WFS服务费

```sql
CREATE TABLE wfs_fees (
    id SERIAL PRIMARY KEY,
    statement_id INTEGER REFERENCES statements(id) ON DELETE CASCADE,
    fee_type VARCHAR(50),
    amount DECIMAL(12,2),
    description TEXT,
    fee_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 索引
CREATE INDEX idx_wfs_fees_statement_id ON wfs_fees(statement_id);
CREATE INDEX idx_wfs_fees_type ON wfs_fees(fee_type);
CREATE INDEX idx_wfs_fees_date ON wfs_fees(fee_date);
```

**字段说明**:
- `fee_type`: 费用类型（如：storage, fulfillment, shipping）
- `amount`: 费用金额
- `description`: 费用说明
- `fee_date`: 费用日期

---

### 7. other_activities - 其他活动

```sql
CREATE TABLE other_activities (
    id SERIAL PRIMARY KEY,
    statement_id INTEGER REFERENCES statements(id) ON DELETE CASCADE,
    activity_type VARCHAR(50),
    amount DECIMAL(12,2),
    description TEXT,
    activity_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 索引
CREATE INDEX idx_activities_statement_id ON other_activities(statement_id);
CREATE INDEX idx_activities_type ON other_activities(activity_type);
CREATE INDEX idx_activities_date ON other_activities(activity_date);
```

**字段说明**:
- `activity_type`: 活动类型（如：transfer, bonus, other）
- `amount`: 金额
- `description`: 活动说明
- `activity_date`: 活动日期

---

### 8. upload_logs - 上传日志

```sql
CREATE TABLE upload_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    filename VARCHAR(255),
    file_size INTEGER,
    upload_status VARCHAR(20),  -- success/failed
    error_message TEXT,
    processing_time FLOAT,  -- 秒
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 索引
CREATE INDEX idx_upload_logs_user_id ON upload_logs(user_id);
CREATE INDEX idx_upload_logs_status ON upload_logs(upload_status);
CREATE INDEX idx_upload_logs_created_at ON upload_logs(created_at);
```

**字段说明**:
- `file_size`: 文件大小（字节）
- `upload_status`: 上传状态（success/failed）
- `error_message`: 错误信息（失败时记录）
- `processing_time`: 处理时长（秒）

---

## 📊 ER关系图

```
users (1) ──< (N) statements
                  │
                  ├──< sales_details
                  ├──< refund_details
                  ├──< adjustments
                  ├──< wfs_fees
                  └──< other_activities

users (1) ──< (N) upload_logs
```

**关系说明**:
- 一个用户可以有多个报表（1:N）
- 一个报表可以有多个明细记录（1:N）
- 所有明细表通过`statement_id`外键关联
- 级联删除：删除报表时自动删除所有明细

---

## 🔧 数据库约束

### 金额字段
- **类型**: `DECIMAL(12,2)`
- **范围**: -999,999,999.99 到 999,999,999.99
- **精度**: 2位小数
- **说明**: 支持到亿级金额

### 币种
- **统一**: `USD`（美元）
- **扩展**: 如需支持多币种，修改为ENUM类型

### 时间戳
- **created_at**: 所有表都有，记录创建时间
- **updated_at**: 主表有，记录最后更新时间
- **自动更新**: 使用触发器自动更新updated_at

```sql
-- 自动更新updated_at触发器
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 应用到statements表
CREATE TRIGGER update_statements_updated_at
    BEFORE UPDATE ON statements
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- 应用到users表
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
```

### 外键约束
- **ON DELETE CASCADE**: 删除主表时级联删除明细
- **示例**: 删除statement时，自动删除所有sales_details
- **注意**: 慎用，确保业务逻辑正确

### 唯一索引
- `users.username` - 防止重复用户名
- `users.email` - 防止重复邮箱
- `statements.file_hash` - 防止重复上传

---

## 🔍 常用查询示例

### 1. 查询用户的所有报表
```sql
SELECT
    s.id,
    s.filename,
    s.statement_date,
    s.total_sales,
    s.net_amount,
    s.status
FROM statements s
WHERE s.user_id = ?
ORDER BY s.statement_date DESC;
```

### 2. 查询报表的所有销售明细
```sql
SELECT
    sd.order_id,
    sd.product_name,
    sd.quantity,
    sd.unit_price,
    sd.total_amount,
    sd.sale_date
FROM sales_details sd
WHERE sd.statement_id = ?
ORDER BY sd.sale_date DESC;
```

### 3. 统计月度销售汇总
```sql
SELECT
    DATE_TRUNC('month', statement_date) AS month,
    SUM(total_sales) AS total_sales,
    SUM(total_refunds) AS total_refunds,
    SUM(total_fees) AS total_fees,
    SUM(net_amount) AS net_amount
FROM statements
WHERE user_id = ?
    AND statement_date BETWEEN ? AND ?
GROUP BY DATE_TRUNC('month', statement_date)
ORDER BY month DESC;
```

### 4. 查找重复上传的文件
```sql
SELECT
    file_hash,
    COUNT(*) AS count,
    ARRAY_AGG(filename) AS filenames
FROM statements
GROUP BY file_hash
HAVING COUNT(*) > 1;
```

### 5. 查询处理失败的报表
```sql
SELECT
    s.id,
    s.filename,
    s.created_at,
    ul.error_message
FROM statements s
LEFT JOIN upload_logs ul ON s.filename = ul.filename
WHERE s.status = 'failed'
ORDER BY s.created_at DESC;
```

---

## 🚀 性能优化

### 索引策略
1. **主键索引**: 自动创建（id）
2. **外键索引**: 手动创建（user_id, statement_id）
3. **查询索引**: 根据常用查询创建（date, status）
4. **唯一索引**: 防止重复（file_hash, email）

### 分区策略（可选，大数据量时）
```sql
-- 按日期分区statements表
CREATE TABLE statements (
    -- ... 字段定义
) PARTITION BY RANGE (statement_date);

-- 创建分区
CREATE TABLE statements_2025 PARTITION OF statements
    FOR VALUES FROM ('2025-01-01') TO ('2026-01-01');

CREATE TABLE statements_2024 PARTITION OF statements
    FOR VALUES FROM ('2024-01-01') TO ('2025-01-01');
```

### 查询优化
1. **使用EXPLAIN分析查询**: `EXPLAIN ANALYZE SELECT ...`
2. **避免SELECT ***: 只查询需要的字段
3. **使用JOIN代替子查询**: JOIN通常更快
4. **分页查询**: 使用LIMIT和OFFSET

---

## 🔐 安全注意事项

### 1. SQL注入防护
```python
# ❌ 错误：拼接SQL
query = f"SELECT * FROM users WHERE username = '{username}'"

# ✅ 正确：使用参数化查询
query = "SELECT * FROM users WHERE username = :username"
result = db.session.execute(query, {"username": username})
```

### 2. 密码存储
```python
import bcrypt

# 存储密码
password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

# 验证密码
is_valid = bcrypt.checkpw(password.encode('utf-8'), stored_hash)
```

### 3. 敏感数据加密
- 数据库连接字符串 → 环境变量
- API密钥 → 环境变量或密钥管理服务
- 用户数据 → 考虑字段级加密（如：银行账号）

---

## 📖 SQLAlchemy模型示例

### Statement模型
```python
from sqlalchemy import Column, Integer, String, Date, Numeric, TIMESTAMP, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from datetime import datetime

class Statement(Base):
    __tablename__ = 'statements'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'))
    filename = Column(String(255), nullable=False)
    file_hash = Column(String(64), unique=True, nullable=False)
    statement_date = Column(Date, nullable=False)
    total_sales = Column(Numeric(12, 2))
    total_refunds = Column(Numeric(12, 2))
    total_fees = Column(Numeric(12, 2))
    net_amount = Column(Numeric(12, 2))
    status = Column(String(20), default='pending')
    extra_fields = Column(JSONB)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    user = relationship('User', back_populates='statements')
    sales_details = relationship('SalesDetail', back_populates='statement', cascade='all, delete-orphan')
    refund_details = relationship('RefundDetail', back_populates='statement', cascade='all, delete-orphan')
```

---

**END OF DB-DESIGN.MD**

*配置版本: v1.0 | 创建时间: 2025-12-16 | 文件行数: 约500行*
