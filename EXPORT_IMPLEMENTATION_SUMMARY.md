# 数据导出功能 - 实现总结

## 📋 功能概述

创建了一个完整的后端数据导出工具，支持：
- 按输入的开始日期从数据库导出数据
- 生成格式规范的 Excel 文件
- 两种调用方式：命令行脚本 + HTTP API

## 🎯 需求理解与实现

### 你的需求

| 需求项 | 你的要求 | 实现方式 |
|--------|---------|---------|
| 数据来源 | PDF 名称 + section_data.data | ✅ 从 statements 和 section_data 表查询 |
| 日期过滤 | 按开始日期导出 | ✅ 比较 statement_period 的起始日期 |
| JSON 展开 | data 中每个字段为一列 | ✅ 解析 JSON，展平为列 |
| 缺失值处理 | 空值填充 | ✅ 缺失字段用空值替代 |
| 输出格式 | Excel 文件 | ✅ .xlsx 格式 |
| 表头结构 | 两行表头（section + 字段名） | ✅ 第一行 section，第二行字段名 |
| 字段名语言 | 中文 | ✅ 所有字段名为中文 |
| 其他要求 | 一个表格即可 | ✅ 单个工作表，所有数据在一起 |

---

## 📦 交付物

### 1. 核心脚本

**文件：** `scripts/export_data_to_excel.py`（378 行代码）

**功能：**
```python
export_to_excel(start_date, output_file=None) -> str
```

**数据流：**
```
开始日期 (2025-09-06)
  ↓
查询 statements 表（过滤日期）
  ↓ 获取 pdf_name, statement_period
查询 section_data 表
  ↓ 获取 section_name, data (JSON)
解析 JSON，收集所有字段
  ↓
构建 DataFrame（多层列索引）
  ↓
生成 Excel 文件（手动处理表头）
  ↓
输出文件 (output/数据导出_YYYYMMDD.xlsx)
```

**主要函数：**
- `parse_period_start_date()`：解析周期字符串
- `query_statements_by_date()`：查询 PDF 记录
- `query_section_data()`：查询 section 数据
- `collect_all_fields()`：收集字段名
- `build_dataframe()`：构建 DataFrame
- `export_to_excel()`：导出 Excel
- `main()`：命令行入口

### 2. API 路由

**文件：** `backend/app/routes/export_router.py`（106 行代码）

**HTTP 端点：**

| 端点 | 方法 | 功能 |
|------|------|------|
| `/api/export/data-to-excel` | POST | 导出数据（返回 Excel 文件） |
| `/api/export/data-to-excel/status` | GET | 检查数据统计（不生成文件） |

**集成方式：** 已在 `backend/main.py` 中注册

### 3. 文档

| 文件 | 内容 |
|------|------|
| `README_导出工具.md` | 详细使用说明（包含原理、常见问题、代码示例） |
| `EXPORT_COMPLETE_GUIDE.md` | 完整指南（所有使用方式和技术细节） |
| `EXPORT_QUICK_REFERENCE.md` | 快速参考（核心用法速查） |

---

## 🚀 使用方式

### 方式 1：命令行（最简单）

```bash
# 最基础的用法
python scripts/export_data_to_excel.py 2025-09-06

# 导出到自定义路径
python scripts/export_data_to_excel.py 2025-09-06 ~/Downloads/data.xlsx

# 导出不同日期的数据
python scripts/export_data_to_excel.py 2025-10-01
python scripts/export_data_to_excel.py 2025-11-15
```

**输出示例：**
```
开始导出数据，起始日期: 2025-09-06
步骤 1/4: 查询 statements 表...
  ✓ 找到 8 条记录
步骤 2/4: 查询 section_data 表...
  ✓ 找到 56 条 section 记录
步骤 3/4: 收集所有字段...
  ✓ 找到 7 个板块，共 38 个字段
步骤 4/4: 构建 Excel 数据...
  ✓ DataFrame 尺寸: 56 行 × 40 列
✓ 数据导出成功
文件路径: /path/to/output/数据导出_20250906.xlsx
```

### 方式 2：HTTP API

**启动服务器：**
```bash
python backend/main.py
# 或
uvicorn backend.main:app --reload --port 8000
```

