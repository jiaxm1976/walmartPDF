# OCR识别调试总结 - 2025-12-18

## 🎯 当前状态

### 已完成的修复
1. ✅ **依赖版本问题** - 更新backend/requirements.txt匹配虚拟环境
   - paddleocr: 2.7.3 → 3.3.2
   - opencv-python: 4.6.0.66 → 4.12.0.88
   - Pillow: >=10.3.0 → 12.0.0
   - numpy: 1.26.2 → 2.2.6

2. ✅ **PIL Image vs numpy数组问题** - 修改pdf_to_images函数
   - 添加as_numpy参数（默认True）
   - 自动将PIL Image转换为numpy数组
   - 添加强制灰度转换（修复pdf2image的grayscale参数不生效问题）

3. ✅ **函数参数不匹配** - 修复LeftSectionCutter.cut_sections
   - 修改为可选参数：output_dir, base_filename, save_to_disk
   - 默认返回Dict[str, np.ndarray]而非保存文件
   - pdf_parser_service调用时使用save_to_disk=False

4. ✅ **Decimal转换错误** - 添加金额清洗函数
   - 创建_clean_decimal_string函数
   - 处理OCR识别的货币符号、千位分隔符、非法字符
   - 批量更新所有Decimal转换调用

5. ✅ **ImageSplitter参数错误** - 移除split_ratio参数
   - split_horizontal方法不接受split_ratio参数
   - 修改pdf_parser_service调用

### 核心问题：关键词识别失败

**现象**：
```
2025-12-18 19:24:24,530 - app.services.keyword_extractor - INFO - 提取到 8 个关键词
2025-12-18 19:24:24,530 - app.services.left_section_cutter - WARNING - 跳过板块 [header]（关键词未找到）
2025-12-18 19:24:24,530 - app.services.left_section_cutter - WARNING - 跳过板块 [sales]（关键词未找到）
2025-12-18 19:24:24,530 - app.services.left_section_cutter - WARNING - 跳过板块 [refund]（关键词未找到）
...
2025-12-18 19:24:24,530 - app.services.left_section_cutter - INFO - 板块范围计算完成，共0个有效板块
```

**分析**：
1. OCR识别到了65个文本块
2. 提取到了8个关键词
3. 但这8个关键词无法匹配任何预定义的7个板块名称
4. 导致0个有效板块被切分

**可能原因**：
1. 关键词定义与OCR识别结果不匹配
2. 关键词匹配逻辑有问题
3. 坐标校准数据不适配当前DPI（使用300 DPI但校准数据可能是其他DPI）

---

## 🔍 需要调试的内容

### 1. 查看关键词提取逻辑
文件：`backend/app/services/keyword_extractor.py`

需要确认：
- 预定义的关键词列表是什么？
- 关键词匹配的容错规则（中文、英文、部分匹配）
- OCR识别结果的格式

### 2. 查看板块切分逻辑
文件：`backend/app/services/left_section_cutter.py`

需要确认：
- 每个板块需要的关键词名称
- 如何从keyword_map中查找关键词

### 3. 使用可视化工具
使用现有工具查看OCR识别结果：
```bash
python scripts/quick_visualize.py PdfData/MP_01142025_statement_summary.pdf
```

这个工具可以：
- 显示OCR识别到的所有文本和位置
- 标记关键词位置
- 生成可视化图片

### 4. 检查坐标校准
文件：`calibration_data/ocr_calibration_300dpi.pkl`

可能需要：
- 重新生成校准数据
- 或者禁用坐标校准测试

---

## 📝 建议的调试步骤

### Step 1: 查看OCR实际识别结果
```bash
# 使用可视化工具查看
python scripts/quick_visualize.py PdfData/MP_01142025_statement_summary.pdf
```

输出应该包含：
- 所有识别到的文本
- 文本的坐标位置
- 关键词标记

### Step 2: 对比关键词定义
查看KeywordExtractor和LeftSectionCutter中定义的关键词，确认是否匹配PDF实际内容。

### Step 3: 临时禁用坐标校准
修改OCR引擎，暂时不使用校准数据，看是否影响识别结果。

### Step 4: 调整DPI设置
当前使用300 DPI，可以尝试：
- 降低到150 DPI（更快但可能识别率下降）
- 提高到600 DPI（更慢但识别率可能提升）

---

## 📊 测试命令

### 快速可视化测试
```bash
python scripts/quick_visualize.py PdfData/MP_01142025_statement_summary.pdf
```

### 完整API测试
```bash
# 确保API服务运行中
curl http://localhost:8000/health

# 运行测试
source venv/bin/activate
python scripts/test_parse_pipeline.py
```

### 查看详细日志
```bash
tail -f /tmp/api_server.log
```

---

## 🔧 已修改的文件

1. `backend/requirements.txt` - 更新依赖版本
2. `backend/app/utils/image_utils.py` - 添加as_numpy参数和强制灰度转换
3. `backend/app/services/left_section_cutter.py` - 修改cut_sections返回类型
4. `backend/app/services/pdf_parser_service.py` - 添加_clean_decimal_string函数，修复调用
5. API服务已重启（最新代码）

---

## 📌 下一步行动

**优先级P0**：
1. 运行quick_visualize.py查看实际OCR识别情况
2. 确认关键词定义是否正确
3. 修复关键词匹配逻辑

**优先级P1**：
4. 验证坐标校准是否正常工作
5. 优化OCR识别参数（DPI、预处理等）

**优先级P2**：
6. 完善错误处理和日志
7. 编写单元测试

---

**创建时间**: 2025-12-18 19:35
**API服务状态**: 运行中（端口8000）
**测试PDF**: PdfData/MP_01142025_statement_summary.pdf
