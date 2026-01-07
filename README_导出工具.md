# 数据导出工具使用指南

## 概述

`export_data_to_excel.py` 是一个后端数据导出工具，用于将数据库中的 PDF 解析数据导出到 Excel 文件。

## 功能说明

### 导出流程
1. **接受开始日期参数**：用户输入一个开始日期（格式：YYYY-MM-DD）
2. **查询数据库**：查询 statements 表中 statement_period 起始日期 >= 输入日期的所有记录
3. **提取结构化数据**：从 section_data 表中获取这些 PDF 对应的所有 section 数据
4. **解析 JSON**：将每个 section 中的 JSON 数据解析为列
5. **生成 Excel**：创建表格，所有缺失的字段用空值填充

### 数据结构

**Excel 表格特点：**
- **表头分两行**：
  - 第一行：板块名称（header、footer、销售、退款、沃尔玛配送服务(WFS)、其他活动、right_section）
  - 第二行：各板块内的具体字段名
- **数据行**：每行对应一个 PDF 的一个 section 记录
- **前两列**：
  - PDF 名称：源 PDF 文件名称
  - 对账周期：该 PDF 的对账周期范围（如 "2025-09-06 - 2025-09-20"）
- **其他列**：各 section 的字段值，缺失值显示为空
- **表头冻结**：前两行表头被冻结，便于在大数据量时查看列名

## 使用方法

### 基本用法

```bash
python scripts/export_data_to_excel.py <start_date>
```

**参数说明：**
- `<start_date>`：开始日期，格式必须为 `YYYY-MM-DD`（例如：`2025-09-06`）

### 示例

```bash
# 导出 2025-09-06 及之后的所有数据
python scripts/export_data_to_excel.py 2025-09-06

# 导出 2025-10-01 及之后的所有数据
python scripts/export_data_to_excel.py 2025-10-01

# 导出 2025-11-01 及之后的所有数据
python scripts/export_data_to_excel.py 2025-11-01
```

### 指定输出文件（可选）

```bash
python scripts/export_data_to_excel.py <start_date> <output_file>
```

**示例：**

```bash
# 导出到指定的文件
python scripts/export_data_to_excel.py 2025-09-06 ~/Downloads/walmart_data.xlsx
```

## 输出文件

### 默认位置
如果不指定输出文件，会自动保存到：
```
/project_root/output/数据导出_YYYYMMDD.xlsx
```

**示例：**
- 输入 `2025-09-06` → 输出文件名：`数据导出_20250906.xlsx`
- 输入 `2025-10-01` → 输出文件名：`数据导出_20251001.xlsx`

### 文件内容

**Excel 文件包含：**
- **工作表名**：`数据导出`
- **数据行数**：每个导出的 section 一行（通常 8 个 PDF × 7 个 section = 56 行）
- **数据列数**：基本信息（2 列）+ 所有 section 的所有字段（动态，通常 38 列）

**表头格式示例：**

| 基本信息 | 基本信息 | footer | footer | header | header | header | header | header | right_section | right_section | ... |
|---------|---------|--------|--------|--------|--------|--------|--------|--------|---------------|---------------|-----|
| PDF 名称 | 对账周期 | 向您支付的金额 | 期末余额 | 向您支付的金额 | 回款等待 | 备用金 | 期初余额 | 统计区间 | 付款方式 | 状态 | ... |

## 数据说明

### 包含的 Section 类型

| Section 名称 | 说明 | 典型字段 |
|-------------|------|---------|
| `header` | PDF 头部信息 | 对账周期、向您支付的金额、期初余额、备用金、回款等待 |
| `footer` | PDF 底部信息 | 向您支付的金额、期末余额 |
| `销售` | 销售数据 | 产品价格、佣金、运输、扣缴税款等 |
| `退款` | 退款数据 | 产品价格、佣金、已收税净额、扣缴税款等 |
| `沃尔玛配送服务(WFS)` | WFS 物流费用 | WFS仓储费、WFS配送费、WFS运输税退款等 |
| `其他活动` | 其他活动 | 沃尔玛产品广告、总计等 |
| `right_section` | 右侧信息 | 状态、付款方式等 |

