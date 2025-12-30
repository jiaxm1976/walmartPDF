# PDF数据流程分析文档

> **创建日期**: 2025-12-19
> **目的**: 详细说明PDF从解析到数据库存储的完整流程

---

## 📊 数据流程概览

```
PDF文件
  ↓
① 上传阶段 (API)
  ↓
② 解析阶段 (PDFParserService)
  ↓
③ 数据格式转换
  ↓
④ 数据库存储 (CRUD)
  ↓
数据库 (10个表)
```

---

## 1️⃣ 上传阶段

### 入口：POST /api/v1/pdfs/upload

**文件**: `backend/app/api/v1/pdfs.py::upload_pdf()`

**流程**:
```python
1. 接收文件上传
   └─ FastAPI UploadFile对象

2. 验证文件
   ├─ 检查扩展名 (.pdf)
   └─ 检查文件大小 (< 50MB)

3. 保存物理文件
   ├─ 生成唯一文件名: {timestamp}_{original_name}.pdf
   ├─ 保存到: uploads/20251219_151030_MP_01142025.pdf
   └─ 计算SHA256哈希值

4. 创建数据库记录
   ├─ 表: pdf_files
   ├─ 状态: 'pending' (待解析)
   └─ 返回: pdf_id=1
```

**数据存储形式**:
```python
# 物理文件
uploads/20251219_151030_MP_01142025_statement_summary.pdf

# 数据库记录 (pdf_files表)
{
    "id": 1,
    "filename": "20251219_151030_MP_01142025_statement_summary.pdf",
    "original_filename": "MP_01142025_statement_summary.pdf",
    "file_path": "/path/to/uploads/20251219_151030_MP_01142025_statement_summary.pdf",
    "file_size": 1048576,
    "file_hash": "a3b5c7d9...",
    "process_status": "pending",
    "created_at": "2025-12-19 15:10:30"
}
```

---

## 2️⃣ 解析阶段

### 入口：POST /api/v1/pdfs/{pdf_id}/parse

**文件**: `backend/app/api/v1/pdfs.py::parse_pdf()`

### 2.1 触发解析流程

```python
# API层
@router.post("/{pdf_id}/parse")
async def parse_pdf(pdf_id: int, db: Session):
    # 1. 验证PDF存在
    db_pdf = crud.get_pdf_file(db, pdf_id)

    # 2. 更新状态为 'processing'
    crud.update_pdf_file_status(db, pdf_id, "processing")

    # 3. 调用解析服务
    parser = PDFParserService(dpi=300)
    result = parser.parse_pdf(file_path)

    # 4. 转换格式
    db_format_data = parser.convert_to_database_format(result["data"])

    # 5. 保存到数据库
    crud.save_parsed_data_to_db(db, pdf_id, db_format_data)

    # 6. 更新状态为 'success'
    crud.update_pdf_file_status(db, pdf_id, "success")
```

### 2.2 PDFParserService详细流程

**文件**: `backend/app/services/pdf_parser_service.py::parse_pdf()`

```python
def parse_pdf(pdf_path: str) -> Dict:
    """
    完整的6步解析流程
    """

    # Step 1: PDF转灰度图片 (300 DPI)
    gray_images = pdf_to_images(pdf_path, dpi=300, grayscale=True)
    first_page = gray_images[0]  # numpy数组 (H, W)

    # Step 2: 横向分割 (63%位置切分左右)
    splitter = KeywordLocator()
    left_image, right_image = splitter.split_horizontal(first_page)

    # Step 3: OCR识别 + 提取关键词Y坐标
    keyword_extractor = KeywordExtractor(ocr_engine)
    ocr_results = ocr_engine.recognize_image(left_image)
    keyword_map = keyword_extractor.extract_keywords_positions(left_image, ocr_results)
    # → {'sales': 450, 'refund': 1200, ...}

    # Step 4: 左侧板块切分
    cutter = LeftSectionCutter()
    section_ranges = cutter.calculate_section_ranges(keyword_map, image_height)
    # → {'header': (0, 450), 'sales': (450, 1200), ...}

    # 切分图片（内存中）
    section_images = {
        'header': left_image[0:450, :],
        'sales': left_image[450:1200, :],
        'refund': left_image[1200:1800, :],
        ...
    }

    # Step 5: 左侧OCR识别（各板块）
    left_ocr = LeftSectionOCR(ocr_engine)
    left_data = left_ocr.process_all_sections(section_images)
    # → {
    #     'header': {'开始日期': '2024年12月6日', ...},
    #     'sales': {'产品价格': '1355.89', '运输': '13.98', ...},
    #     'refund': {'产品价格': '-65.55', ...},
    #     ...
    # }

    # Step 6: 右侧OCR识别
    right_ocr = RightSectionOCR(ocr_engine)
    right_data = right_ocr.process_right_image(right_image)
    # → {
    #     'payment_details': {'状态': '不予付款', '付款日期': '2025年1月14日', ...}
    # }

    # 整合返回
    return {
        "success": True,
        "data": {
            "left_section": left_data,   # 8个板块数据
            "right_section": right_data  # 付款详情
        },
        "process_time": 2.5
    }
```