**导出数据：**
```bash
# curl 方式
curl -X POST "http://localhost:8000/api/export/data-to-excel?start_date=2025-09-06" \
  -o walmart_data.xlsx

# Python 方式
import requests
response = requests.post(
  "http://localhost:8000/api/export/data-to-excel",
  params={"start_date": "2025-09-06"}
)
with open("data.xlsx", "wb") as f:
    f.write(response.content)

# JavaScript 方式（已在文档中提供）
fetch('/api/export/data-to-excel?start_date=2025-09-06', {method: 'POST'})
  .then(r => r.blob())
  .then(blob => /* 处理下载 */)
```

**检查数据统计：**
```bash
curl "http://localhost:8000/api/export/data-to-excel/status?start_date=2025-09-06"
```

返回：
```json
{
  "status": "success",
  "pdf_count": 8,
  "section_count": 56,
  "message": "找到 8 个 PDF，56 个 section 记录"
}
```

---

## 📊 生成的 Excel 文件

### 文件结构

**默认位置：** `output/数据导出_YYYYMMDD.xlsx`

**工作表名：** `数据导出`

**数据尺寸示例：**
- 日期 2025-09-06：56 行 × 40 列（8 个 PDF × 7 个 section）
- 日期 2025-10-01：42 行 × 40 列（6 个 PDF × 7 个 section）
- 日期 2025-11-15：21 行 × 37 列（3 个 PDF × 7 个 section）

### 表头结构

**第一行（蓝色背景）：** Section 名称（板块）
```
基本信息 | 基本信息 | footer | footer | header | header | header | header | header | ...
```

**第二行（绿色背景）：** 字段名
```
PDF 名称 | 对账周期 | 向您支付的金额 | 期末余额 | 向您支付的金额 | 回款等待 | 备用金 | 期初余额 | 统计区间 | ...
```

**第 3+ 行：** 数据行

### 包含的 Sections

| Section | 字段数 | 说明 |
|---------|--------|------|
| header | 5 | 对账周期、向您支付的金额、期初余额、备用金、回款等待 |
| footer | 2 | 向您支付的金额、期末余额 |
| 销售 | 10 | 产品价格、佣金、运输等 |
| 退款 | 9 | 产品价格、佣金、已收税净额等 |
| 沃尔玛配送服务(WFS) | 8 | WFS 仓储费、配送费、运输税退款等 |
| 其他活动 | 2 | 沃尔玛产品广告、总计 |
| right_section | 2 | 状态、付款方式 |

**总计：** 38 个字段

### 格式特点

✅ **表头冻结**：前两行被冻结，便于查看大数据量
✅ **列宽自动调整**：每列宽度根据内容自动计算（最大 50）
✅ **字体样式**：表头加粗，颜色区分
✅ **编码支持**：UTF-8，完整支持中文
✅ **空值填充**：缺失数据显示为空

---

## 🔧 技术实现细节

### 关键技术点

1. **多层列索引的 Excel 导出**
   - pandas 不原生支持多层列索引 + `index=False` 的导出
   - 解决方案：使用 openpyxl 手动创建 Excel，逐行写入数据

2. **JSON 数据解析**
   ```python
   import json
   data = json.loads(section_data_json)
   # 自动处理 JSON 解析失败的情况
   ```

3. **日期过滤逻辑**
   ```python
   # statement_period 格式："2025-09-06 - 2025-09-20"
   # 提取起始日期（前 10 个字符）进行比较
   start_date = period.split(" - ")[0]
   if start_date >= user_input_date:
       # 包含该记录
   ```

4. **空值处理**
   ```python
   # 收集所有可能的字段名
   all_fields = set()
   for section in sections:
       all_fields.update(section['data'].keys())
   
   # 为每行补充缺失字段（值为 None）
   for field in all_fields:
       if field not in row_data:
           row_data[field] = None
   ```

### 依赖包

```
pandas >= 1.3.0
openpyxl >= 3.0.0
fastapi >= 0.68.0  (仅 API 路由需要)
```

---

## 📈 测试验证

### 已测试的场景

| 场景 | 结果 |
|------|------|
| 导出全部数据（2025-09-06） | ✅ 8 PDF × 7 section = 56 行 |
| 导出部分数据（2025-10-01） | ✅ 6 PDF × 7 section = 42 行 |
| 导出最近数据（2025-11-15） | ✅ 3 PDF × 7 section = 21 行 |
| 文件生成和下载 | ✅ 正常 |
| 日期格式验证 | ✅ 正确处理错误格式 |
| 空值填充 | ✅ 缺失字段显示为空 |
| Excel 格式 | ✅ 表头冻结、列宽调整正常 |