### 字段名称特点

- **所有字段名均为中文**
- **多行字段名**：某些长字段名（如 "T沃尔玛出资的节余总额"）可能换行显示
- **缺失值处理**：如果某个 PDF 的某个 section 不含某个字段，对应单元格为空

## 工作流程示例

### 场景：导出最近三周的所有数据

```bash
# 假设今天是 2025-12-20，想导出最近三周（从 2025-11-29 开始）的数据
python scripts/export_data_to_excel.py 2025-11-29
```

**输出：**
```
开始导出数据，起始日期: 2025-11-29

步骤 1/4: 查询 statements 表...
  ✓ 找到 3 条记录

步骤 2/4: 查询 section_data 表...
  ✓ 找到 21 条 section 记录

步骤 3/4: 收集所有字段...
  ✓ 找到 7 个板块，共 38 个字段

步骤 4/4: 构建 Excel 数据...
  ✓ DataFrame 尺寸: 21 行 × 40 列

保存到 Excel 文件: /project_root/output/数据导出_20251129.xlsx
✓ 数据导出成功
```

## 常见问题

### Q1：如何导出特定日期范围的数据？

**当前脚本只支持"从某日期开始"的查询。** 如果需要特定日期范围，可以：
1. 分别导出起始和结束日期的数据
2. 在 Excel 中手动筛选所需行

**改进方案**（可选）：修改脚本支持日期范围参数。

### Q2：为什么某些单元格是空的？

这是正常的。Excel 遵循"空值填充"策略：
- 如果某个 PDF 的某个 section 没有包含某个字段，对应单元格为空
- 例如：footer 通常不包含"统计区间"字段，所以这些单元格为空

### Q3：表头为什么分两行？

这样做的好处：
1. **清晰的分类**：第一行显示数据所属的 section
2. **便于筛选**：可以按 section 或字段名筛选
3. **便于冻结**：冻结前两行表头，便于查看大数据量

### Q4：如何更新脚本以支持新功能？

常见的扩展需求：
1. **添加日期范围查询**：修改 `query_statements_by_date()` 函数
2. **按 section 分割工作表**：修改 Excel 写入逻辑
3. **支持更多导出格式**：添加 CSV、JSON 等导出方式

## 技术细节

### 依赖包

```
pandas >= 1.3.0
openpyxl >= 3.0.0
```

### 数据库查询逻辑

1. **查询语句表**：
   ```sql
   SELECT id, pdf_name, statement_period
   FROM statements
   WHERE LEFT(statement_period, 10) >= ?
   ORDER BY statement_period ASC
   ```

2. **查询分段数据**：
   ```sql
   SELECT statement_id, section_name, data
   FROM section_data
   WHERE statement_id IN (...)
   ORDER BY statement_id, section_name
   ```

### 数据处理流程

1. 解析 `statement_period`：提取起始日期
2. 过滤 statements：只保留起始日期 >= 输入日期的记录
3. 递归查询 section_data
4. 解析每个 section 的 JSON 数据
5. 收集所有字段名（并集）
6. 构建 DataFrame（缺失值用 None/NaN 表示）
7. 导出到 Excel（手动处理多层表头）

## 脚本文件

**位置**：`scripts/export_data_to_excel.py`

**主要函数**：
- `parse_period_start_date()`：解析对账周期字符串
- `query_statements_by_date()`：查询符合条件的 statements
- `query_section_data()`：查询 section_data
- `collect_all_fields()`：收集所有字段名
- `build_dataframe()`：构建 DataFrame
- `export_to_excel()`：导出到 Excel
- `main()`：命令行入口

## 更新日志

### 2026-01-06
- ✅ 完成初始版本
- ✅ 支持两行表头（section_name + 字段名）
- ✅ 支持空值填充
- ✅ 支持表头冻结
- ✅ 支持自动列宽调整