### 2.3 解析结果数据结构

```json
{
  "success": true,
  "data": {
    "left_section": {
      "header": {
        "开始日期": "2024年12月6日",
        "结束日期": "2025年1月11日",
        "期初余额": "-122.56",
        "备用金": "0.00",
        "回款等待": "0.00"
      },
      "sales": {
        "产品价格": "1355.89",
        "运输": "13.98",
        "WFS运输退款": "-13.98",
        "已收税净额": "92.92",
        "净佣金": "-195.44",
        "扣缴税款净额": "-91.91",
        "WFS 运输税退款": "-1.01",
        "T沃尔玛出资的节余": "0.00",
        "总计：": "1160.45",
        "其他税款（费用）": "5.00"
      },
      "refund": {
        "产品价格": "-65.55",
        "运输": "0.00",
        "已收税净额": "-3.26",
        "佣金": "4.88",
        "扣缴税款净额": "3.26",
        "T沃尔玛出资的节余": "0.00",
        "总计": "-60.67"
      },
      "adjustment": {
        "退货沃尔玛运输服务费": "-17.50",
        "沃尔玛全球运输标签服务费": "-216.68",
        "总计": "-234.18"
      },
      "wfs": {
        "沃尔玛商品服务（WFS）": "-171.15",
        "WFS 以太坊费": "-3.85",
        "WFS 总折扣": "0.00",
        "总计：": "-175.00"
      },
      "other": {
        "沃尔玛产品广告": "-568.04",
        "总计：": "-568.04"
      },
      "footer": {
        "期末余额": "0.00",
        "向您支付的金额": "0.00"
      }
    },
    "right_section": {
      "payment_details": {
        "状态": "不予付款",
        "付款日期": "2025年1月14日（太平洋夏令时）",
        "周期付款": "每周",
        "付款方式": "pingpong",
        "设备方式": "曰信用卡",
        "待付款金额": "0.00美元",
        "等待回款金额": "① 0.00美元",
        "回款等待期": "①"
      }
    }
  },
  "process_time": 2.5
}
```

---

## 3️⃣ 数据格式转换

### 入口：PDFParserService.convert_to_database_format()

**文件**: `backend/app/services/pdf_parser_service.py::convert_to_database_format()`

### 3.1 转换流程（当前实现）

```python
def convert_to_database_format(parsed_data: Dict) -> Dict:
    """
    将解析结果转换为数据库格式

    输入: PDF解析结果（中文字段名，字符串值）
    输出: 数据库格式（英文字段名，类型化值）
    """

    left_section = parsed_data.get("left_section", {})
    right_section = parsed_data.get("right_section", {})

    # 转换每个板块
    result = {}

    # 1. Header板块
    header = left_section.get("header", {})
    result["header"] = {
        "start_date": parse_date(header.get("开始日期")),      # str → date
        "end_date": parse_date(header.get("结束日期")),        # str → date
        "opening_balance": parse_decimal(header.get("期初余额")),  # str → Decimal
        "reserve_funds": parse_decimal(header.get("备用金")),
        "awaiting_payment": parse_decimal(header.get("回款等待")),
    }

    # 2. Sales板块
    sales = left_section.get("sales", {})
    result["sales"] = {
        "product_price": parse_decimal(sales.get("产品价格")),
        "shipping": parse_decimal(sales.get("运输")),
        "net_commission": parse_decimal(sales.get("净佣金")),
        ...
    }

    # ... 其他板块类似

    return result
```

### 3.2 字段映射表

```python
# 中文字段 → 英文字段
FIELD_MAPPING = {
    "header": {
        "开始日期": "start_date",
        "结束日期": "end_date",
        "期初余额": "opening_balance",
        "备用金": "reserve_funds",
        "回款等待": "awaiting_payment",
    },
    "sales": {
        "产品价格": "product_price",
        "运输": "shipping",
        "净佣金": "net_commission",
        "扣缴税款净额": "withholding_tax",
        "已收税净额": "net_tax_collected",
        "T沃尔玛出资的节余": "walmart_funded_savings",
        "总计": "total",
        ...
    },
    ...
}
```

