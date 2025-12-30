# Walmart PDF解析系统 - Claude开发助手配置

> **版本**: v4.1 | **更新**: 2025-12-16 | **架构**: 分层配置体系

---

## 🎯 项目概览

### 一句话描述
**自动化处理沃尔玛市场（Walmart Marketplace）财务对账单的PDF报表识别和数据分析系统**

### 核心能力
- PDF自动解析（pdfplumber）
- OCR文字识别（PaddleOCR）
- 智能图像分割（OpenCV）
- 数据结构化提取（正则+规则引擎）
- 数据库存储 （SQLite） 
- 数据库文件 `/Users/jiaxinming/JxmWork/walmart-a/backend/data/walmart_pdf_parser.db`
- 后续：Web API + 前端

### 环境管理
```bash
# 激活虚拟环境
source venv/bin/activate

# 安装依赖 (使用阿里云镜像)
pip install -i https://mirrors.aliyun.com/pypi/simple/ -r backend/requirements.txt
```
---

### 当前进度
- 项目总体开发方案，在项目开始阶段设计出来，并存放在 '.claude/TaskList.md'文件中，需要调整有用户发起调整。
- 过程中的任务清单存放在 './todo.md'文件中


---
### 我的习惯 
 - 你是专业的全站工程师助手，专业，非常专业
 - 定期重置上下文，超过2000行，使用/compact 命令
 - 不要随便输出md文档，只需要将重要信息保存在项目文档中’walmart-a/.claude/context/‘目录下，项目文档分级构建，主文件main.md,主文件只有菜单链接，通过跳转到各模块文档,文档用中文命名，方便Claude随时参考。需要生成前和我确认，我确认才开始生成，不确认之前不生成。
 - 项目开始前，需要创建一个todo.md 命令文件，运行/todo命令来管理任务列表,任务类标树状保存
 - 每次执行/exit 先更新todo.md 
 - 注释策略 适度注释
 - 写代码后 写测试代码，测试代码执行后日志写到测试覆盖率>80%，需要测试问题从backend/tests/testlog+序号.log中读取分析
 - 测试代码策略 测试代码可以离开环境执行，日志输出到backend/tests/testlog+序号.log文件中，每次测试
 - 牢记不要过度工程化，牢记
 - 所有解决方案必须以“编号分步执行列表”的形式输出，每一步包含：
   - 操作目的（简要说明这一步要做什么）
   - 禁止无结构的文本描述，禁止省略关键执行步骤。

## ⚡ 快速命令
- 帮我理解
```
□ 分层解释 （解释清楚了吗?）
□ 有示例吗? (代码示例)
□ 有验证吗? (运行验证)
□ 建议吗?
```



## 🔴 代码注释铁律（强制执行）

### 1. 文件头注释（必需）
```python
# ============================================================
# 文件: backend/app/services/example_service.py
# 功能: [一句话描述核心功能]
# 作者: [姓名或团队]
# 创建时间: 2025-12-15
# 最后修改: 2025-12-15
# 依赖: [列出核心依赖库]
# 说明: [可选：额外的重要说明]
# ============================================================

**函数代码**:
-适度注释，核心语句

‘’‘


## Claude任务完成反馈格式规范
**良好反馈的标准**：
- ✅ 用户10秒内理解核心结果
- ✅ 用户清楚知道下一步做什么
- ✅ 没有冗余或重复信息
- ✅ 关键数字清晰可见
- ✅ 格式清爽易读

### **场景：需要用户决策时**

## 🤔 需要您决策

**当前状况**：[一句话说明]

**方案对比**：
| 方案 | 优点 | 缺点 | 工作量 |
|-----|------|------|--------|
| A   | XXX  | XXX  | 2小时  |
| B   | XXX  | XXX  | 4小时  |

**建议**：方案A（原因：XXX）

**请回复**：选择A还是B？
```
**解决方案**：
1. [方案1 - 推荐]：预计XX时间
2. [方案2]：预计XX时间


### 测试文件组织
```
backend/tests/
├── unit/                    # 单元测试
│   ├── test_ocr_engine.py
│   ├── test_pdf_parser.py
│   └── test_image_splitter.py
├── integration/             # 集成测试
│   └── test_full_pipeline.py
├── test_data/               # 测试数据
│   └── sample_pdfs/
├── fixtures/                # 测试fixtures
│    └── __init__.py
└── output/                # 测试输出目录
    


## 🏗️ 项目结构速览

```
walmart-a/                  (1.6GB total)
├── .claude/                # Claude配置（当前目录）
│   ├── CLAUDE.md          # 本文件（主配置）
│   ├── QUICKREF.md        # 快速参考卡 ⚡ NEW
│   ├── CORE.md            # 核心开发规范
│   ├── AI-ASSIST.md       # AI辅助配置
│   ├── specs/             # 专项深度指南
│   │   └── ocr-guide.md
│   ├── context/           # 动态上下文
│   │   ├── current-sprint.md
│   │   ├── known-issues.md
│   │   ├── error-patterns.md  ⚡ NEW
│   │   └── recent-changes.md
│   └── settings.local.json
│
├── backend/                # 后端核心代码 (4.1MB)
│   ├── app/
│   │   ├── services/      # 业务逻辑层
│   │   │   ├── ocr_engine.py           # OCR引擎封装
│   │   │   ├── pdf_parser.py           # PDF解析器
│   │   │   ├── image_splitter.py       # 图像分割器
│   │   │   ├── section_splitter.py     # 区块分割
│   │   │   └── pdf_section_splitter.py # PDF区块处理
│   │   ├── utils/         # 工具函数
│   │   ├── models/        # 数据模型（待实现）
│   │   └── schemas/       # Pydantic schemas（待实现）
│   ├── tests/             # 测试目录
│   │   ├── unit/          # 单元测试（待完善）
│   │   ├── fixtures/      # 测试fixtures
│   │   └── test_data/     # 测试数据
│   │       └── sample_pdfs/  # 6个测试PDF
│   └── requirements.txt
│
├── scripts/                # 开发脚本 (24KB)
│   ├── create_calibration.py    # 坐标校准生成
│   ├── quick_visualize.py       # OCR可视化工具
│   └── test/               # 测试目录规范
│       ├── test-code/     # 所有测试代码
│       ├── test-output/   # 所有测试输出
│       └── test-md/       # 所有测试文档
│
├── calibration_data/       # OCR坐标校准数据 (332KB)
│   └── ocr_calibration_300dpi.pkl
│
├── PdfData/                # 测试PDF样本 (3.5MB)
├── venv/                   # Python 3.11.9虚拟环境 (1.5GB)
└── README_安装说明.txt
```


**END OF CLAUDE.md**

*配置版本: v4.1 | 最后更新: 2025-12-16 | 文件行数: 约235行*

测试和运行在环境source .venv/bin/activate   

