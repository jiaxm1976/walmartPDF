# 完整使用说明

## 功能概述

创建了一个后端数据导出工具，可以按照输入的开始日期，从数据库中导出 PDF 解析数据到 Excel 文件。

## 使用方式

### 方式 1：命令行脚本（推荐）

#### 基本用法

```bash
python scripts/export_data_to_excel.py <start_date>
```

**参数说明：**
- `<start_date>`：开始日期，格式必须为 `YYYY-MM-DD`

#### 示例

```bash
# 导出 2025-09-06 及之后的所有数据
python scripts/export_data_to_excel.py 2025-09-06

# 导出 2025-10-01 及之后的所有数据
python scripts/export_data_to_excel.py 2025-10-01

# 导出 2025-11-15 及之后的所有数据
python scripts/export_data_to_excel.py 2025-11-15

# 导出到指定文件
python scripts/export_data_to_excel.py 2025-09-06 ~/Downloads/walmart_data.xlsx
```

#### 输出示例

```
开始导出数据，起始日期: 2025-09-06

步骤 1/4: 查询 statements 表...
  ✓ 找到 8 条记录
步骤 2/4: 查询 section_data 表...
  ✓ 找到 56 条 section 记录
步骤 3/4: 收集所有字段...
  ✓ 找到 7 个板块，共 38 个字段
    - footer: 2 个字段
    - header: 5 个字段
    - right_section: 2 个字段
    - 其他活动: 2 个字段
    - 沃尔玛配送服务(WFS): 8 个字段
    - 退款: 9 个字段
    - 销售: 10 个字段
步骤 4/4: 构建 Excel 数据...
  ✓ DataFrame 尺寸: 56 行 × 40 列

保存到 Excel 文件: /Users/jiaxinming/JxmWork/walmart-a/output/数据导出_20250906.xlsx
✓ 数据导出成功

文件路径: /Users/jiaxinming/JxmWork/walmart-a/output/数据导出_20250906.xlsx
```

### 方式 2：FastAPI HTTP 接口

#### 启动 API 服务

```bash
# 启动 API 服务（开发模式）
python backend/main.py

# 或使用 uvicorn
uvicorn backend.main:app --reload --port 8000
```

#### API 端点 1：导出数据

**请求：**
```http
POST /api/export/data-to-excel?start_date=2025-09-06
```

**参数：**
- `start_date`：开始日期，格式为 YYYY-MM-DD

**响应：**
- 直接返回 Excel 文件，浏览器会自动下载

**示例（curl）：**
```bash
curl -X POST "http://localhost:8000/api/export/data-to-excel?start_date=2025-09-06" \
  -o walmart_data.xlsx
```

**示例（Python）：**
```python
import requests

url = "http://localhost:8000/api/export/data-to-excel"
params = {"start_date": "2025-09-06"}
response = requests.post(url, params=params)

if response.status_code == 200:
    with open("walmart_data.xlsx", "wb") as f:
        f.write(response.content)
    print("导出成功")
else:
    print(f"导出失败: {response.json()}")
```

**示例（JavaScript/Fetch）：**
```javascript
const startDate = "2025-09-06";

fetch(`http://localhost:8000/api/export/data-to-excel?start_date=${startDate}`, {
  method: "POST"
})
  .then(response => response.blob())
  .then(blob => {
    // 创建下载链接
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `数据导出_${startDate.replace(/-/g, "")}.xlsx`;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    a.remove();
  })
  .catch(error => console.error("导出失败:", error));