### 3.3 Phase 3.1优化版转换（使用data_processor）

**文件**: `backend/app/utils/data_processor.py::prepare_section_for_database()`

```python
def prepare_section_for_database(section_name: str, section_data: Dict) -> Dict:
    """
    优化版转换流程（集成规范化 + 核心字段 + other_total）

    步骤:
    1. 字段名规范化（去标点、空格、同义词）
    2. 判断核心字段 vs 低频字段
    3. 核心字段 → 独立列
    4. 低频字段 → 累加到 other_total
    5. 填充默认值
    """

    # Step 1: 规范化字段名
    normalized_data = normalize_section_data(section_data)
    # "总计：" → "总计"
    # "WFS运输税退款" → "WFS 运输税退款"
    # "T沃尔玛出资的节余总额" → "T沃尔玛出资的节余"

    # Step 2: 分离核心字段和低频字段
    core_field_data = {}
    other_total = Decimal('0.00')

    for field_name, field_value in normalized_data.items():
        if is_core_field(section_name, field_name):
            # 核心字段：转换为英文名 + Decimal
            english_name = get_english_field_name(section_name, field_name)
            core_field_data[english_name] = parse_amount(field_value)
        else:
            # 低频字段：累加到 other_total
            other_total += parse_amount(field_value)

    # Step 3: 填充默认值（缺失的核心字段 → 0.00）
    complete_data = fill_default_values(section_name, core_field_data)

    # Step 4: 添加 other_total
    complete_data['other_total'] = other_total

    return complete_data

# 示例:
# 输入:
section_data = {
    "产品价格": "1000",
    "运输": "50",
    "其他税款（费用）": "5",  # 低频字段
}

# 输出:
{
    'product_price': Decimal('1000'),
    'shipping': Decimal('50'),
    'net_commission': Decimal('0.00'),  # 填充默认值
    'withholding_tax': Decimal('0.00'),
    ...
    'other_total': Decimal('5')  # 低频字段汇总
}
```

---

## 4️⃣ 数据库存储

### 入口：crud.save_parsed_data_to_db()

**文件**: `backend/app/crud/pdf_file.py::save_parsed_data_to_db()`

### 4.1 存储流程

```python
def save_parsed_data_to_db(db: Session, pdf_id: int, parsed_data: Dict) -> bool:
    """
    将转换后的数据保存到数据库（10个表）

    流程:
    1. 遍历每个板块
    2. 检查记录是否已存在
    3. 存在 → 更新；不存在 → 创建
    4. 提交事务
    """

    try:
        # 1. 保存 header → statement_headers表
        if "header" in parsed_data:
            header_data = parsed_data["header"]
            existing = db.query(StatementHeader).filter_by(pdf_file_id=pdf_id).first()

            if existing:
                # 更新
                for key, value in header_data.items():
                    setattr(existing, key, value)
            else:
                # 创建
                db_header = models.StatementHeader(
                    pdf_file_id=pdf_id,
                    **header_data
                )
                db.add(db_header)

        # 2. 保存 sales → sales_details表
        if "sales" in parsed_data:
            sales_data = parsed_data["sales"]
            existing = db.query(SalesDetail).filter_by(pdf_file_id=pdf_id).first()

            if existing:
                for key, value in sales_data.items():
                    setattr(existing, key, value)
            else:
                db_sales = models.SalesDetail(
                    pdf_file_id=pdf_id,
                    **sales_data
                )
                db.add(db_sales)

        # 3-8. 类似处理其他板块
        # refund → refund_details
        # adjustment → adjustment_details
        # wfs → wfs_details
        # other → other_activity_details
        # footer → statement_footers
        # payment_details → payment_details

        # 提交事务
        db.commit()
        logger.info(f"✅ 数据保存成功: pdf_id={pdf_id}")
        return True

    except Exception as e:
        logger.error(f"❌ 数据保存失败: {e}")
        db.rollback()
        return False
```

### 4.2 数据库表结构（优化版）

