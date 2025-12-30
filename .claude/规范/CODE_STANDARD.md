# Python 代码规范指南 v1.0

> **适用范围**: 所有Python项目 | **日期**: 2025-12-26 | **基准**: text_formatter.py 最佳实践

---

## 📋 目录

1. [核心原则](#核心原则)
2. [文件和模块规范](#文件和模块规范)
3. [注释规范](#注释规范)
4. [常量管理规范](#常量管理规范)
5. [函数设计规范](#函数设计规范)
6. [数据结构规范](#数据结构规范)
7. [参数和返回值规范](#参数和返回值规范)
8. [异常处理规范](#异常处理规范)
9. [类型提示规范](#类型提示规范)
10. [日志记录规范](#日志记录规范)
11. [代码组织规范](#代码组织规范)
12. [测试编写规范](#测试编写规范)

---

## 🎯 核心原则

### 第一原则：可读性优先

**代码应该为人而写，而非仅为机器而写**

```
代码 = 30% 业务逻辑 + 70% 沟通和理解
      ↓          ↓
   机器可执行  人类易理解
```

### 第二原则：可维护性优先

**维护成本往往超过开发成本**

- 避免硬编码 → 使用常量
- 避免重复代码 → 提取为函数
- 避免复杂嵌套 → 拆分为步骤
- 集中管理配置 → 统一修改

### 第三原则：类型安全完整

**动态语言也需要类型保证**

- 参数需要类型提示
- 返回值需要类型标注
- 数据结构使用类而非dict
- IDE可以帮助发现类型错误

### 第四原则：错误处理优雅

**异常是一等公民，而非被隐藏的错误**

- 明确定义异常类型
- 详细的错误日志
- 合理的降级策略
- 不隐藏错误

---

## 📁 文件和模块规范

### 1. 文件头注释（必需）

**所有Python文件必须以文件头注释开头**

```python
# ============================================================
# 文件: <相对路径或文件名>
# 功能: <一句话核心功能描述>
# 作者: <开发者或团队名称>
# 创建时间: YYYY-MM-DD
# 最后修改: YYYY-MM-DD
# 依赖: <核心依赖库>
# 说明: <可选的补充说明，通常不超过2行>
# ============================================================
```

**示例：**

```python
# ============================================================
# 文件: utils/text_processor.py
# 功能: 文本格式化和清洗处理工具
# 作者: 开发团队
# 创建时间: 2025-12-01
# 最后修改: 2025-12-26
# 依赖: logging, typing, re
# 说明: 提供统一的文本处理接口，支持多种编码和格式
# ============================================================
```

**文件头注释的价值：**
- ✅ 快速定位文件功能
- ✅ 了解最后修改时间
- ✅ 追踪代码演进历史
- ✅ 识别所需依赖

### 2. 导入组织规范

**导入顺序遵循PEP 8标准**

```python
# 1️⃣ 标准库导入（Python内置）
import logging
import json
import os
from pathlib import Path
from typing import Optional, List, Dict, Tuple

# 2️⃣ 第三方库导入（pip安装）
import numpy as np
import pandas as pd
from requests import Session

# 3️⃣ 本地应用导入（同一项目）
from .models import User
from .services import AuthService
from ..utils import helpers
```

**导入的注释规范：**

```python
# 导入日志模块，用于记录程序运行状态和调试信息
import logging

# 导入类型提示模块
#   - Optional: 可选类型，表示值或None
#   - List: 列表类型
#   - Dict: 字典类型
#   - Tuple: 元组类型
from typing import Optional, List, Dict, Tuple

# 导入第三方数据处理库
import pandas as pd  # 数据框架操作
import numpy as np   # 数值计算
```

**导入组织的好处：**
- ✅ 快速定位依赖来源
- ✅ 便于修改依赖
- ✅ 避免循环导入
- ✅ 提高代码可读性

### 3. 模块结构规范

**规范的模块内部结构顺序：**

```
module.py
├─ 1. 文件头注释 (10行)
├─ 2. 模块级文档字符串 (可选, 5行)
├─ 3. 导入语句 (15-20行)
├─ 4. logger初始化 (3行)
├─ 5. 常量定义 (30-50行)
├─ 6. 数据类定义 (50-100行)
├─ 7. 公开函数 (100-200行)
├─ 8. 私有辅助函数 (50-100行)
├─ 9. 主程序块 (10-20行)
└─ 总计: ~500行（大模块应拆分）
```

**示例：**

```python
# ============================================================
# 文件: processor.py
# 功能: 数据处理核心模块
# ...
# ============================================================

"""模块级文档字符串

该模块提供了数据处理的核心功能，包括：
- 数据验证和清洗
- 格式转换和标准化
- 结果导出和报告

主要使用的模块：
- DataValidator: 数据验证器
- DataProcessor: 数据处理器

示例用法：
    >>> validator = DataValidator()
    >>> processor = DataProcessor()
    >>> result = processor.process(data)
"""

import logging
from typing import List, Dict

logger = logging.getLogger(__name__)

# 常量定义
MAX_BATCH_SIZE = 1000
DEFAULT_TIMEOUT = 30

# 数据类定义
from dataclasses import dataclass

@dataclass
class ProcessResult:
    success: bool
    data: List[Dict]

# 公开函数
def process_data(data: List[Dict]) -> ProcessResult:
    """处理数据"""
    pass

# 私有函数
def _validate_data(data: List[Dict]) -> bool:
    """验证数据"""
    pass

# 主程序块
if __name__ == "__main__":
    pass
```

---

## 💬 注释规范

### 1. 注释的基本原则

| 原则 | 说明 | ✅ 示例 | ❌ 反例 |
|-----|------|--------|--------|
| **解释"为什么"** | 说明为什么这样做 | # 使用UUID避免冲突 | # 转换为UUID |
| **关键逻辑处** | 复杂逻辑需要注释 | # 检查Y坐标容差 | x = x + 1 |
| **保持同步** | 修改代码时更新注释 | 注释与代码一致 | 注释陈旧过时 |
| **适度注释** | 不要过度注释 | 注释比例 60-80% | 注释比例 > 90% |
| **语言一致** | 同一文件风格统一 | 全中文或混用统一 | 混乱的中英混用 |

### 2. 注释分类

#### 📌 **文件和模块级注释**

```python
"""模块文档字符串

完整的模块说明，包括：
- 模块的主要功能
- 核心概念和算法
- 使用示例
- 相关模块或依赖关系

该模块负责处理JSON数据的验证和转换。
支持的转换类型包括：
  1. JSON到Python对象
  2. Python对象到JSON
  3. Schema验证

示例：
    >>> from json_processor import process
    >>> data = process('{"name": "John"}')
    >>> print(data.name)
    John
"""
```

#### 📌 **类级注释**

```python
class DataValidator:
    """数据验证器

    提供对各种数据格式的验证功能。

    使用dataclass的原因：
    - 自动生成__init__方法
    - 提供类型提示支持
    - 支持默认值和工厂函数
    - 自动生成__repr__方法

    属性说明：
        rules (List[Rule]): 验证规则列表
        strict_mode (bool): 是否使用严格验证模式
    """
    rules: List[Rule]
    strict_mode: bool = False
```

#### 📌 **函数级注释（最重要）**

```python
def process_file(
    file_path: str,
    encoding: str = "utf-8",
    max_lines: int = 10000
) -> Dict[str, Any]:
    """处理文件，返回结构化数据

    这是函数的简单描述。

    完整说明：
        该函数读取指定文件，进行数据验证和转换，
        最后返回结构化的结果字典。

    参数说明：
        file_path (str): 待处理文件的路径
                        必须指向存在的文件
                        支持相对路径和绝对路径
        encoding (str): 文件编码，默认utf-8
                       常见值：utf-8, gbk, latin-1
        max_lines (int): 最大读取行数，默认10000
                        用于限制内存使用
                        有效范围：1-1000000

    返回值：
        Dict[str, Any]: 处理结果字典
        - "status": "success" 或 "error"
        - "data": 实际数据或错误信息
        - "lines": 处理的行数
        - "warnings": 警告列表

    异常处理：
        FileNotFoundError: 文件不存在
        UnicodeDecodeError: 文件编码不匹配
        ValueError: 文件格式不支持或数据无效
        MemoryError: 文件过大，超出内存限制

    性能提示：
        - 大文件（>1GB）建议分批处理
        - 建议使用流式处理避免加载整个文件
        - 初次调用会加载schema，有初始化成本

    相关函数：
        - process_batch(): 批量处理多个文件
        - validate_file(): 仅验证文件格式
        - convert_format(): 转换文件格式

    示例：
        >>> result = process_file("data.csv")
        >>> if result["status"] == "success":
        ...     print(f"处理{result['lines']}行")
        ...     data = result["data"]
    """
```

**函数docstring的必需元素：**
- ✅ 简单描述（1行）
- ✅ 详细说明（3-5行）
- ✅ 参数说明（类型、含义、范围）
- ✅ 返回值说明（类型、结构、含义）
- ✅ 异常说明（何时抛出，什么类型）
- ✅ 使用示例（可运行的代码）

#### 📌 **行级注释**

```python
# ===== 第1步：验证输入 =====
# 检查文件是否存在，若不存在则记录日志并返回
if not os.path.exists(file_path):
    logger.warning(f"文件不存在: {file_path}")
    return None

# ===== 第2步：读取文件 =====
# 使用context manager自动关闭文件，避免资源泄漏
with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# 原因说明：某些PDF可能有非标准的行尾格式
# 使用strip()处理不同平台的换行符差异
lines = [line.strip() for line in lines if line.strip()]
```

**行级注释指南：**
- ✅ 注释关键决策点
- ✅ 解释非显然的代码
- ✅ 标记处理的特殊情况
- ✅ 说明性能优化的原因
- ❌ 不要重复代码本身说的话
- ❌ 不要注释显然的代码

### 3. 常见注释模板

#### **魔法数字解释**

```python
# 缓存过期时间：24小时 = 86400秒
CACHE_TIMEOUT = 86400

# 图像像素密度：标准屏幕 72DPI，PDF 300DPI
# PDF页面宽度(A4纸): 210mm = 595像素(72DPI) = 2480像素(300DPI)
PDF_PAGE_WIDTH_72DPI = 595

# Y坐标容差范围：15像素
# 原因：考虑到OCR识别的偏差，同一行的文本Y坐标可能相差15像素
Y_TOLERANCE = 15
```

#### **算法说明**

```python
# 使用指数退避算法进行重试
# 重试间隔序列：1s, 1s, 2s, 3s, 5s, 8s...（斐波那契数列）
# 优点：避免瞬时故障导致的重复失败，给系统恢复时间
# 总重试次数：6次，最长总等待时间：18秒
def exponential_backoff_retry(func, max_retries=6):
    ...
```

#### **特殊情况处理**

```python
# 特殊情况：当金额为0时，不显示货币符号
# 原因：避免显示"$0"导致的视觉混乱和用户困惑
# 标准格式应该是直接显示"0"或"N/A"
if amount == 0:
    return "N/A"
else:
    return f"${amount:.2f}"
```

---

## 🔧 常量管理规范

### 1. 常量定义位置

```
代码结构：

模块顶部（导入之后）
├─ 常量定义区域（第一优先级）
│  ├─ 业务常量（核心业务配置）
│  ├─ 技术常量（超时、重试次数）
│  ├─ 阈值常量（容差、限制值）
│  └─ 格式常量（正则表达式、格式字符串）
│
└─ 代码实现区域
   ├─ 数据类定义
   ├─ 函数实现
   └─ 主程序
```

**为什么常量要集中在顶部：**
- ✅ 便于查看所有可配置项
- ✅ 便于修改参数（集中地修改）
- ✅ 避免硬编码魔法数字散落代码中
- ✅ 提高代码可维护性

### 2. 常量命名规范

| 类型 | 规范 | 示例 | 说明 |
|-----|------|------|------|
| **模块常量** | `UPPER_CASE` | `MAX_RETRIES` | 全大写+下划线 |
| **枚举常量** | `UPPER_CASE` | `STATUS_PENDING` | 避免拼写错误 |
| **配置常量** | `DESCRIPTIVE_NAME` | `DATABASE_TIMEOUT` | 名称要自解释 |
| **版本号** | `VERSION_X_Y_Z` | `API_VERSION_2_0` | 包含版本信息 |

### 3. 常量分组规范

```python
# ============================================================
# 配置常量 - 按功能分组便于维护
# ============================================================

# 【业务相关常量】
# 核心业务配置，修改需要评估影响
PAYMENT_KEYWORD = "向您支付的金额"
PAYMENT_THRESHOLD = 500

# 【技术相关常量】
# 系统参数，调整影响性能和稳定性
DEFAULT_TIMEOUT = 30
MAX_RETRIES = 3

# 【阈值常量】
# 识别阈值，影响精确度和召回率
CONFIDENCE_THRESHOLD = 0.8
Y_TOLERANCE = 15

# 【格式常量】
# 数据格式定义
DATE_FORMAT = "%Y-%m-%d"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
```

### 4. 常量注释规范

```python
# 【含义说明】
# 缓存有效期设置为24小时
# 原因：平衡存储成本和数据新鲜度
# 调整建议：高频变化数据可设置为1小时，静态数据可设置为7天
CACHE_EXPIRY = 86400

# 【公式说明】
# Y坐标容差 = 单行高度的50%
# 计算：文本高度约30像素，容差应为15像素
# 影响：影响多列文本的行对齐识别
Y_TOLERANCE = 15

# 【依赖说明】
# 与PDF_PAGE_DPI紧密相关
# 若PDF DPI变化，需要同步调整此值
# A4纸宽度：210mm = 595像素(72DPI) = 2480像素(300DPI)
PDF_PAGE_WIDTH = 595  # 72DPI标准
```

---

## 🔨 函数设计规范

### 1. 函数签名规范

#### **参数设计原则**

```python
# ❌ 不好：参数过多，难以理解和维护
def process(a, b, c, d, e, f, g, h):
    pass

# ✅ 好：参数少且有意义
def process_file(
    file_path: str,
    encoding: str = "utf-8",
    validate: bool = True,
    max_size: int = 1024*1024
) -> ProcessResult:
    pass
```

**参数设计规则：**

| 规则 | 标准 | 说明 |
|-----|------|------|
| **参数个数** | ≤ 5个 | 必需参数≤3个，可选参数≤2个 |
| **参数顺序** | 必需→可选 | 必需参数在前，可选参数在后 |
| **参数命名** | 自解释 | 避免单字母（a, b），用full_name |
| **默认值** | 使用None | 可选参数必须有默认值 |
| **参数验证** | 函数开始处 | 验证后立即抛出异常 |

#### **参数过多的解决方案**

```python
# 问题：参数过多
def generate_report(
    data, format, theme, locale, timezone,
    include_charts, include_tables, include_summary
):
    pass

# 解决方案1：使用配置对象
@dataclass
class ReportConfig:
    format: str
    theme: str
    locale: str
    timezone: str
    include_charts: bool
    include_tables: bool
    include_summary: bool

def generate_report(data: List, config: ReportConfig) -> Report:
    pass

# 使用方式
config = ReportConfig(
    format="pdf",
    theme="dark",
    locale="en_US",
    timezone="UTC",
    include_charts=True,
    include_tables=True,
    include_summary=True
)
report = generate_report(data, config)
```

### 2. 返回值设计规范

```python
# ❌ 不好：返回类型不一致
def get_user(user_id: int):
    if not found:
        return None      # 返回None
    elif error:
        return False     # 返回False
    else:
        return user_obj  # 返回对象

# ✅ 好：返回类型一致
def get_user(user_id: int) -> Optional[User]:
    """获取用户，不存在返回None"""
    user = database.query(User).filter_by(id=user_id).first()
    return user

# ✅ 好：返回多个值使用元组
def parse_result(data: str) -> Tuple[bool, str]:
    """解析结果，返回(成功标志, 消息或数据)"""
    try:
        parsed = json.loads(data)
        return True, parsed
    except json.JSONDecodeError as e:
        return False, str(e)

# ✅ 好：返回多个值使用dataclass
@dataclass
class ParseResult:
    success: bool
    data: Optional[Dict] = None
    error: Optional[str] = None

def parse_result(data: str) -> ParseResult:
    """解析结果"""
    try:
        parsed = json.loads(data)
        return ParseResult(success=True, data=parsed)
    except json.JSONDecodeError as e:
        return ParseResult(success=False, error=str(e))
```

**返回值规则：**
- ✅ 返回类型单一（不混合None、False、[]等）
- ✅ 多个返回值使用元组或dataclass
- ✅ 错误使用异常而非返回值
- ✅ 成功/失败使用布尔值或自定义类型

### 3. 函数长度和复杂度

```python
【函数规模参考】
- 小函数: ≤ 30行    → 单一职责，易于测试
- 中函数: 30-100行  → 3-5个清晰的步骤
- 大函数: > 100行   → 考虑拆分
```

**拆分函数的标志：**
- ✅ 超过50行
- ✅ 有多个嵌套循环/条件
- ✅ 超过3个不同的责任
- ✅ 难以用一句话描述功能

**重构示例：**

```python
# ❌ 原函数太复杂
def process_and_save(file_path: str) -> bool:
    # 读取
    with open(file_path) as f:
        content = f.read()

    # 验证
    if not validate(content):
        return False

    # 处理
    processed = transform(content)

    # 保存
    with open(file_path + ".out") as f:
        f.write(processed)

    # 发送
    send_notification(file_path)

    return True

# ✅ 拆分后的函数
def process_and_save(file_path: str) -> bool:
    """处理文件并保存结果"""
    content = _load_file(file_path)
    if not _validate_content(content):
        return False

    processed = _transform_content(content)
    _save_file(file_path + ".out", processed)
    _notify_completion(file_path)
    return True

def _load_file(path: str) -> str:
    """加载文件内容"""
    with open(path) as f:
        return f.read()

def _validate_content(content: str) -> bool:
    """验证内容有效性"""
    return len(content) > 0 and content.startswith("valid")

def _transform_content(content: str) -> str:
    """转换内容格式"""
    return content.upper()

def _save_file(path: str, content: str) -> None:
    """保存文件"""
    with open(path, 'w') as f:
        f.write(content)

def _notify_completion(file_path: str) -> None:
    """通知任务完成"""
    print(f"处理完成: {file_path}")
```

### 4. 函数命名规范

| 动词 | 含义 | 示例 |
|-----|------|------|
| **get_** | 获取数据 | `get_user()`, `get_config()` |
| **set_** | 设置数据 | `set_timeout()`, `set_logging_level()` |
| **is_** | 检查条件 | `is_valid()`, `is_empty()` |
| **has_** | 检查属性 | `has_children()`, `has_permission()` |
| **can_** | 检查能力 | `can_delete()`, `can_access()` |
| **process_** | 处理数据 | `process_file()`, `process_payment()` |
| **parse_** | 解析数据 | `parse_json()`, `parse_response()` |
| **convert_** | 转换格式 | `convert_to_json()`, `convert_to_csv()` |
| **calculate_** | 计算值 | `calculate_total()`, `calculate_score()` |
| **validate_** | 验证数据 | `validate_input()`, `validate_schema()` |
| **_** 前缀 | 私有函数 | `_validate_internal()` |

---

## 📦 数据结构规范

### 1. 使用dataclass而非dict

```python
# ❌ 不好：使用dict，没有类型提示
config = {
    'host': 'localhost',
    'port': 5432,
    'timeout': 30
}
# 容易拼写错误：config['hos']  # 运行时才发现

# ✅ 好：使用dataclass
from dataclasses import dataclass

@dataclass
class DatabaseConfig:
    host: str
    port: int
    timeout: int = 30  # 默认值

config = DatabaseConfig(
    host='localhost',
    port=5432
)
# IDE会检查：config.hos  # 编译时就发现错误

# dataclass自动生成的功能
config.host = 'newhost'  # 可修改（mutable）
config == DatabaseConfig('newhost', 5432)  # 自动__eq__
repr(config)  # 自动__repr__
```

**dataclass优势：**
- ✅ 类型提示完整
- ✅ IDE自动补全
- ✅ 编译时类型检查 (mypy)
- ✅ 自动生成__init__、__repr__、__eq__等方法
- ✅ 支持继承、默认值、工厂函数
- ✅ 可使用frozen=True创建不可变对象

### 2. 使用Enum避免魔法字符串

```python
# ❌ 不好：魔法字符串分散在代码中
if status == "success":
    ...
elif status == "failed":
    ...
elif status == "pending":
    ...

# ✅ 好：使用Enum
from enum import Enum

class ProcessStatus(Enum):
    """处理状态枚举"""
    SUCCESS = "success"
    FAILED = "failed"
    PENDING = "pending"

if status == ProcessStatus.SUCCESS:
    ...

# Enum的好处
status = ProcessStatus.SUCCESS
status.value    # "success"
status.name     # "SUCCESS"
str(status)     # "ProcessStatus.success"
ProcessStatus("success")  # 通过值查找枚举
```

---

## 📥 参数和返回值规范

### 1. 完整的参数文档

```python
def merge_records(
    records: List[Dict[str, Any]],
    merge_key: str = "id",
    conflict_strategy: str = "last"
) -> Dict[str, Dict[str, Any]]:
    """合并多条记录

    将列表中的多条相似记录合并为一个记录。
    适用于数据去重和数据融合场景。

    算法说明：
        1. 按merge_key分组
        2. 同组内按冲突策略合并
        3. 返回合并后的结果字典

    参数说明：
        records (List[Dict[str, Any]]): 待合并的记录列表
                                       - 每项是一个字典
                                       - 必须包含merge_key字段
                                       - 可以为空列表
        merge_key (str): 用于分组的键，默认"id"
                        - 必须存在于所有记录中
                        - 作为结果字典的键
        conflict_strategy (str): 冲突解决策略，默认"last"
                               - "last": 保留最后一个值
                               - "first": 保留第一个值
                               - "merge": 合并所有值为列表
                               - "custom": 使用自定义函数

    返回值：
        Dict[str, Dict[str, Any]]: 合并后的结果字典
        - 键: merge_key的值
        - 值: 合并后的记录字典
        示例：{
            "id1": {"id": "id1", "name": "John", ...},
            "id2": {"id": "id2", "name": "Jane", ...}
        }

    异常处理：
        TypeError: records不是列表或merge_key不是字符串
        ValueError: merge_key在某条记录中不存在
                  或conflict_strategy值无效
        KeyError: 字典访问失败时

    性能特性：
        - 时间复杂度：O(n)，其中n是records长度
        - 空间复杂度：O(m)，其中m是合并后的记录数
        - 大数据集（>100k条）建议分批处理

    示例：
        >>> records = [
        ...     {"id": "1", "name": "John", "age": 30},
        ...     {"id": "1", "name": "John Doe", "age": 31},
        ...     {"id": "2", "name": "Jane", "age": 28}
        ... ]
        >>> result = merge_records(records, merge_key="id")
        >>> result["1"]
        {"id": "1", "name": "John Doe", "age": 31}
    """
```

### 2. 参数验证模式

```python
def process_file(
    file_path: str,
    max_size: int = 1024*1024*100  # 100MB
) -> ProcessResult:
    """处理文件"""

    # ===== 参数验证：第一步 =====
    # 验证file_path
    if not file_path:
        raise ValueError("文件路径不能为空")

    if not isinstance(file_path, str):
        raise TypeError(f"文件路径必须是字符串，得到{type(file_path)}")

    # 验证max_size
    if not isinstance(max_size, int):
        raise TypeError(f"max_size必须是整数，得到{type(max_size)}")

    if max_size <= 0:
        raise ValueError(f"max_size必须大于0，得到{max_size}")

    # ===== 文件存在性检查 =====
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"文件不存在: {file_path}")

    # ===== 文件大小检查 =====
    file_size = os.path.getsize(file_path)
    if file_size > max_size:
        raise ValueError(
            f"文件过大: {file_size} > {max_size} "
            f"(超过{file_size - max_size}字节)"
        )

    # ===== 业务逻辑开始 =====
    return _do_process(file_path)
```

---

## ⚠️ 异常处理规范

### 1. 异常定义和使用

```python
# ❌ 不好：捕获所有异常
try:
    process_data(data)
except:  # 绝对不要这样做
    print("出错了")

# ✅ 好：明确捕获特定异常
try:
    result = process_data(data)
except ValueError as e:
    logger.error(f"数据格式错误: {e}")
    raise  # 重新抛出，让上层处理
except IOError as e:
    logger.error(f"文件操作错误: {e}")
    return DEFAULT_RESULT  # 降级处理
```

### 2. 异常处理模式

#### **参数验证异常**

```python
def divide(a: float, b: float) -> float:
    """计算a/b的商"""
    if not isinstance(a, (int, float)):
        raise TypeError(f"a必须是数字，得到{type(a)}")
    if not isinstance(b, (int, float)):
        raise TypeError(f"b必须是数字，得到{type(b)}")
    if b == 0:
        raise ValueError("除数不能为零")
    return a / b
```

#### **资源获取异常**

```python
def read_file(path: str) -> str:
    """读取文件内容"""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        logger.error(f"文件不存在: {path}")
        raise  # 重新抛出，让调用者处理
    except UnicodeDecodeError as e:
        logger.error(f"文件编码错误 {path}: {e}")
        raise  # 编码问题通常不可恢复
```

#### **业务逻辑异常**

```python
def transfer_money(from_account: str, to_account: str, amount: float):
    """转账"""
    try:
        # 参数验证
        if amount <= 0:
            raise ValueError(f"转账金额必须大于0，得到{amount}")

        # 检查账户
        from_info = get_account(from_account)
        to_info = get_account(to_account)

        # 检查余额
        if from_info.balance < amount:
            raise ValueError("余额不足")

        # 执行转账（可能有网络或数据库错误）
        api.transfer(from_account, to_account, amount)

    except ValueError as e:
        # 参数或业务逻辑错误，不需要重试
        logger.warning(f"转账失败: {e}")
        return False

    except ConnectionError as e:
        # 网络错误，可以重试
        logger.warning(f"网络错误，准备重试: {e}")
        return retry_transfer(from_account, to_account, amount)

    except Exception as e:
        # 未预期的错误，记录完整traceback
        logger.error(f"转账异常: {e}", exc_info=True)
        raise
```

### 3. 异常链接（保留原始异常）

```python
# ❌ 不好：丢失原始异常
try:
    json.loads(data)
except json.JSONDecodeError:
    raise ValueError("JSON格式错误")  # 丢失原始异常信息

# ✅ 好：使用from保留异常链接
try:
    json.loads(data)
except json.JSONDecodeError as e:
    # from e保留了原始异常，便于调试
    raise ValueError("JSON格式错误") from e
```

---

## 🏷️ 类型提示规范

### 1. 完整的类型提示

```python
# ❌ 不好：没有类型提示
def process_data(data, options=None):
    return transform(data, options)

# ✅ 好：完整的类型提示
def process_data(
    data: List[Dict[str, Any]],
    options: Optional[ProcessOptions] = None
) -> List[Dict[str, Any]]:
    """处理数据列表，返回转换后的结果"""
    if options is None:
        options = ProcessOptions()
    return transform(data, options)
```

### 2. 复杂类型提示

```python
from typing import Union, Callable, TypeVar, Generic

# 联合类型（多种可能）
def load_config(path: Union[str, Path]) -> Dict[str, Any]:
    """接受字符串或Path对象"""
    pass

# 可调用类型（函数作为参数）
def apply_transformation(
    data: List[int],
    transform_func: Callable[[int], int]
) -> List[int]:
    """应用转换函数到每个元素"""
    return [transform_func(x) for x in data]

# 泛型类型（保持类型一致）
T = TypeVar('T')
def get_first(items: List[T]) -> T:
    """获取列表的第一个元素，返回类型与输入一致"""
    return items[0]

# 回调函数类型
def register_callback(
    callback: Callable[[str, int], bool]
) -> None:
    """注册回调函数，签名为(str, int)->bool"""
    pass
```

---

## 📝 日志记录规范

### 1. 日志初始化

```python
import logging

# 模块顶部获取logger
# 使用__name__自动获取模块名称
logger = logging.getLogger(__name__)

# 在应用程序main中配置日志格式
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

### 2. 日志级别使用指南

| 级别 | 用途 | 示例 |
|-----|------|------|
| **DEBUG** | 调试信息 | `logger.debug(f"处理第{i}行，值{value}")` |
| **INFO** | 重要状态 | `logger.info(f"成功处理{count}条记录")` |
| **WARNING** | 警告信息 | `logger.warning(f"跳过无效数据: {data}")` |
| **ERROR** | 错误信息 | `logger.error(f"处理失败: {error}")` |
| **CRITICAL** | 严重错误 | `logger.critical(f"系统崩溃: {error}")` |

### 3. 日志记录模式

```python
def process_large_file(file_path: str) -> bool:
    """处理大型文件"""
    try:
        # 处理开始
        logger.info(f"开始处理文件: {file_path}")

        # 输入检查
        if not os.path.exists(file_path):
            logger.warning(f"文件不存在: {file_path}")
            return False

        # 处理过程的关键步骤
        with open(file_path) as f:
            lines = f.readlines()
        logger.debug(f"已读取{len(lines)}行")

        # 处理进度（定期输出）
        for i, line in enumerate(lines):
            if i % 1000 == 0:
                logger.info(f"处理进度: {i}/{len(lines)}")
            process_line(line)

        # 处理完成
        logger.info(f"文件处理完成: {file_path}")
        return True

    except Exception as e:
        # 错误日志必须包含exc_info获取完整traceback
        logger.error(
            f"处理文件失败: {file_path}, 错误: {e}",
            exc_info=True  # 关键：包含堆栈跟踪
        )
        return False
```

### 4. 避免日志陷阱

```python
# ❌ 陷阱1：日志信息不足
logger.error("发生错误")  # 什么错误？哪里出错？

# ✅ 改进：提供完整信息
logger.error(f"文件读取失败: {file_path}, 错误: {str(e)}", exc_info=True)

# ❌ 陷阱2：性能问题（计算成本高）
logger.debug(f"数据: {expensive_calculation()}")  # 即使DEBUG关闭也会执行

# ✅ 改进：条件检查
if logger.isEnabledFor(logging.DEBUG):
    logger.debug(f"数据: {expensive_calculation()}")

# ❌ 陷阱3：敏感信息暴露
logger.info(f"用户登录: {username}:{password}")  # 密码不应该在日志中

# ✅ 改进：过滤敏感信息
logger.info(f"用户登录: {username}")  # 只记录用户名
```

---

## 🏗️ 代码组织规范

### 1. 模块内部结构

```python
# 【第1部分】文件头注释（10行）
# ============================================================
# 文件: utils/processor.py
# 功能: 数据处理核心模块
# ...
# ============================================================

# 【第2部分】导入（15-20行）
import logging
from typing import List, Dict

# 【第3部分】logger初始化（3行）
logger = logging.getLogger(__name__)

# 【第4部分】常量定义（30-50行）
MAX_SIZE = 1000
DEFAULT_TIMEOUT = 30

# 【第5部分】数据类定义（50-100行）
@dataclass
class ProcessResult:
    success: bool
    data: List[Dict]

# 【第6部分】公开函数（100-200行）
def process_data(data: List) -> ProcessResult:
    """处理数据"""
    pass

# 【第7部分】私有函数（50-100行）
def _validate_data(data: List) -> bool:
    """验证数据"""
    pass

# 【第8部分】主程序块（10-20行）
if __name__ == "__main__":
    pass
```

### 2. 函数排序规范

```
【推荐排序】

模块内函数排序应该遵循以下原则：

1. 公开函数优先
   ├─ 主要API函数（最常用）
   ├─ 次要API函数
   └─ 工具函数

2. 私有函数次序
   ├─ 被公开函数调用的私有函数
   ├─ 被其他私有函数调用的私有函数
   └─ 独立的私有函数

【好处】
- 用户看到主要接口
- 逻辑层次清晰
- 易于维护代码关系
```

### 3. 代码分块规范

```python
def complex_processing(data: dict) -> dict:
    """复杂数据处理"""

    # ===== 第1步：验证输入 =====
    # 检查数据类型和内容完整性
    if not isinstance(data, dict):
        raise TypeError(f"data必须是字典，得到{type(data)}")

    if not data:
        logger.warning("输入数据为空")
        return {}

    # ===== 第2步：数据清洗 =====
    # 移除空值和无效数据
    clean_data = {k: v for k, v in data.items() if v is not None}
    logger.debug(f"清洗后数据条数: {len(clean_data)}")

    # ===== 第3步：业务转换 =====
    # 应用核心业务逻辑
    transformed = transform_business_logic(clean_data)

    # ===== 第4步：格式处理 =====
    # 转换为输出格式
    result = format_output(transformed)

    # ===== 第5步：返回结果 =====
    logger.info(f"处理完成，输出{len(result)}条记录")
    return result
```

---

## ✅ 测试编写规范

### 1. 测试文件组织

```
project/
├─ src/                   # 源代码
│  └─ utils/processor.py
└─ tests/                 # 测试目录
   ├─ unit/               # 单元测试
   │  ├─ test_processor.py      # 对应src/utils/processor.py
   │  └─ test_validator.py
   ├─ integration/        # 集成测试
   │  └─ test_full_flow.py
   ├─ fixtures/           # 测试数据
   │  ├─ __init__.py
   │  └─ sample_data.py
   └─ output/             # 测试输出
      └─ test_results.log
```

### 2. 测试命名规范

```python
class TestDataProcessor:
    """数据处理器的测试套件"""

    # 命名格式：test_<function>_<condition>_<expected>

    def test_process_empty_input_returns_empty_result(self):
        """测试空输入：应返回空结果"""
        result = process([])
        assert result == []

    def test_process_valid_data_returns_processed_result(self):
        """测试有效数据：应返回处理后的结果"""
        data = [1, 2, 3]
        result = process(data)
        assert result == [2, 4, 6]

    def test_process_invalid_type_raises_type_error(self):
        """测试无效类型：应抛出TypeError"""
        with pytest.raises(TypeError):
            process("invalid")

    def test_process_large_dataset_completes_in_time(self):
        """测试大数据集：应在规定时间内完成"""
        data = list(range(10000))
        start = time.time()
        process(data)
        duration = time.time() - start
        assert duration < 1.0  # 应该在1秒内完成
```

### 3. 测试覆盖规范

**必须包含的测试类型：**

```python
class TestPaymentProcessor:
    """支付处理器测试"""

    # ✅ 正常情况测试
    def test_process_valid_payment(self):
        """正常支付流程"""
        pass

    # ✅ 边界情况测试
    def test_process_zero_amount(self):
        """金额为0"""
        pass

    def test_process_negative_amount(self):
        """负数金额"""
        pass

    def test_process_very_large_amount(self):
        """超大金额"""
        pass

    # ✅ 异常情况测试
    def test_process_invalid_account(self):
        """账户不存在"""
        pass

    def test_process_insufficient_balance(self):
        """余额不足"""
        pass

    def test_process_network_error(self):
        """网络错误"""
        pass

    # ✅ 集成测试
    def test_process_payment_end_to_end(self):
        """端到端测试"""
        pass

    # 【覆盖率目标】
    # - 行覆盖率: ≥ 80%
    # - 分支覆盖率: ≥ 75%
    # - 函数覆盖率: ≥ 90%
```

---

## 📊 代码质量检查清单

提交代码前，使用此清单验证代码质量：

### ✅ 注释检查
- [ ] 文件头注释完整（所有9项）
- [ ] 所有常量有详细注释
- [ ] 所有函数有完整docstring
- [ ] 关键代码行有行级注释
- [ ] 注释与代码保持同步
- [ ] 注释比例60-80%

### ✅ 代码质量检查
- [ ] 没有硬编码的数字或字符串（用常量替代）
- [ ] 所有参数都有类型提示
- [ ] 所有函数都有返回类型注释
- [ ] 没有拼写和语法错误
- [ ] 代码风格一致
- [ ] 函数长度≤50行

### ✅ 异常处理检查
- [ ] 参数验证完整且在函数开始处
- [ ] 所有可能的异常都被明确处理
- [ ] 错误日志包含足够的上下文信息
- [ ] 使用异常链接（from e）保留原始异常
- [ ] 没有捕获过于宽泛的异常(避免except:)

### ✅ 测试检查
- [ ] 有单元测试覆盖所有公开函数
- [ ] 测试覆盖率≥80%
- [ ] 包含正常情况、边界情况、异常情况
- [ ] 所有测试通过
- [ ] 测试命名清晰能看出测试内容

### ✅ 日志检查
- [ ] 使用正确的日志级别
- [ ] 日志信息清晰完整（包含上下文）
- [ ] 错误日志包含exc_info=True
- [ ] 没有输出敏感信息
- [ ] 没有过度日志输出

### ✅ 类型提示检查
- [ ] 所有函数参数都有类型提示
- [ ] 所有函数都有返回类型
- [ ] 复杂类型使用明确的Union、Optional等
- [ ] 使用dataclass替代dict
- [ ] 使用Enum替代魔法字符串

---

## 🔄 更新日志

| 版本 | 日期 | 更新内容 |
|-----|------|---------|
| v1.0 | 2025-12-26 | 初版发布，基于text_formatter.py最佳实践 |

---

## 📚 参考资源

- [PEP 8 - Python 代码风格指南](https://www.python.org/dev/peps/pep-0008/)
- [PEP 257 - Python 文档字符串约定](https://www.python.org/dev/peps/pep-0257/)
- [Google Python 代码风格指南](https://google.github.io/styleguide/pyguide.html)
- [Clean Code](https://www.amazon.com/Clean-Code-Handbook-Software-Craftsmanship/) - Robert C. Martin

---

**版本**: v1.0 | **创建**: 2025-12-26 | **适用**: 所有Python项目
