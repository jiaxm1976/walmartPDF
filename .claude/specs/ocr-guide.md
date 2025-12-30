# OCR识别详细策略指南（精简版）

> **适用场景**: Walmart PDF报表识别 | **OCR引擎**: PaddleOCR 2.7.0.3
> **当前重点**: 坐标校准优化 | **更新**: 2025-12-16 | **版本**: v4.0

---

## 🎯 快速参考

### DPI选择（3秒决策）
```
清晰PDF  → 300 DPI (推荐, 38秒/3页, 96%准确率)
模糊PDF  → 400 DPI (62秒/3页, 97%准确率)
极模糊   → 600 DPI (105秒/3页, 救急用)
```

### 坐标校准公式
```python
y_pdf = (y_ocr * 72 / dpi) + page_margin
# 默认: dpi=300, page_margin=12px
```

### 快速排查
```
识别率低(<80%) → 提高DPI或预处理图像
速度慢(>30秒/页) → 启用GPU或降低DPI
内存高(>8GB) → 逐页处理+gc.collect()
坐标偏移(>10px) → 重新生成校准文件
```

---

## 📐 坐标校准详解（当前P0任务）

### 问题与原因
**核心问题**: OCR坐标与PDF实际坐标偏差约50px
**根本原因**:
1. DPI转换误差 (300 DPI → 72 DPI)
2. 页边距未校准 (默认12px)
3. 浮点精度累积误差

### 线性校准（推荐）

```python
def calibrate_coordinates(x_ocr, y_ocr, dpi=300, margin=12):
    """坐标校准函数.

    Args:
        x_ocr: OCR识别的X坐标（基于图像DPI）
        y_ocr: OCR识别的Y坐标
        dpi: 图像DPI（默认300）
        margin: 页边距（默认12px）

    Returns:
        (x_pdf, y_pdf): 校准后的PDF坐标

    Example:
        >>> calibrate_coordinates(500, 500, dpi=300, margin=12)
        (132, 132)
    """
    # DPI转换比例: 300 DPI → 72 DPI = 72/300 = 0.24
    scale = 72 / dpi

    x_pdf = (x_ocr * scale) + margin
    y_pdf = (y_ocr * scale) + margin

    return x_pdf, y_pdf
```

### 校准工作流

```bash
# 1. 生成校准数据
python scripts/create_calibration.py \
    --input PdfData/sample.pdf \
    --dpi 300 \
    --output calibration_data/ocr_calibration_300dpi.pkl

# 2. 可视化验证
python scripts/quick_visualize.py PdfData/sample.pdf

# 3. 检查偏差
# 偏差<5px → 优秀
# 5-10px → 良好
# 10-20px → 可接受（需优化）
# >20px → 必须重新校准
```

### 校准代码集成

```python
from backend.app.services.ocr_engine import OCREngine
import pickle

# 加载校准函数
with open("calibration_data/ocr_calibration_300dpi.pkl", "rb") as f:
    calibrate_func = pickle.load(f)

# 初始化OCR引擎
engine = OCREngine(use_gpu=False)
engine.load_calibration(calibrate_func)

# 识别时自动应用校准
result = engine.recognize("page1.png", dpi=300)
# result["boxes"]中的坐标已校准
```

### 常见问题排查

**问题1: 校准后坐标仍偏移>10px**

可能原因:
- PDF有旋转（检查PDF元数据）
- DPI不匹配（校准文件DPI ≠ 识别DPI）
- 不同页边距不同

解决方案:
```python
# 检查PDF旋转
import PyPDF2
with open("sample.pdf", "rb") as f:
    pdf = PyPDF2.PdfReader(f)
    rotation = pdf.pages[0].get("/Rotate", 0)
    if rotation != 0:
        print(f"警告: PDF旋转{rotation}度")
```

**问题2: X坐标和Y坐标偏差不同**

Y轴偏差通常大于X轴，使用不同校准参数:
```python
x_pdf = x_ocr * 72 / 300  # X轴不加offset
y_pdf = (y_ocr * 72 / 300) + 12  # Y轴加offset
```

---

## 🚀 性能优化速查

### GPU加速（最有效，提速5倍）
```python
import paddle
print(f"GPU可用: {paddle.is_compiled_with_cuda()}")

engine = OCREngine(use_gpu=True)
# CPU: 15秒/页 → GPU: 3秒/页
```

### 缓存机制（提速1500倍）
```python
class OCRCache:
    def __init__(self, cache_dir="cache/ocr"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def get_cache_key(self, image_path, dpi):
        with open(image_path, "rb") as f:
            file_hash = hashlib.md5(f.read()).hexdigest()
        return f"{file_hash}_dpi{dpi}.pkl"

    def get(self, image_path, dpi):
        cache_file = self.cache_dir / self.get_cache_key(image_path, dpi)
        if cache_file.exists():
            with open(cache_file, "rb") as f:
                return pickle.load(f)
        return None

    def set(self, image_path, dpi, result):
        cache_file = self.cache_dir / self.get_cache_key(image_path, dpi)
        with open(cache_file, "wb") as f:
            pickle.dump(result, f)

# 使用
cache = OCRCache()
cached = cache.get(image_path, 300)
if cached:
    return cached  # 0.01秒（缓存命中）
else:
    result = engine.recognize(image_path, dpi=300)  # 15秒（首次识别）
    cache.set(image_path, 300, result)
```

### 内存优化（节省75%内存）
```python
import gc

def process_pdf_memory_efficient(pdf_path, dpi=300):
    """逐页处理+及时释放."""
    results = []
    for page_num in range(page_count):
        page_img = convert_page(pdf_path, page_num, dpi)
        result = engine.recognize(page_img, dpi=dpi)
        results.append(result)

        del page_img  # 立即释放

        if (page_num + 1) % 5 == 0:
            gc.collect()  # 每5页垃圾回收

    return results
# 内存: 8GB → 2GB
```

