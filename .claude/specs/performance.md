# 性能优化指南

> **目标**: 提高系统处理速度和资源利用率
> **适用**: 所有开发阶段
> **最后更新**: 2025-12-16

---

## 🎯 性能优化原则

### 优化顺序
```
1. 算法优化 (影响最大)
2. 数据结构优化
3. I/O优化
4. 并行/并发优化
5. 缓存优化
6. 硬件优化 (影响最小)
```

### 优化前必做
```
□ 性能分析（找到瓶颈）
□ 设定目标（明确优化目标）
□ 建立基准（记录优化前性能）
□ 编写测试（确保优化后功能正确）
```

---

## 🚀 OCR优化策略

### 1. GPU加速

#### 启用GPU
```python
# 检查GPU是否可用
import paddle
print(f"GPU可用: {paddle.is_compiled_with_cuda()}")
print(f"GPU数量: {paddle.device.get_device_count()}")

# 初始化GPU模式
from backend.app.services.ocr_engine import OCREngine
engine = OCREngine(use_gpu=True)

# 性能对比
# CPU模式：15秒/页
# GPU模式：3秒/页（提速5倍）
```

#### GPU显存优化
```python
# 问题：GPU显存不足（OOM错误）
# 解决：减小批处理大小

engine = OCREngine(use_gpu=True)
engine._ocr_config['rec_batch_num'] = 3  # 默认6，减小到3

# 显存占用：从4GB降到2GB
# 速度影响：约降低10%
```

**适用场景**:
- 有NVIDIA GPU且显存≥4GB
- 批量处理大量PDF
- 需要实时响应

---

### 2. DPI优化

```python
# 根据文档质量选择合适的DPI

# 场景1：清晰文档（推荐）
result = engine.recognize(image, dpi=300)  # 标准配置
# 处理时间：15秒/页
# 准确率：96%

# 场景2：快速处理
result = engine.recognize(image, dpi=250)  # 降低DPI
# 处理时间：10秒/页（提速33%）
# 准确率：93%（下降3%）

# 场景3：高质量要求
result = engine.recognize(image, dpi=400)  # 提高DPI
# 处理时间：25秒/页（慢67%）
# 准确率：97%（提升1%）
```

**优化建议**:
- 清晰PDF使用250-300 DPI
- 模糊PDF使用400 DPI
- 不要盲目使用高DPI

---

### 3. 批量处理

#### 串行处理（慢）
```python
# ❌ 错误示例：逐个处理
results = []
for pdf_path in pdf_list:
    result = engine.recognize(pdf_path, dpi=300)
    results.append(result)
# 总时间：15秒 × 100 = 1500秒（25分钟）
```

#### 批量处理（快）
```python
# ✅ 正确示例：批量处理
results = engine.recognize_batch(pdf_list, dpi=300, batch_size=10)
# 总时间：约900秒（15分钟，节省40%时间）
```

**性能提升**:
- 减少模型加载次数
- 优化GPU利用率
- 减少I/O等待时间

---

### 4. 缓存机制

```python
import hashlib
import pickle
from pathlib import Path

class OCRCache:
    """OCR结果缓存（避免重复识别）."""

    def __init__(self, cache_dir="cache/ocr"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def get_cache_key(self, image_path, dpi):
        """生成缓存键（使用文件内容MD5）."""
        with open(image_path, "rb") as f:
            file_hash = hashlib.md5(f.read()).hexdigest()
        return f"{file_hash}_dpi{dpi}.pkl"

    def get(self, image_path, dpi):
        """获取缓存."""
        cache_file = self.cache_dir / self.get_cache_key(image_path, dpi)
        if cache_file.exists():
            with open(cache_file, "rb") as f:
                return pickle.load(f)
        return None

    def set(self, image_path, dpi, result):
        """保存缓存."""
        cache_file = self.cache_dir / self.get_cache_key(image_path, dpi)
        with open(cache_file, "wb") as f:
            pickle.dump(result, f)

# 使用示例
cache = OCRCache()

def recognize_with_cache(image_path, dpi=300):
    """带缓存的OCR识别."""
    # 先查缓存
    cached = cache.get(image_path, dpi)
    if cached:
        return cached  # 0.01秒（命中缓存）

    # 执行识别
    result = engine.recognize(image_path, dpi=dpi)  # 15秒

    # 保存缓存
    cache.set(image_path, dpi, result)
    return result

# 性能提升：首次15秒，第二次0.01秒（提速1500倍）
```

