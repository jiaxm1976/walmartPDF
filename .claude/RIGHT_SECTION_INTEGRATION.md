# 右侧数据独立处理流程

## 概述
为了在不影响左侧文件操作的基础上，为右侧数据构建独立的识别和导入流程。所有右侧数据都统一存储为 'right_section' 板块。

---

## 架构设计

### 1. 核心模块

#### **右侧数据处理器** (`backend/app/services/right_section_processor.py`)
- 专门处理 PDF 右侧数据的识别与提取
- 不涉及左侧（header、sales、refund等）数据处理
- 完全独立的处理流程，不会干扰左侧数据

**主要功能：**
- `extract_right_section(ocr_data)` - 从 OCR 数据中提取右侧数据
- `validate_right_section_data(right_data)` - 验证数据完整性
- `format_right_section_for_db(right_data)` - 格式化数据以便存储
- `merge_right_section_to_structured_data(structured_data, right_section)` - 合并到 jg_structured_data 格式

**字段列表：**
```python
RIGHT_SECTION_FIELDS = [
    '状态',              # 支付状态
    '付款日期',          # 付款日期
    '周期付款',          # 付款频率
    '付款方式',          # 付款方法
    '设备方式',          # 设备方式 (FBA/MFN)
    '待付款金额',        # 待付款金额
    '等待回款金额',      # 等待回款金额
    '回款等待期',        # 回款等待期
    '警告信息'           # 警告信息
]
```

### 2. 数据库集成

#### **数据库模式**
右侧数据存储到 `section_data` 表：
- `section_name` = 'right_section'（固定值）
- `data` = JSON 格式的所有右侧字段
- `statement_id` = 关联的 statement 记录 ID

#### **字段处理**
- 右侧数据中的所有字段都被设为**高频字段**（frequency >= 2）
- 这意味着：不会被合并到 `right_section_其他` 字段
- 每个字段都独立存储在 JSON 中，方便查询和提取

#### **频率初始化** (`scripts/init_right_section.py`)
在数据库初始化时，自动在 `field_frequency` 表中创建右侧数据字段记录。

### 3. 导入流程

#### **流程图**
```
PDF 处理
   ↓
─────────────────────────────┬─────────────────────────────
左侧处理                      │                        右侧处理
  (header/sales/refund...)   │        (payment info)
  ↓                          │              ↓
 jg_structured_data          │    RightSectionProcessor
  (左侧板块)                  │    .extract_right_section()
  ↓                          │              ↓
structured_importer          │    right_section 数据
  .import_jg_data()          │    (9 个字段)
  ↓                          │              ↓
statements + section_data    │    merge_right_section_to_structured_data()
 (左侧数据)                   │              ↓
  ↑────────────────────────────────────────┘
  
最终：
statements 表 + section_data 表
  - 左侧板块 (header/sales/refund...)
  - 右侧板块 (right_section)
```

#### **集成步骤**

**步骤 1：初始化数据库**
```bash
python scripts/init_database_v2.py
```
此脚本会：
- 创建 statements、section_data、field_frequency 等表
- 初始化所有字段频率（包括右侧数据的 9 个字段）
- 确保右侧数据的字段被标记为高频

**步骤 2：导入 PDF 并处理右侧数据**

在你的 PDF 处理流程中：

```python
from backend.app.services.right_section_processor import RightSectionProcessor, merge_right_section_to_structured_data
from backend.database.structured_importer import StructuredDataImporter

# 假设你已经有：
# 1. PDF 处理完成，获得 jg_data（包含左侧和右侧信息）
# 2. jg_structured_data 格式的数据（左侧板块）

# Step 1: 提取右侧数据
processor = RightSectionProcessor()
right_section = processor.extract_right_section(jg_data)

# Step 2: 验证右侧数据
if processor.validate_right_section_data(right_section):
    # Step 3: 格式化并合并到 structured_data
    formatted_right = processor.format_right_section_for_db(right_section)
    jg_data = merge_right_section_to_structured_data(jg_data, formatted_right)
    
    # Step 4: 导入到数据库（统一处理左右侧数据）
    importer = StructuredDataImporter('backend/data/walmart_pdf_parser.db')
    importer.connect()
    statement_id = importer.import_jg_data(pdf_name, jg_data)
    importer.disconnect()
```