```

#### API 端点 2：检查导出状态（不生成文件）

**请求：**
```http
GET /api/export/data-to-excel/status?start_date=2025-09-06
```

**参数：**
- `start_date`：开始日期，格式为 YYYY-MM-DD

**响应示例：**
```json
{
  "status": "success",
  "start_date": "2025-09-06",
  "pdf_count": 8,
  "section_count": 56,
  "message": "找到 8 个 PDF，56 个 section 记录"
}
```

**示例（curl）：**
```bash
curl -X GET "http://localhost:8000/api/export/data-to-excel/status?start_date=2025-09-06"
```

---

## 导出数据结构说明

### Excel 文件结构

**表头特点：**
- **两层表头**：
  - 第一层：板块名称（section_name）
  - 第二层：具体字段名（field_name）
- **所有字段名均为中文**
- **表头冻结**：前两行被冻结，便于查看大数据量

**数据列：**

| 列序号 | 列名 | 说明 |
|-------|------|------|
| 1 | PDF 名称 | 源 PDF 文件名 |
| 2 | 对账周期 | PDF 的对账周期，格式："2025-09-06 - 2025-09-20" |
| 3+ | section 字段 | 各 section 的具体字段值 |

**数据行数：**
- 每个 PDF 的每个 section 占一行
- 默认 8 个 PDF × 7 个 section = 56 行

### 包含的 Section 类型

| Section | 中文名称 | 说明 | 字段示例 |
|---------|---------|------|---------|
| `header` | 头部信息 | PDF 开头的统计信息 | 对账周期、向您支付的金额、期初余额、备用金、回款等待 |
| `footer` | 底部信息 | PDF 结尾的汇总信息 | 向您支付的金额、期末余额 |
| `销售` | 销售 | 产品销售相关数据 | 产品价格、佣金、运输、扣缴税款等 |
| `退款` | 退款 | 退款相关数据 | 产品价格、佣金、已收税净额、扣缴税款等 |
| `沃尔玛配送服务(WFS)` | WFS 物流 | 沃尔玛物流费用 | WFS仓储费、WFS配送费、WFS运输税退款等 |
| `其他活动` | 其他活动 | 其他类型的费用或收入 | 沃尔玛产品广告、总计 |
| `right_section` | 右侧信息 | PDF 右侧的补充信息 | 状态、付款方式等 |

### 空值处理

- 如果某个 PDF 的某个 section 不包含某个字段，对应单元格为空（**空值填充**）
- 这是正常的，不表示数据错误

**示例：**
- footer section 通常不包含"统计区间"字段，所以这个单元格为空
- 某些 PDF 的某个 section 可能包含特殊字段，这些字段会在所有行中显示，缺失行用空值填充

---

## 脚本文件说明

### 主脚本文件

**位置：** `scripts/export_data_to_excel.py`

**主要函数：**

| 函数 | 功能 |
|------|------|
| `parse_period_start_date()` | 从"2025-09-06 - 2025-09-20"格式中提取起始日期 |
| `query_statements_by_date()` | 查询起始日期 >= 指定日期的所有 PDF 记录 |
| `query_section_data()` | 查询指定 PDF 的所有 section 数据 |
| `collect_all_fields()` | 收集所有 section 中的所有字段名 |
| `build_dataframe()` | 构建 DataFrame，使用多层列索引 |
| `export_to_excel()` | 导出到 Excel 文件 |
| `main()` | 命令行入口函数 |

**执行流程：**

```
输入：start_date (2025-09-06)
  ↓
query_statements_by_date()
  ↓ 获取符合条件的 statement 记录
query_section_data()
  ↓ 获取这些 statement 的 section 数据
collect_all_fields()
  ↓ 收集所有字段名
build_dataframe()
  ↓ 构建 DataFrame（处理多层列索引）
export_to_excel()
  ↓ 手动创建 Excel，写入两层表头
输出：Excel 文件
```

### API 路由文件

**位置：** `backend/app/routes/export_router.py`

**路由说明：**

| 路由 | 方法 | 功能 |
|------|------|------|
| `/api/export/data-to-excel` | POST | 导出数据到 Excel |
| `/api/export/data-to-excel/status` | GET | 检查导出数据状态（不生成文件） |

---

## 常见用场景

### 场景 1：每周导出一次数据

```bash
# 导出最近一周的数据（假设今天是 2025-12-20）
python scripts/export_data_to_excel.py 2025-12-13
```

### 场景 2：导出特定时间段的数据

```bash
# 导出 10 月份开始的数据
python scripts/export_data_to_excel.py 2025-10-01
```

### 场景 3：从前端网页导出

1. 用户在前端输入开始日期
2. 前端调用 API `/api/export/data-to-excel?start_date=2025-09-06`
3. 后端返回 Excel 文件
4. 浏览器自动下载文件

**前端代码示例（React）：**

```jsx
import React, { useState } from 'react';

function ExportData() {
  const [startDate, setStartDate] = useState('2025-09-06');
  const [loading, setLoading] = useState(false);

  const handleExport = async () => {
    setLoading(true);
    try {
      const response = await fetch(
        `/api/export/data-to-excel?start_date=${startDate}`,
        { method: 'POST' }
      );
      
      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `数据导出_${startDate.replace(/-/g, '')}.xlsx`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        a.remove();
        alert('导出成功！');
      } else {
        alert('导出失败！');
      }
    } catch (error) {
      console.error('导出错误:', error);
      alert('导出出错！');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <input 
        type="date" 
        value={startDate} 
        onChange={(e) => setStartDate(e.target.value)}
      />
      <button onClick={handleExport} disabled={loading}>
        {loading ? '导出中...' : '导出数据'}
      </button>
    </div>
  );
}