---

### 5. 并行处理

```python
from concurrent.futures import ProcessPoolExecutor
import multiprocessing

def parallel_ocr(pdf_list, dpi=300, workers=None):
    """并行OCR识别.

    Args:
        pdf_list: PDF文件路径列表
        dpi: 识别DPI
        workers: 并行worker数量
            None: 自动检测（CPU核心数）
            推荐: CPU核心数 - 1（留一个核心给系统）

    Returns:
        OCR结果列表
    """
    if workers is None:
        workers = max(1, multiprocessing.cpu_count() - 1)

    def process_one(pdf_path):
        # 每个worker独立创建OCR引擎
        from backend.app.services.ocr_engine import OCREngine
        engine = OCREngine(use_gpu=False)
        return engine.recognize(pdf_path, dpi=dpi)

    # 使用进程池（绕过GIL）
    with ProcessPoolExecutor(max_workers=workers) as executor:
        results = list(executor.map(process_one, pdf_list))

    return results

# 性能对比（100个PDF，4核CPU）
# 串行处理：15秒 × 100 = 1500秒（25分钟）
# 并行处理：约400秒（6.7分钟，提速3.75倍）
```

**注意事项**:
- GPU模式不适合并行（GPU已并行）
- CPU模式使用进程池（避免GIL）
- workers数量 = CPU核心数 - 1

---

## 📊 图像处理优化

### 1. 内存管理

```python
import gc
import cv2

def process_image_memory_efficient(image_path):
    """内存友好的图像处理."""

    # 1. 读取图像
    img = cv2.imread(image_path)

    # 2. 处理图像
    processed = preprocess(img)

    # 3. 及时释放原图内存
    del img
    gc.collect()  # 强制垃圾回收

    # 4. 继续处理
    result = ocr.recognize(processed)

    # 5. 释放处理后的图像
    del processed
    gc.collect()

    return result

# 内存占用：从8GB降到2GB（节省75%）
```

---

### 2. 向量化操作

```python
import numpy as np

# ❌ 错误：循环操作
result = np.zeros_like(array)
for i in range(len(array)):
    result[i] = array[i] * 2 + 10
# 耗时：1000ms

# ✅ 正确：向量化操作
result = array * 2 + 10
# 耗时：10ms（快100倍）
```

**常见向量化场景**:
- 数组运算（加减乘除）
- 条件筛选（where）
- 聚合操作（sum, mean, max）

---

### 3. 避免不必要的拷贝

```python
import numpy as np

# ❌ 错误：多次拷贝
img1 = image.copy()  # 拷贝1
img2 = img1.copy()   # 拷贝2
img3 = img2.copy()   # 拷贝3
# 内存：原图×4

# ✅ 正确：直接操作或最少拷贝
img = image  # 引用，不拷贝
process_inplace(img)  # 原地修改
# 内存：原图×1
```

---

## 💾 数据库优化

### 1. 批量插入

```python
from backend.app.models import SalesDetail

# ❌ 错误：逐条插入
for item in items:
    detail = SalesDetail(**item)
    db.session.add(detail)
    db.session.commit()  # 每次commit都要写磁盘
# 耗时：100条 × 50ms = 5秒

# ✅ 正确：批量提交
details = [SalesDetail(**item) for item in items]
db.session.add_all(details)
db.session.commit()  # 一次性提交
# 耗时：200ms（快25倍）
```

---

### 2. 索引优化

```sql
-- 场景1：频繁按日期查询
CREATE INDEX idx_statements_date ON statements(statement_date);

-- 场景2：按用户+日期查询
CREATE INDEX idx_statements_user_date ON statements(user_id, statement_date);

-- 场景3：全文搜索
CREATE INDEX idx_sales_product_name_fulltext ON sales_details
USING GIN (to_tsvector('english', product_name));
```

**索引原则**:
- WHERE条件字段 → 建立索引
- JOIN连接字段 → 建立索引
- ORDER BY字段 → 考虑索引
- 索引不是越多越好（影响写入性能）

---

### 3. 查询优化

```python
# ❌ 错误：N+1查询
statements = Statement.query.all()
for stmt in statements:
    sales = stmt.sales_details  # 每次查询一次数据库
# 查询次数：1 + N

# ✅ 正确：预加载（eager loading）
from sqlalchemy.orm import joinedload

statements = Statement.query.options(
    joinedload(Statement.sales_details)
).all()
# 查询次数：1（使用JOIN）
```

---

## ⚡ Python代码优化