**步骤 3：验证导入结果**
```bash
# 查询右侧数据记录数
sqlite3 backend/data/walmart_pdf_parser.db
SELECT COUNT(*) FROM section_data WHERE section_name = 'right_section';

# 查看右侧数据样本
SELECT id, data FROM section_data WHERE section_name = 'right_section' LIMIT 1;
```

---

## 关键特性

### 1. **完全独立处理**
- 右侧数据的识别和提取不涉及左侧处理
- 错误处理和日志记录独立
- 不会因为右侧数据问题而影响左侧导入

### 2. **灵活的字段识别**
- 支持多种字段名映射（英文/中文）
- 自动适配不同的 OCR 结果格式
- 支持从 payment_details、right_section、other_section 等多个源提取

### 3. **数据库设计**
- 所有右侧字段存储在单个 JSON 字段中
- 通过 SQLite 的 JSON 函数可以灵活查询
- 无需提前定义所有字段列，支持动态扩展

### 4. **高频字段处理**
- 右侧数据的所有字段都被设为高频（frequency = 2）
- 避免低频字段被合并到 `_其他` 字段
- 保持数据完整性和可查询性

---

## 使用示例

### 查询右侧数据
```sql
-- 查询所有右侧数据
SELECT s.pdf_name, sd.data 
FROM statements s
LEFT JOIN section_data sd ON s.id = sd.statement_id
WHERE sd.section_name = 'right_section';

-- 提取特定字段（SQLite JSON 函数）
SELECT 
    s.pdf_name,
    json_extract(sd.data, '$.状态') as 状态,
    json_extract(sd.data, '$.付款日期') as 付款日期,
    json_extract(sd.data, '$.待付款金额') as 待付款金额
FROM statements s
LEFT JOIN section_data sd ON s.id = sd.statement_id
WHERE sd.section_name = 'right_section';
```

### 字段提取和合并
```python
from backend.app.services.right_section_processor import RightSectionProcessor

processor = RightSectionProcessor()

# 从原始 OCR 数据提取
ocr_data = {
    'payment_details': {
        'status': '待发送',
        'payment_date': '2025-01-08',
        'payment_method': '直接存款',
        # ...
    }
}

right_section = processor.extract_right_section(ocr_data)
# 结果: {'状态': '待发送', '付款日期': '2025-01-08', '付款方式': '直接存款', ...}
```

---

## 文件清单

### 新增文件
1. **backend/app/services/right_section_processor.py** - 右侧数据处理器
2. **scripts/init_right_section.py** - 右侧数据初始化脚本

### 修改文件
1. **backend/database/structured_importer.py** - 添加右侧数据特殊处理逻辑
2. **scripts/init_database_v2.py** - 集成右侧数据初始化

### 不受影响的文件
- **backend/database/schema_v2_dynamic.sql** - schema 保持不变
- 所有左侧处理相关的代码都不受影响

---

## 测试验证

### 1. 初始化验证
```bash
python scripts/init_database_v2.py
# 检查输出中是否包含：
# ✓ 右侧数据字段初始化完成 (9 个字段)
```

### 2. 导入验证
```bash
# 导入 PDF 后检查
sqlite3 backend/data/walmart_pdf_parser.db
SELECT section_name, COUNT(*) FROM section_data GROUP BY section_name;
# 应该包含 'right_section' 行
```

### 3. 数据完整性验证
```python
import sqlite3
import json

conn = sqlite3.connect('backend/data/walmart_pdf_parser.db')
cursor = conn.execute(
    "SELECT data FROM section_data WHERE section_name = 'right_section' LIMIT 1"
)
row = cursor.fetchone()
data = json.loads(row[0])
print(f"字段数: {len(data)}")
print(f"字段名: {list(data.keys())}")
# 应该显示 9 个字段
```

---

## 总结

这个方案通过以下方式实现了右侧数据的独立处理：

1. **模块化设计** - 右侧数据处理完全独立
2. **数据库集成** - 统一存储在 section_data 表中
3. **不影响左侧** - 左侧处理流程完全不受影响
4. **灵活扩展** - 支持动态添加新字段
5. **便于查询** - JSON 格式支持灵活的数据提取

右侧数据现在作为 'right_section' 板块，与左侧的其他板块（header、sales、refund等）并存于同一数据库中，可以方便地进行联合查询和分析。