export default ExportData;
```

---

## 技术细节

### 数据库查询逻辑

**步骤 1：查询 statements 表**

```sql
SELECT id, pdf_name, statement_period
FROM statements
WHERE statement_period >= ? 
ORDER BY statement_period ASC
```

其中 `statement_period` 格式为 "2025-09-06 - 2025-09-20"，脚本提取前 10 个字符（起始日期）进行比较。

**步骤 2：查询 section_data 表**

```sql
SELECT statement_id, section_name, data
FROM section_data
WHERE statement_id IN (...)
ORDER BY statement_id, section_name
```

**步骤 3：处理 JSON 数据**

- 从 `data` 列（JSON）解析字段和值
- 收集所有可能的字段名（并集）
- 为缺失的字段填充 None/NaN

### 导出格式选择

**为什么选择 Excel 而不是 CSV？**

1. **两层表头**：CSV 无法原生支持多层表头
2. **格式保留**：Excel 支持字体、颜色、冻结等格式
3. **易于阅读**：Excel 在 Office 软件中打开效果最佳

### 多层列索引处理

由于 pandas 不支持多层列索引且 `index=False` 的直接导出，脚本采用手动方式：

1. 使用 openpyxl 创建新的 Workbook
2. 手动写入第一行表头（section_name）
3. 手动写入第二行表头（field_name）
4. 逐行写入数据
5. 设置格式（颜色、冻结、列宽等）

---

## 故障排除

### 错误：日期格式不正确

```
错误: 日期格式不正确，应为 'YYYY-MM-DD'，您输入的是 '09/06/2025'
```

**解决：** 使用正确的日期格式 `YYYY-MM-DD`

```bash
# 错误
python scripts/export_data_to_excel.py 09/06/2025

# 正确
python scripts/export_data_to_excel.py 2025-09-06
```

### 错误：没有找到符合条件的数据

```
警告: 没有找到符合条件的数据
```

**原因：** 输入的日期太晚，没有数据符合条件

**解决：** 检查数据库中的日期范围

```bash
# 查看数据库中有哪些日期
python scripts/export_data_to_excel.py 2025-01-01
```

### 错误：数据库文件不存在

```
错误: 数据库文件不存在: /path/to/walmart_pdf_parser.db
```

**解决：** 先初始化数据库

```bash
python scripts/init_database_v2.py
```

---

## 后续改进建议

1. **支持日期范围查询**
   ```bash
   python scripts/export_data_to_excel.py 2025-09-06 2025-12-31
   ```

2. **支持多个 Excel 工作表**
   - 每个 section 一个工作表
   - 或者按 PDF 分工作表

3. **支持更多导出格式**
   - CSV（逗号分隔值）
   - JSON（原始数据格式）
   - Parquet（大数据分析）

4. **添加筛选和聚合功能**
   - 筛选特定 section
   - 按板块汇总数据
   - 计算统计值（总和、平均值等）

5. **性能优化**
   - 为大数据量添加分页导出
   - 添加进度条实时反馈
   - 支持后台任务队列

---

## 相关文件

- 主脚本：`scripts/export_data_to_excel.py`
- API 路由：`backend/app/routes/export_router.py`
- 主应用：`backend/main.py`（已注册路由）
- 使用说明：`README_导出工具.md`

---

## 总结

✅ **已实现功能：**
- ✅ 按开始日期导出数据
- ✅ 两层表头（section_name + 字段名）
- ✅ 所有字段名为中文
- ✅ 空值填充
- ✅ 命令行脚本接口
- ✅ HTTP API 接口
- ✅ 自动列宽调整
- ✅ 表头冻结

**使用方式：**
1. **命令行**：`python scripts/export_data_to_excel.py 2025-09-06`
2. **HTTP API**：`POST /api/export/data-to-excel?start_date=2025-09-06`

**生成的 Excel 文件：**
- 默认位置：`output/数据导出_YYYYMMDD.xlsx`
- 包含所有 section 的所有字段
- 缺失值用空值填充