### 输出文件验证

```
✅ 文件 1: output/数据导出_20250906.xlsx (13 KB)
✅ 文件 2: output/数据导出_20251001.xlsx (11 KB)
✅ 文件 3: output/数据导出_20251115.xlsx (8.6 KB)

文件大小差异原因：不同日期的 PDF 数量和字段数不同
```

---

## 💡 使用示例

### 示例 1：简单命令行导出

```bash
$ python scripts/export_data_to_excel.py 2025-09-06
# 生成文件：output/数据导出_20250906.xlsx
```

### 示例 2：定时自动导出（cron）

```bash
# 每周日晚上 8 点自动导出过去一周的数据
0 20 * * 0 cd /project/path && python scripts/export_data_to_excel.py $(date -d '7 days ago' +\%Y-\%m-\%d)
```

### 示例 3：前端集成

```jsx
// React 组件
<button onClick={() => 
  fetch('/api/export/data-to-excel?start_date=2025-09-06', {method: 'POST'})
    .then(r => r.blob())
    .then(blob => /* 处理下载 */)
}>
  导出数据
</button>
```

### 示例 4：批量导出多个日期

```bash
#!/bin/bash
for date in 2025-09-06 2025-10-01 2025-11-15; do
  python scripts/export_data_to_excel.py $date
done
```

---

## 🎓 学习要点

### 代码架构

```
export_data_to_excel.py
├── 数据库查询层
│   ├── query_statements_by_date()
│   └── query_section_data()
├── 数据处理层
│   ├── collect_all_fields()
│   └── build_dataframe()
└── 导出层
    └── export_to_excel()
```

### 数据流向

```
用户输入 (日期字符串)
  ↓ [验证日期格式]
数据库查询 (SQL)
  ↓ [过滤、排序]
JSON 解析和展开
  ↓ [字段收集、空值填充]
DataFrame 构建
  ↓ [多层列索引]
Excel 导出 (openpyxl)
  ↓ [表头、格式、冻结]
输出文件
  ↓ [用户下载]
```

---

## 📚 相关文件导航

| 文件 | 类型 | 用途 |
|------|------|------|
| `scripts/export_data_to_excel.py` | 脚本 | 导出核心逻辑 |
| `backend/app/routes/export_router.py` | 路由 | HTTP API 接口 |
| `backend/main.py` | 应用 | FastAPI 主应用（已整合） |
| `README_导出工具.md` | 文档 | 详细说明（80+ 行） |
| `EXPORT_COMPLETE_GUIDE.md` | 文档 | 完整指南（200+ 行） |
| `EXPORT_QUICK_REFERENCE.md` | 文档 | 快速参考（100+ 行） |

---

## ✅ 清单

- ✅ 按开始日期导出数据
- ✅ Excel 文件生成（.xlsx 格式）
- ✅ 两层表头（section 名称 + 字段名）
- ✅ 所有字段名为中文
- ✅ 空值填充（缺失字段为空）
- ✅ 单个工作表（所有数据在一起）
- ✅ 命令行脚本接口
- ✅ HTTP API 接口
- ✅ 表头冻结
- ✅ 列宽自动调整
- ✅ 完整文档和示例

---

## 📞 快速帮助

### 最快的开始方式

```bash
python scripts/export_data_to_excel.py 2025-09-06
```

### 查看完整用法

```bash
cat EXPORT_COMPLETE_GUIDE.md  # 完整指南
cat EXPORT_QUICK_REFERENCE.md # 快速参考
```

### 遇到问题

1. 检查日期格式是否正确（YYYY-MM-DD）
2. 确认数据库已初始化（`python scripts/init_database_v2.py`）
3. 查看输出目录是否存在（`output/`）
4. 查阅文档中的故障排除部分

---

## 🎉 总结

实现了一个**功能完整、文档详尽、易于使用**的数据导出工具：

- **快速开始**：一条命令即可导出
- **灵活调用**：脚本 + API 两种方式
- **规范输出**：格式规范的 Excel 文件
- **完整文档**：详细说明 + 快速参考 + 完整指南

**现在就试试吧！**
