
# Walmart-a 项目打包信息

打包时间: 2025-12-15 00:09:25
Python版本要求: 3.9+

## 包含的内容

### 核心代码
- backend/               - 后端代码（OCR引擎、图像处理等）
- scripts/               - 脚本工具
- .claude/CLAUDE.md      - 项目配置文件

### 数据文件
- calibration_data/      - OCR校准函数和校准图片
- PdfData/               - 测试PDF样本

### 配置文件
- requirements.txt       - Python依赖列表

## 在新电脑上安装

### 1. 解压文件
```bash
# Windows:
右键 → 解压到当前文件夹

# Linux/Mac:
tar -xzf walmart-a-package.tar.gz
cd walmart-a
```

### 2. 安装Python依赖
```bash
# 创建虚拟环境（推荐，使用 .venv）
python -m venv .venv

# Windows激活:
.venv\Scripts\activate

# Linux/Mac激活:
source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt
pip install scipy
```

注意：仓库脚本已兼容 legacy `venv`（回退），但建议统一使用 `.venv`。如需清理遗留的 `venv`，可运行 `scripts/remove_legacy_venv.sh`。

重要：虚拟环境为本项目标配
- **原因**: 隔离依赖、避免系统包冲突、便于本地/CI 环境一致性。
- **推荐做法**: 在项目根创建并激活 `.venv`，随后使用该环境安装依赖并运行脚本与测试。
- **快速命令**:
```
python -m venv .venv
source .venv/bin/activate  # macOS / Linux
pip install -r backend/requirements.txt
```
将虚拟环境加入项目开发规范有助于减少环境相关的测试失败（例如缺少本地 OCR 绑定或模块导入错误）。

### 3. 初始化数据库（标准方式）
```bash
python scripts/init_database_v2.py
```
**重要：** 自 2026-01-06 起，必须使用此方式初始化数据库。
功能包括：
- 自动备份现有数据库
- 清空旧数据库
- 执行 SQL schema 初始化
- 初始化右侧数据字段频率
- 验证表结构完整性

### 4. 测试环境
```bash
# 运行测试脚本
python scripts/visualize_with_calibration.py PdfData/MP_01142025_statement_summary.pdf
```

### 5. 验证OCR引擎
首次运行会自动下载PaddleOCR模型（约1-2GB），请耐心等待。

## 项目状态说明

### 当前进度
1. ✅ 已完成PDF转图片（300 DPI）
2. ✅ 已完成OCR关键词识别
3. ✅ 已完成校准函数生成
4. ⚠️ 校准效果需要进一步优化

### 待解决问题
1. 关键词坐标越往下偏差越大
2. OCR误识别问题
3. 校准函数效果不理想

### 下一步工作
1. 调试校准函数
2. 优化关键词识别准确率
3. 实现实际的图片分割功能

## 联系方式
项目文档: .claude/CLAUDE.md