```sql
-- 1. pdf_files (主表)
CREATE TABLE pdf_files (
    id INTEGER PRIMARY KEY,
    filename VARCHAR(255),
    file_path VARCHAR(500),
    file_size INTEGER,
    process_status ENUM('pending', 'processing', 'success', 'failed'),
    created_at DATETIME
);

-- 2. statement_headers (Header板块)
CREATE TABLE statement_headers (
    id INTEGER PRIMARY KEY,
    pdf_file_id INTEGER REFERENCES pdf_files(id),
    start_date DATE,
    end_date DATE,
    opening_balance DECIMAL(15,2),
    reserve_funds DECIMAL(15,2),
    awaiting_payment DECIMAL(15,2),
    created_at DATETIME
);

-- 3. sales_details (Sales板块 - 优化版)
CREATE TABLE sales_details (
    id INTEGER PRIMARY KEY,
    pdf_file_id INTEGER REFERENCES pdf_files(id),
    -- 核心字段（9个）
    product_price DECIMAL(15,2),
    shipping DECIMAL(15,2),
    net_commission DECIMAL(15,2),
    withholding_tax DECIMAL(15,2),
    net_tax_collected DECIMAL(15,2),
    walmart_funded_savings DECIMAL(15,2),
    total DECIMAL(15,2),
    wfs_shipping_refund DECIMAL(15,2),
    wfs_shipping_tax_refund DECIMAL(15,2),
    -- 低频字段汇总
    other_total DECIMAL(15,2),  -- ⬅️ 新增
    created_at DATETIME
);

-- 4-9. 其他板块表（类似结构）
-- refund_details, adjustment_details, wfs_details,
-- other_activity_details, statement_footers, payment_details

-- 10. dynamic_fields (动态字段扩展表 - 备用)
CREATE TABLE dynamic_fields (
    id INTEGER PRIMARY KEY,
    pdf_file_id INTEGER REFERENCES pdf_files(id),
    section_type ENUM('sales', 'refund', ...),
    field_name VARCHAR(255),
    field_value VARCHAR(500),
    created_at DATETIME
);
```

### 4.3 存储后的数据示例

```sql
-- pdf_files 表
id | filename                              | process_status | created_at
1  | 20251219_151030_MP_01142025.pdf      | success        | 2025-12-19 15:10:30

-- statement_headers 表
id | pdf_file_id | start_date  | end_date    | opening_balance | reserve_funds | awaiting_payment
1  | 1           | 2024-12-06  | 2025-01-11  | -122.56         | 0.00          | 0.00

-- sales_details 表
id | pdf_file_id | product_price | shipping | net_commission | ... | other_total
1  | 1           | 1355.89       | 13.98    | -195.44        | ... | 5.00

-- refund_details 表
id | pdf_file_id | product_price | commission | ... | other_total
1  | 1           | -65.55        | 4.88       | ... | 0.00

-- ... 其他表类似
```

---

## 📈 完整数据流程图

