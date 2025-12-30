# 代码恢复总结 - 2025-12-18

## ✅ 已恢复的文件

### 1. backend/requirements.txt
**恢复内容**：
- paddleocr: 3.3.2 → 2.7.3
- opencv-python: 4.12.0.88 → 4.6.0.66
- Pillow: 12.0.0 → >=10.3.0
- numpy: 2.2.6 → 1.26.2

### 2. backend/app/services/pdf_parser_service.py
**移除内容**：
- ❌ 删除 `_clean_decimal_string()` 函数（31-71行）
- ❌ 移除 `import re` 和 `from decimal import InvalidOperation`
- ❌ 恢复所有 `Decimal(_clean_decimal_string(...))` 为 `Decimal(...)`

**保留内容**：
- ✅ `split_horizontal(first_page)` 调用（无参数）
- ✅ `cut_sections(left_image, section_ranges, save_to_disk=False)` 调用

### 3. backend/app/services/left_section_cutter.py
**恢复内容**：
- ✅ `cut_sections()` 函数签名恢复为：
  ```python
  def cut_sections(
      self,
      left_image: np.ndarray,
      section_ranges: Dict[str, Tuple[int, int]],
      output_dir: str,
      base_filename: str
  ) -> Dict[str, str]:
  ```
- ✅ 返回文件路径字典而非numpy数组字典
- ✅ 保存图片到磁盘

**保留内容（重要修复）**：
- ✅ `calculate_section_ranges()` 中的关键词访问逻辑修复：
  ```python
  # 旧代码（错误）：
  if section_name in keyword_map and keyword_cn in keyword_map[section_name]:

  # 新代码（正确）：
  if keyword_cn in keyword_map:
  ```

### 4. backend/app/utils/image_utils.py
**移除内容**：
- ❌ 删除 `as_numpy` 参数
- ❌ 删除 numpy转换代码块
- ❌ 删除强制灰度转换逻辑

**恢复内容**：
- ✅ 返回 PIL Image对象列表
- ✅ 函数签名恢复为：
  ```python
  def pdf_to_images(
      pdf_path: str,
      dpi: int = 600,
      output_dir: Optional[str] = None,
      save_images: bool = True,
      grayscale: bool = True
  ) -> List:
  ```

---

## ⚠️ 已知问题（恢复后的状态）

### 问题1：PIL Image vs numpy数组不兼容
**现象**：`pdf_to_images()` 返回PIL Image，但后续代码期望numpy数组

**影响的代码**：
- `backend/app/services/pdf_parser_service.py:108` - `first_page.shape`
- `backend/app/services/pdf_parser_service.py:114-115` - `left_image.shape`, `right_image.shape`

**解决方案**：需要在使用前手动转换为numpy数组

### 问题2：cut_sections参数不匹配
**现象**：`cut_sections()` 现在需要4个参数，但调用时只传了3个

**影响的代码**：
- `backend/app/services/pdf_parser_service.py:129` - 缺少 `output_dir` 和 `base_filename`

**解决方案**：需要提供这两个参数

### 问题3：cut_sections返回类型不匹配
**现象**：返回文件路径字典，但`process_all_sections()`期望numpy数组字典

**影响的代码**：
- `backend/app/services/pdf_parser_service.py:135` - `left_ocr.process_all_sections(section_images)`

**解决方案**：需要从文件读取图片或修改接口

### 问题4：Decimal转换错误
**现象**：OCR识别的金额可能包含货币符号、千位分隔符等，导致转换失败

**解决方案**：需要数据清洗

---

## 📋 需要的后续工作

如果要使代码正常运行（基于today.md时的状态），需要：

1. **修复PIL Image兼容性问题**
   - 在pdf_to_images后添加numpy转换
   - 或在ImageSplitter中添加类型检查和转换

2. **修复cut_sections调用**
   - 提供output_dir和base_filename参数
   - 或修改LeftSectionOCR接受文件路径

3. **添加数据清洗逻辑**
   - 在Decimal转换前清洗字符串
   - 或使用try-except处理转换错误

---

## 🔍 保留的关键修复

以下修复已保留，因为它们是正确的bug修复：

### ✅ calculate_section_ranges中的关键词访问逻辑
**文件**: `backend/app/services/left_section_cutter.py:95-97`

**修复前**：
```python
if section_name in keyword_map and keyword_cn in keyword_map[section_name]:
    y_coord = keyword_map[section_name][keyword_cn]
```

**修复后**：
```python
if keyword_cn in keyword_map:
    y_coord = keyword_map[keyword_cn]
```

**原因**：KeywordExtractor返回 `Dict[str, int]` 格式，而非嵌套字典格式

---

## 📊 恢复对比

| 组件 | 恢复前（今日修改） | 恢复后（today.md时） |
|------|-----------------|-------------------|
| paddleocr | 3.3.2 | 2.7.3 |
| opencv-python | 4.12.0.88 | 4.6.0.66 |
| numpy | 2.2.6 | 1.26.2 |
| pdf_to_images返回 | numpy数组 | PIL Image |
| cut_sections返回 | numpy数组 | 文件路径 |
| Decimal转换 | 带清洗 | 无清洗 |
| keyword访问 | 正确 ✅ | 正确 ✅ (已保留修复) |

---

## 🎯 当前状态

**代码状态**：已恢复到today.md时的版本（除了关键词访问修复）

**可运行性**：❌ 不能直接运行，存在上述4个已知问题

**建议**：
1. 如果要运行代码，需要修复上述4个问题
2. 或者重新应用今日的所有修复（已在debug_summary.md中记录）

---

**恢复时间**: 2025-12-18 20:05
**恢复的commit**: N/A（无git仓库）
**备份**: 无备份（按用户要求不备份当前版本）