### 并行处理（提速3.75倍）
```python
from concurrent.futures import ProcessPoolExecutor

def parallel_ocr(pdf_list, workers=4):
    """CPU多核并行处理."""
    def process_one(pdf_path):
        engine = OCREngine(use_gpu=False)
        return engine.recognize(pdf_path, dpi=300)

    with ProcessPoolExecutor(max_workers=workers) as executor:
        results = list(executor.map(process_one, pdf_list))

    return results
# 串行: 1500秒 → 并行(4核): 400秒
```

---

## 🔍 常见问题排查

### 问题1: 识别率低(<80%)

**症状**: "Total Sales"识别成"Tota1 Sa1es"，"1000"识别成"1OOO"

**解决方案**: 图像预处理
```python
import cv2
import numpy as np

def preprocess_image(image_path):
    """提高OCR准确率的预处理.

    步骤: 灰度化 → 去噪 → 二值化 → 锐化
    """
    img = cv2.imread(image_path)

    # 1. 灰度化
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # 2. 去噪（中值滤波）
    denoised = cv2.medianBlur(gray, 3)

    # 3. 二值化（Otsu自适应阈值）
    _, binary = cv2.threshold(
        denoised, 0, 255,
        cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )

    # 4. 锐化（可选）
    sharpen_kernel = np.array([
        [-1, -1, -1],
        [-1,  9, -1],
        [-1, -1, -1]
    ])
    sharpened = cv2.filter2D(binary, -1, sharpen_kernel)

    return sharpened

# 使用
preprocessed = preprocess_image("page1.png")
result = engine.recognize(preprocessed, dpi=300)
# 识别率: 75% → 90%
```

### 问题2: 识别速度慢(>30秒/页)

**排查清单**:
```bash
□ GPU是否启用? python -c "import paddle; print(paddle.is_compiled_with_cuda())"
□ DPI是否过高? 建议≤300
□ 图像是否过大? >5MB会影响速度
□ 批处理配置? rec_batch_num是否过小
```

**解决方案优先级**:
1. 启用GPU (提速5倍) ← 最优先
2. 降低DPI (300→250, 提速30%)
3. 裁剪空白区域 (提速10-30%)
4. 增大批处理 (GPU模式, 提速20%)

### 问题3: 内存占用高(>8GB)

**原因**: 图像未释放、中间结果累积

**解决方案**: 见"内存优化"章节（逐页处理+gc.collect）

---

## 📊 PaddleOCR参数调优

### 核心参数速查

```python
# 文本检测阈值（默认0.3）
engine._ocr_config['det_db_thresh'] = 0.3  # 标准
engine._ocr_config['det_db_thresh'] = 0.2  # 模糊文档（增加召回）
engine._ocr_config['det_db_thresh'] = 0.4  # 高精度（减少误检）

# 边界框过滤阈值（默认0.5）
engine._ocr_config['det_db_box_thresh'] = 0.5  # 标准
engine._ocr_config['det_db_box_thresh'] = 0.6  # 减少误检
engine._ocr_config['det_db_box_thresh'] = 0.4  # 增加召回

# 识别批次大小（默认6）
engine._ocr_config['rec_batch_num'] = 6   # CPU模式（推荐）
engine._ocr_config['rec_batch_num'] = 30  # GPU模式（提速20%）
engine._ocr_config['rec_batch_num'] = 3   # GPU显存不足
```

---

## 🎯 推荐工作流

```python
def recommended_ocr_workflow(pdf_path):
    """推荐的OCR识别流程（包含最佳实践）."""

    # 1. 初始化OCR引擎（GPU优先）
    engine = OCREngine(use_gpu=True)

    # 2. 加载坐标校准
    engine.load_calibration("calibration_data/ocr_calibration_300dpi.pkl")

    # 3. 设置DPI
    dpi = 300

    # 4. 检查缓存
    cache = OCRCache()
    cached_result = cache.get(pdf_path, dpi)
    if cached_result:
        return cached_result

    # 5. 执行识别
    result = engine.recognize(pdf_path, dpi=dpi)

    # 6. 保存缓存
    cache.set(pdf_path, dpi, result)

    # 7. 质量检查（可选）
    quality = validate_ocr_quality(result)
    if quality < 0.8:
        logger.warning(f"识别质量较低: {quality}, 建议人工核查")

    return result
```

### 质量检查清单
```markdown
□ DPI设置为300
□ 已加载坐标校准文件
□ GPU加速已启用（如有GPU）
□ 识别准确率>90%
□ 坐标偏差<10px
□ 处理速度<15秒/页（CPU）或<3秒/页（GPU）
□ 内存占用<4GB/100页
```

---

## 📞 获取帮助

### 问题排查顺序
1. **查看日志**: `logs/ocr.log`
2. **可视化调试**: `python scripts/quick_visualize.py <PDF>`
3. **参数实验**: `scripts/test_ocr_api.py`
4. **查看已知问题**: [known-issues.md](../context/known-issues.md)
5. **查看历史错误**: [error-patterns.md](../context/error-patterns.md)

### 相关文档
- **快速参考**: [QUICKREF.md](../QUICKREF.md)
- **性能优化**: [performance.md](performance.md)
- **已知问题**: [known-issues.md](../context/known-issues.md)

---

**END OF OCR-GUIDE.md (精简版)**

*配置版本: v4.0 | 优化日期: 2025-12-16 | 文件行数: 约400行（从750行压缩47%）*
