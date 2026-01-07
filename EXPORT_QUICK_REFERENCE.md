# 数据导出 - 快速参考

## 最简单的使用方式

```bash
python scripts/export_data_to_excel.py 2025-09-06
```

✅ 完成！Excel 文件已生成到 `output/数据导出_20250906.xlsx`

---

## 完整命令参考

| 需求 | 命令 |
|------|------|
| 导出 2025-09-06 的数据 | `python scripts/export_data_to_excel.py 2025-09-06` |
| 导出 2025-10-01 的数据 | `python scripts/export_data_to_excel.py 2025-10-01` |
| 导出到自定义路径 | `python scripts/export_data_to_excel.py 2025-09-06 ~/Downloads/data.xlsx` |
| 使用 API（需启动服务器） | `curl -X POST "http://localhost:8000/api/export/data-to-excel?start_date=2025-09-06" -o data.xlsx` |

---

## 输出文件

- **默认位置**：`output/数据导出_YYYYMMDD.xlsx`
- **文件格式**：Excel (.xlsx)
- **表头**：2行（section_name + 字段名）
- **数据行数**：取决于符合条件的 PDF 数量（每个 PDF × 7 个 section）
- **编码**：UTF-8，支持中文

---

## Excel 文件结构

```
┌─────────────────┬─────────────────┬──────────┬──────────┬─────────────┐
│  基本信息        │  基本信息        │  footer  │  footer  │   header    │
│  PDF 名称        │  对账周期        │ 向您支付  │ 期末余额  │ 对账周期    │
├─────────────────┼─────────────────┼──────────┼──────────┼─────────────┤
│ MP_0923...pdf   │ 2025-09-06...   │ 868.55   │ 0.0      │ 2025-09-06..│
│ MP_0923...pdf   │ 2025-09-06...   │          │          │             │
│ ...             │ ...             │ ...      │ ...      │ ...         │
└─────────────────┴─────────────────┴──────────┴──────────┴─────────────┘
```

---

## 关键特性

✅ **两层表头**
- 第一行：数据所属的板块（section）
- 第二行：具体的字段名

✅ **中文字段名**
- 所有列名都是中文
- 易于理解和使用

✅ **空值填充**
- 缺失的数据显示为空
- 没有错误行

✅ **自动格式化**
- 表头冻结（前 2 行）
- 列宽自动调整
- 表头颜色区分

---

## 常见问题

### Q：为什么某些单元格是空的？
**A：** 这是正常的。如果某个 PDF 的某个 section 没有某个字段，对应单元格为空。这不是错误。

### Q：如何导出特定日期范围的数据？
**A：** 当前脚本只支持"从某日期开始"的查询。可以：
1. 先导出起始日期的数据
2. 在 Excel 中筛选所需日期范围

### Q：Excel 文件在哪里？
**A：** 默认保存在 `output/数据导出_YYYYMMDD.xlsx`

### Q：可以自动化这个过程吗？
**A：** 可以！在 cron（Linux/Mac）或任务计划（Windows）中添加定时任务：
```bash
0 0 * * 0 cd /project/path && python scripts/export_data_to_excel.py 2025-01-01
```

---

## 包含的数据

### 7 个 Section（板块）

| 名称 | 字段数 | 典型字段 |
|------|--------|---------|
| header（头部） | 5 | 对账周期、向您支付的金额、期初余额 |
| footer（底部） | 2 | 向您支付的金额、期末余额 |
| 销售 | 10 | 产品价格、佣金、运输 |
| 退款 | 9 | 产品价格、佣金、扣缴税款 |
| 沃尔玛配送服务(WFS) | 8 | WFS 仓储费、配送费、运输税退款 |
| 其他活动 | 2 | 沃尔玛产品广告、总计 |
| right_section（右侧） | 2 | 状态、付款方式 |

**总计：** 38 个字段

---

## 故障排除

### 错误：日期格式不正确
```
python scripts/export_data_to_excel.py 09-06-2025  ❌ 错误
python scripts/export_data_to_excel.py 2025-09-06  ✅ 正确
```

### 错误：数据库不存在
```bash
# 先初始化数据库
python scripts/init_database_v2.py
```

### 错误：没有找到符合条件的数据
- 检查日期是否正确（格式 YYYY-MM-DD）
- 确认数据库中有该日期的数据
- 尝试更早的日期

---

## Python API 使用

```python
from scripts.export_data_to_excel import export_to_excel

# 导出数据
excel_file = export_to_excel("2025-09-06")
print(f"导出成功: {excel_file}")
```

---

## HTTP API 使用

### 导出数据
```bash
curl -X POST "http://localhost:8000/api/export/data-to-excel?start_date=2025-09-06" \
  -o data.xlsx
```

### 检查数据统计
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

## 文件列表

| 文件 | 用途 |
|------|------|
| `scripts/export_data_to_excel.py` | 主导出脚本 |
| `backend/app/routes/export_router.py` | HTTP API 路由 |
| `backend/main.py` | FastAPI 主应用（已注册路由） |
| `README_导出工具.md` | 详细使用说明 |
| `EXPORT_COMPLETE_GUIDE.md` | 完整指南 |

---

## 总结

✅ **已完成**
- ✅ 按开始日期导出数据
- ✅ 两层表头结构
- ✅ 中文字段名
- ✅ 空值填充
- ✅ 命令行 + HTTP API 两种调用方式
- ✅ 自动格式化（冻结表头、调整列宽）

**现在就试试吧！**
```bash
python scripts/export_data_to_excel.py 2025-09-06
```