### 1. 使用生成器

```python
# ❌ 错误：返回列表（内存占用大）
def read_large_file(filepath):
    lines = []
    with open(filepath) as f:
        for line in f:
            lines.append(line.strip())
    return lines
# 内存：一次性加载所有行

# ✅ 正确：使用生成器（惰性加载）
def read_large_file(filepath):
    with open(filepath) as f:
        for line in f:
            yield line.strip()
# 内存：每次只加载一行
```

---

### 2. 选择合适的数据结构

```python
# 场景1：频繁查找 → 使用set或dict
items = ['a', 'b', 'c', ...]  # 列表
if 'x' in items:  # O(n)

items = {'a', 'b', 'c', ...}  # 集合
if 'x' in items:  # O(1)，快n倍

# 场景2：频繁插入删除 → 使用deque
from collections import deque
queue = deque()
queue.append(item)  # O(1)
queue.popleft()     # O(1)
```

---

### 3. 避免重复计算

```python
# ❌ 错误：重复计算
for i in range(len(array)):
    if array[i] > calculate_threshold():  # 每次都计算
        process(array[i])

# ✅ 正确：缓存结果
threshold = calculate_threshold()  # 计算一次
for i in range(len(array)):
    if array[i] > threshold:
        process(array[i])
```

---

## 📊 性能分析工具

### 1. cProfile（Python性能分析）

```bash
# 分析脚本性能
python -m cProfile -o profile.stats script.py

# 查看结果
python -m pstats profile.stats
> sort cumulative
> stats 10
```

```python
# 代码中使用
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()

# 执行代码
your_function()

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(20)  # 打印前20个最耗时的函数
```

---

### 2. memory_profiler（内存分析）

```bash
# 安装
pip install memory_profiler

# 分析脚本
python -m memory_profiler script.py
```

```python
# 装饰器使用
from memory_profiler import profile

@profile
def my_function():
    # 函数代码
    pass
```

---

### 3. line_profiler（逐行分析）

```bash
# 安装
pip install line_profiler

# 使用
kernprof -l -v script.py
```

```python
# 装饰器使用
@profile
def my_function():
    # 函数代码
    pass
```

---

## 🎯 性能优化检查清单

### 优化前
```
□ 已进行性能分析（找到瓶颈）
□ 已设定优化目标（明确目标）
□ 已记录当前性能（建立基准）
□ 已编写性能测试（验证效果）
```

### 优化中
```
□ 优先优化最慢的部分（80/20原则）
□ 每次只优化一个地方（避免混淆）
□ 及时测量优化效果（数据驱动）
□ 保持代码可读性（不过度优化）
```

### 优化后
```
□ 运行性能测试（验证提速）
□ 运行功能测试（确保正确）
□ 记录优化结果（文档化）
□ 提交代码（包含性能数据）
```

---

## 📈 性能优化案例

### 案例1: OCR批量处理优化

**优化前**:
```python
# 串行处理100个PDF
for pdf in pdf_list:
    result = ocr.recognize(pdf, dpi=300)
# 耗时：1500秒（25分钟）
```

**优化后**:
```python
# 缓存 + 并行 + 降低DPI
results = parallel_ocr(
    pdf_list,
    dpi=250,  # 降低DPI（300→250）
    workers=4  # 4核并行
)
# 耗时：300秒（5分钟）
# 提速：5倍
```

---

### 案例2: 数据库批量插入优化

**优化前**:
```python
# 逐条插入1000条销售明细
for item in items:
    db.session.add(SalesDetail(**item))
    db.session.commit()
# 耗时：50秒
```

**优化后**:
```python
# 批量插入
db.session.bulk_insert_mappings(SalesDetail, items)
db.session.commit()
# 耗时：0.5秒
# 提速：100倍
```

---

## 🚫 过度优化警告

### 不要优化这些
1. **不是瓶颈的代码** - 优化快代码没意义
2. **牺牲可读性** - 代码可读性 > 微小的性能提升
3. **过早优化** - 先实现功能，再优化性能
4. **猜测优化** - 必须先分析，再优化

### Knuth名言
> "过早优化是万恶之源" - Donald Knuth

**正确的优化顺序**:
```
1. 让代码正确运行
2. 让代码清晰易读
3. 性能分析找瓶颈
4. 优化瓶颈
5. 验证效果
```

---

**END OF PERFORMANCE.MD**

*配置版本: v1.0 | 创建时间: 2025-12-16 | 文件行数: 约550行*
