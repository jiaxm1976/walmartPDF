# OCR坐标校准函数工作原理

## 问题背景

OCR识别返回的Y坐标与PDF实际位置可能存在偏差，导致：
- 关键词定位不准确
- 板块切分位置偏移
- 数据提取错误

## 解决方案：Y坐标校准

### 1. 校准文件

**位置**: `calibration_data/ocr_calibration_300dpi.pkl`

**内容** (pickle格式):
```python
{
    'calibration_func': <scipy.interpolate.interp1d对象>,  # 插值函数
    'reference_points': [(1, 10), (1, 62), ...],          # 86个参考点
    'width': 2174,                                         # 校准图片宽度
    'height': 3508,                                        # 校准图片高度
    'interval': 50,                                        # 参考点间隔
    'dpi': 300                                            # 分辨率
}
```

### 2. 工作原理

#### 步骤1: 生成校准数据（已完成）
```python
# 使用scripts/create_calibration.py生成
# 1. 创建标准校准图片（每50px画一条水平线）
# 2. OCR识别所有水平线位置
# 3. 对比实际位置和OCR位置，记录偏差
# 4. 使用scipy.interpolate.interp1d创建插值函数
# 5. 保存为pkl文件
```

#### 步骤2: 加载校准函数（运行时）
```python
# 在OCREngine.__init__()中自动加载
def _load_default_calibration(self):
    calibration_file = Path('calibration_data/ocr_calibration_300dpi.pkl')

    with open(calibration_file, 'rb') as f:
        calibration_data = pickle.load(f)
        # 兼容两种键名
        self.calibration_func = calibration_data.get('calibration_func') or \
                               calibration_data.get('calibration_function')
```

#### 步骤3: Y坐标校准（每次识别）
```python
def calibrate_y_coordinate(self, y_raw: int) -> int:
    """对OCR识别的Y坐标进行校准"""
    if self.calibration_func is None:
        return y_raw  # 无校准函数，返回原始值

    try:
        # 使用插值函数校准
        y_calibrated = int(self.calibration_func(y_raw))
        return y_calibrated
    except:
        return y_raw  # 校准失败，返回原始值
```

### 3. 插值函数原理

使用**scipy.interpolate.interp1d**进行线性插值：

```
已知参考点:
  实际Y=0    → OCR识别Y=10   (偏差+10)
  实际Y=50   → OCR识别Y=62   (偏差+12)
  实际Y=100  → OCR识别Y=111  (偏差+11)
  ...

查询: OCR识别Y=1000
插值计算: 实际Y ≈ 1061
偏差: +61
```

**数学模型**:
- 输入: OCR原始Y坐标
- 输出: 校准后的实际Y坐标
- 方法: 分段线性插值
- 参考点数量: 86个（每50px一个点）

### 4. 校准效果

**测试案例**:
```python
ocr = OCREngine()

# 原始Y坐标 → 校准后Y坐标
ocr.calibrate_y_coordinate(0)    → 10
ocr.calibrate_y_coordinate(500)  → 531
ocr.calibrate_y_coordinate(1000) → 1061
ocr.calibrate_y_coordinate(2000) → 2122
ocr.calibrate_y_coordinate(3000) → 3183
```

**平均偏差**: 约+60px (Vision OCR系统性偏移)

## 问题诊断：为什么之前没找到？

### 根本原因
校准文件中的键是`calibration_func`，但代码查找的是`calibration_function`（键名不匹配）

### 修复前
```python
# ocr_engine.py line 76
self.calibration_func = calibration_data.get('calibration_function')
# 返回None，因为键不存在

# 日志输出
logger.warning("校准文件中未找到calibration_function")
```

### 修复后
```python
# ocr_engine.py line 78-79
# 兼容两种键名
self.calibration_func = calibration_data.get('calibration_func') or \
                       calibration_data.get('calibration_function')

# 日志输出
logger.info("已加载坐标校准函数: calibration_data/ocr_calibration_300dpi.pkl")
```

### 影响分析
- ❌ 修复前: 所有Y坐标未校准，使用原始值（可能偏差60+px）
- ✅ 修复后: Y坐标自动校准，偏差修正

## 校准数据生成方法

如果需要重新生成校准数据：

```bash
cd scripts
python create_calibration.py

# 生成文件:
# - calibration_data/calibration_standard.png    (标准图片)
# - calibration_data/calibration_with_marks.png  (标记版本)
# - calibration_data/ocr_calibration_300dpi.pkl  (校准函数)
```

### 校准图片格式
- 尺寸: 2174×3508 (300 DPI的A4纸)
- 内容: 每50px画一条黑色水平线
- 标记: 每条线左侧标注实际Y坐标
- 用途: OCR识别线条位置，计算偏差

## 使用建议

### 何时需要重新校准
1. 更换OCR引擎（如从PaddleOCR切换到Vision）
2. 更改PDF转图片的DPI（如从300改为600）
3. OCR识别偏差明显增大
4. 更换操作系统或硬件平台

### 校准文件管理
- 每个DPI应有独立的校准文件
- 命名格式: `ocr_calibration_{dpi}dpi.pkl`
- 版本控制: 建议纳入git管理
- 备份: 校准生成耗时，应定期备份

### 性能考虑
- 校准函数加载: 启动时一次性加载，耗时<10ms
- Y坐标校准: 每次调用耗时<0.1ms
- 总体影响: 可忽略不计

## 常见问题

### Q1: 为什么只校准Y坐标，不校准X坐标？
A: X坐标偏差通常很小（<5px），且不影响板块切分（只按Y坐标切分）

### Q2: 校准函数是否适用于所有PDF？
A: 是的。校准函数基于OCR引擎的系统性偏移，与PDF内容无关

### Q3: 校准后还有偏差怎么办？
A:
1. 检查DPI是否匹配（PDF转图片DPI=300）
2. 检查校准文件是否正确加载
3. 考虑重新生成校准数据
4. 增加OFFSET偏移量（目前80px）

### Q4: 切换OCR引擎后需要重新校准吗？
A: 是的。不同OCR引擎的偏差特征不同，必须重新生成校准数据

## 技术栈

- **scipy.interpolate.interp1d**: 一维插值函数
- **pickle**: Python对象序列化
- **Vision框架**: macOS原生OCR（当前使用）
- **numpy**: 数值计算

## 相关文件

- `backend/app/services/ocr_engine.py` - OCR引擎（校准逻辑）
- `scripts/create_calibration.py` - 校准数据生成脚本
- `calibration_data/ocr_calibration_300dpi.pkl` - 校准数据文件
- `calibration_data/calibration_standard.png` - 标准校准图片

---
**创建时间**: 2025-12-18
**最后更新**: 2025-12-18 21:15
**状态**: ✅ 已修复键名不匹配问题