```
┌─────────────────────────────────────────────────────────────┐
│                     1. 上传阶段                              │
├─────────────────────────────────────────────────────────────┤
│  POST /api/v1/pdfs/upload                                   │
│    ↓                                                         │
│  FastAPI接收文件 (UploadFile)                               │
│    ↓                                                         │
│  保存物理文件: uploads/20251219_151030_MP.pdf               │
│    ↓                                                         │
│  创建数据库记录: pdf_files (id=1, status='pending')          │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│                     2. 解析阶段                              │
├─────────────────────────────────────────────────────────────┤
│  POST /api/v1/pdfs/1/parse                                  │
│    ↓                                                         │
│  更新状态: status='processing'                               │
│    ↓                                                         │
│  PDFParserService.parse_pdf()                               │
│  ├─ Step 1: PDF → 灰度图片 (numpy数组)                       │
│  ├─ Step 2: 横向分割 → 左右图片                              │
│  ├─ Step 3: OCR → 关键词Y坐标                                │
│  ├─ Step 4: 左侧板块切分 → 8个板块图片                        │
│  ├─ Step 5: 左侧OCR → 8个板块数据（中文字段名，字符串值）      │
│  └─ Step 6: 右侧OCR → 付款详情                               │
│    ↓                                                         │
│  返回: {                                                     │
│    "success": true,                                         │
│    "data": {                                                │
│      "left_section": {                                      │
│        "header": {"开始日期": "...", ...},                   │
│        "sales": {"产品价格": "1355.89", ...},                │
│        ...                                                  │
│      },                                                     │
│      "right_section": {...}                                 │
│    }                                                        │
│  }                                                          │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│                   3. 数据格式转换                             │
├─────────────────────────────────────────────────────────────┤
│  parser.convert_to_database_format()                        │
│  （或 data_processor.prepare_section_for_database()）         │
│    ↓                                                         │
│  处理每个板块:                                                │
│  ├─ 字段名规范化 (去标点、空格、同义词)                        │
│  ├─ 中文 → 英文映射 ("产品价格" → "product_price")            │
│  ├─ 字符串 → 类型转换 ("1355.89" → Decimal('1355.89'))       │
│  ├─ 核心字段 → 独立列                                         │
│  ├─ 低频字段 → other_total                                   │
│  └─ 填充默认值 (缺失字段 → 0.00)                              │
│    ↓                                                         │
│  返回: {                                                     │
│    "header": {                                              │
│      "start_date": date(2024, 12, 6),                      │
│      "end_date": date(2025, 1, 11),                        │
│      "opening_balance": Decimal('-122.56'),                 │
│      ...                                                    │
│    },                                                       │
│    "sales": {                                               │
│      "product_price": Decimal('1355.89'),                   │
│      "shipping": Decimal('13.98'),                          │
│      ...                                                    │
│      "other_total": Decimal('5.00')                         │
│    },                                                       │
│    ...                                                      │
│  }                                                          │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│                    4. 数据库存储                              │
├─────────────────────────────────────────────────────────────┤
│  crud.save_parsed_data_to_db(db, pdf_id=1, data)           │
│    ↓                                                         │
│  循环处理每个板块:                                            │
│  ├─ header → statement_headers 表                           │
│  ├─ sales → sales_details 表                                │
│  ├─ refund → refund_details 表                              │
│  ├─ adjustment → adjustment_details 表                      │
│  ├─ wfs → wfs_details 表                                    │
│  ├─ other → other_activity_details 表                       │
│  ├─ footer → statement_footers 表                           │
│  └─ payment_details → payment_details 表                    │
│    ↓                                                         │
│  对每个板块:                                                  │
│  ├─ 检查是否已存在 (SELECT ... WHERE pdf_file_id=1)           │
│  ├─ 存在 → UPDATE                                            │
│  └─ 不存在 → INSERT                                          │
│    ↓                                                         │
│  db.commit()  # 提交事务                                     │
│    ↓                                                         │
│  更新状态: pdf_files.process_status = 'success'              │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│                   5. 数据存储完成                             │
├─────────────────────────────────────────────────────────────┤
│  数据库中现在包含:                                            │
│  ├─ pdf_files (1条记录)                                      │
│  ├─ statement_headers (1条记录)                             │
│  ├─ sales_details (1条记录)                                 │
│  ├─ refund_details (1条记录)                                │
│  ├─ adjustment_details (1条记录)                            │
│  ├─ wfs_details (1条记录)                                   │
│  ├─ other_activity_details (1条记录)                        │
│  ├─ statement_footers (1条记录)                             │
│  └─ payment_details (1条记录)                               │
│                                                             │
│  总计: 1个PDF → 9条数据库记录（1主表 + 8板块表）              │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔍 关键代码文件索引

| 阶段 | 文件路径 | 核心函数 |
|------|---------|---------|
| 上传 | `backend/app/api/v1/pdfs.py` | `upload_pdf()` |
| 解析触发 | `backend/app/api/v1/pdfs.py` | `parse_pdf()` |
| 解析核心 | `backend/app/services/pdf_parser_service.py` | `PDFParserService.parse_pdf()` |
| 格式转换（旧） | `backend/app/services/pdf_parser_service.py` | `convert_to_database_format()` |
| 格式转换（新）| `backend/app/utils/data_processor.py` | `prepare_section_for_database()` |
| 字段规范化 | `backend/app/utils/field_normalizer.py` | `normalize_field_name()` |
| 核心字段配置 | `backend/app/config/core_fields.py` | `is_core_field()`, `get_english_field_name()` |
| 数据库保存 | `backend/app/crud/pdf_file.py` | `save_parsed_data_to_db()` |
| ORM模型 | `backend/database/models.py` | 所有模型类 |

---

## 📝 总结

### 数据存储方式

1. **物理文件**: `uploads/` 目录，原始PDF文件
2. **解析中间结果**: 内存中（numpy数组、字典），不持久化
3. **最终数据**: SQLite数据库（10个表），结构化存储

### 数据流转格式

| 阶段 | 格式 | 示例 |
|------|------|------|
| 上传 | 二进制文件 | PDF文件 (1MB) |
| 解析 | numpy数组 + 字典 | `{"sales": {"产品价格": "1355.89"}}` |
| 转换 | 字典 (类型化) | `{"sales": {"product_price": Decimal('1355.89')}}` |
| 存储 | 数据库记录 | SQLite表行 |

### 优化版改进（Phase 3.1）

1. **字段规范化**: 统一处理变体（标点、空格、同义词）
2. **核心字段**: 37个核心字段独立存储
3. **other_total**: 低频字段汇总，避免NULL值
4. **灵活性**: 新字段自动处理，无需修改Schema

---

**文档维护**: 项目组
**最后更新**: 2025-12-19 22:30
