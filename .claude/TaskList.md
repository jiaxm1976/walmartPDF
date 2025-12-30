# Walmart PDF解析系统 - 项目任务清单

> **版本**: v1.0 | **创建时间**: 2025-12-19 | **维护者**: 项目团队

---

## 一、项目情况说明

### 1.1 项目概述
**自动化处理沃尔玛市场（Walmart Marketplace）财务对账单的PDF报表识别和数据分析系统**

### 1.2 核心能力
- PDF自动解析（pdfplumber + PyMuPDF）
- OCR文字识别（Apple Vision Framework）
- 智能图像分割（OpenCV横线检测）
- 数据结构化提取（7个财务板块）
- RESTful API服务（FastAPI）
- 数据库存储（SQLite/MySQL/PostgreSQL）
- 数据查询和修改（Web API）
- 数据导出（Excel/CSV/JSON）

### 1.3 环境信息
- **开发语言**: Python 3.11.9
- **数据库**: SQLite（开发）/ MySQL（生产）
- **虚拟环境**: venv
- **项目路径**: `/Users/jiaxinming/JxmWork/walmart-a/`
- **数据库文件**: `walmart_pdf_parser.db`
- **依赖管理**: pip + requirements.txt

---

## 二、技术架构

### 2.1 技术栈

#### 后端框架
- **FastAPI** 0.104.1 - 异步Web框架
- **Uvicorn** 0.24.0 - ASGI服务器
- **SQLAlchemy** 2.0.23 - ORM框架
- **Pydantic** 2.5.2 - 数据验证

#### PDF处理
- **pdfplumber** 0.10.3 - PDF文本提取
- **PyMuPDF** (fitz) - PDF转图片
- **Pillow** - 图像处理

#### OCR识别
- **Apple Vision Framework** - 主OCR引擎（macOS）
- **PaddleOCR** - 备用OCR引擎
- **OpenCV** - 图像预处理和分割

#### 数据存储
- **SQLite** - 开发环境数据库
- **MySQL/PostgreSQL** - 生产环境支持
- **PyMySQL** - MySQL驱动

### 2.2 系统架构图

```
┌─────────────────────────────────────────────────────────┐
│                   Client（客户端）                       │
│              cURL / Postman / Web前端                    │
└────────────────────────┬────────────────────────────────┘
                         │ HTTP/HTTPS
                         ▼
┌─────────────────────────────────────────────────────────┐
│              API Layer（API接口层）                      │
│  ┌─────────────────┬──────────────────────────────────┐ │
│  │  /pdfs/*        │  /statements/*                   │ │
│  │  PDF文件管理    │  对账单数据管理                  │ │
│  │  - 上传         │  - 查询完整数据                  │ │
│  │  - 查询         │  - 更新板块数据                  │ │
│  │  - 删除         │  - 数据验证                      │ │
│  │  - 触发解析     │  - 数据导出                      │ │
│  └─────────────────┴──────────────────────────────────┘ │
│                    FastAPI Router                        │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│            Service Layer（业务逻辑层）                   │
│  ┌──────────────────┬──────────────────────────────────┐│
│  │ pdf_parser_      │ keyword_extractor.py             ││
│  │ service.py       │ 关键词提取服务                    ││
│  │ PDF解析服务      │ - 7个板块关键词识别               ││
│  │ - 调用PDF解析器  │ - 板块范围计算                    ││
│  │ - 调用OCR引擎    │ - Footer过滤                      ││
│  │ - 数据结构化     │                                   ││
│  └──────────────────┴──────────────────────────────────┘│
│  ┌──────────────────┬──────────────────────────────────┐│
│  │ ocr_engine.py    │ pdf_parser.py                    ││
│  │ OCR识别引擎      │ PDF解析器                         ││
│  │ - Vision OCR集成 │ - PDF转图片                       ││
│  │ - 坐标校准       │ - pdfplumber提取                  ││
│  │ - 置信度过滤     │ - 图像分割                        ││
│  └──────────────────┴──────────────────────────────────┘│
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│             CRUD Layer（数据访问层）                     │
│  ┌─────────────────────────────────────────────────────┐│
│  │ pdf_file.py (584行)                                 ││
│  │ - create_pdf_file()         创建PDF记录             ││
│  │ - get_pdf_files()           分页查询PDF列表         ││
│  │ - update_pdf_file_status()  更新处理状态            ││
│  │ - create_statement_header() 创建对账单头部          ││
│  │ - get_complete_statement_data() 获取完整数据        ││
│  │ - update_complete_statement_data() 更新完整数据     ││
│  └─────────────────────────────────────────────────────┘│
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│              ORM Layer（对象关系映射层）                 │
│  ┌─────────────────────────────────────────────────────┐│
│  │ models.py (10个表)                                  ││
│  │ - PDFFile                   PDF文件表               ││
│  │ - StatementHeader           对账单头部              ││
│  │ - SalesDetail               销售明细                ││
│  │ - RefundDetail              退款明细                ││
│  │ - AdjustmentDetail          调整明细                ││
│  │ - WFSDetail                 WFS服务明细             ││
│  │ - OtherActivityDetail       其他活动明细            ││
│  │ - StatementFooter           对账单尾部              ││
│  │ - PaymentDetail             付款详情                ││
│  │ - DynamicField              动态字段扩展            ││
│  └─────────────────────────────────────────────────────┘│
│                    SQLAlchemy ORM                        │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│          Database（数据库层）                            │
│  ┌─────────────────────────────────────────────────────┐│
│  │ SQLite (开发)                                       ││
│  │ MySQL/PostgreSQL (生产)                             ││
│  │                                                     ││
│  │ walmart_pdf_parser.db                               ││
│  └─────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────┘
```

### 2.3 目录结构

```
walmart-a/                              # 项目根目录
│
├── .claude/                            # Claude配置目录
│   ├── CLAUDE.md                       # 主配置文件
│   ├── CORE.md                         # 开发规范
│   ├── TaskList.md                     # 本文件（项目任务清单）
│   ├── specs/                          # 技术规范文档
│   │   ├── ocr-guide.md               # OCR技术指南
│   │   ├── db-design.md               # 数据库设计文档
│   │   └── performance.md             # 性能优化指南
│   └── context/                        # 工作上下文记录
│       ├── current-sprint.md          # 当前冲刺计划
│       ├── known-issues.md            # 已知问题列表
│       └── phase*-*.md                # 各Phase工作记录
│
├── backend/                            # 后端代码目录
│   ├── main.py                         # FastAPI主应用入口
│   │
│   ├── database/                       # 数据库配置和模型
│   │   ├── config.py                   # 数据库连接配置
│   │   ├── models.py                   # SQLAlchemy ORM模型（10个表）
│   │   └── schema.sql                  # SQL建表语句
│   │
│   ├── app/                            # 应用核心代码
│   │   ├── config.py                   # 应用配置
│   │   │
│   │   ├── services/                   # 业务逻辑层
│   │   │   ├── ocr_engine.py           # OCR识别引擎（555行）
│   │   │   ├── pdf_parser.py           # PDF解析器（861行）
│   │   │   ├── pdf_parser_service.py   # PDF解析服务（420行）
│   │   │   ├── image_splitter.py       # 图像分割器
│   │   │   ├── keyword_extractor.py    # 关键词提取（65行）
│   │   │   ├── direct_keyword_extractor.py  # 直接关键词提取
│   │   │   ├── section_splitter.py     # 区块分割器
│   │   │   └── pdf_section_splitter.py # PDF区块处理
│   │   │
│   │   ├── schemas/                    # Pydantic数据模型
│   │   │   └── pdf_file.py             # API数据模型（270行）
│   │   │
│   │   ├── crud/                       # 数据库CRUD操作
│   │   │   └── pdf_file.py             # PDF和对账单CRUD（584行）
│   │   │
│   │   └── api/v1/                     # API接口（版本1）
│   │       ├── __init__.py             # 路由注册
│   │       ├── pdfs.py                 # PDF管理接口（460行）
│   │       └── statements.py           # 对账单数据接口（270行）
│   │
│   ├── tests/                          # 测试代码目录
│   │   ├── unit/                       # 单元测试
│   │   ├── integration/                # 集成测试
│   │   ├── fixtures/                   # 测试fixtures
│   │   └── test_data/                  # 测试数据
│   │       └── sample_pdfs/            # 测试PDF文件
│   │
│   └── requirements.txt                # Python依赖清单
│
├── scripts/                            # 工具脚本目录
│   ├── init_database.py                # 数据库初始化脚本
│   ├── verify_database.py              # 数据库验证脚本
│   ├── test_parse_pipeline.py          # 完整流程测试脚本
│   ├── batch_test_direct_extraction.py # 批量测试脚本
│   ├── create_calibration.py           # OCR坐标校准生成
│   ├── quick_visualize.py              # OCR可视化工具
│   └── test/                           # 测试相关
│       ├── test-code/                  # 测试代码
│       ├── test-output/                # 测试输出
│       └── test-md/                    # 测试文档
│
├── calibration_data/                   # OCR校准数据目录
│   └── ocr_calibration_300dpi.pkl      # 300DPI坐标校准文件
│
├── PdfData/                            # 测试PDF样本目录（6个文件）
├── uploads/                            # 上传文件存储目录
├── output/                             # 输出文件目录
├── venv/                               # Python虚拟环境
│
├── walmart_pdf_parser.db               # SQLite数据库文件
├── API_README.md                       # API完整使用文档（710行）
├── API_QUICKSTART.md                   # API快速开始指南（173行）
├── todo.md                             # 日常任务清单（进度跟踪）
└── README_安装说明.txt                 # 环境安装说明
```

### 2.4 数据库设计

**10个核心表结构**:

| 表名 | 说明 | 主要字段 |
|------|------|----------|
| `pdf_files` | PDF文件主表 | id, filename, file_path, file_size, file_hash, upload_time, status |
| `statement_headers` | 对账单头部信息 | pdf_id, statement_period_start, statement_period_end, marketplace |
| `sales_details` | 销售明细 | pdf_id, total_sales, units_sold, shipping_charges, gift_wrap_charges |
| `refund_details` | 退款明细 | pdf_id, total_refund, refund_amount, units_refunded |
| `adjustment_details` | 调整明细 | pdf_id, adjustment_amount, adjustment_description |
| `wfs_details` | WFS服务明细 | pdf_id, fulfillment_fee, storage_fee, removal_fee |
| `other_activity_details` | 其他活动明细 | pdf_id, other_amount, other_description |
| `statement_footers` | 对账单尾部 | pdf_id, total_paid, ending_balance |
| `payment_details` | 付款详情 | pdf_id, payment_date, payment_amount, payment_method |
| `dynamic_fields` | 动态字段扩展表 | pdf_id, section, field_name, field_value, field_type |

**关系设计**:
- 所有表通过 `pdf_id` 外键关联到 `pdf_files` 表
- 级联删除：删除PDF文件时，自动删除所有关联数据
- 自动时间戳：created_at 和 updated_at 字段自动维护

---

## 三、实现任务清单

### Phase 1: 基础架构

#### 1. 开发环境搭建（P0）
验收标准：虚拟环境可正常激活，所有依赖可成功安装和导入
- 1.1 Python虚拟环境创建 - 使用Python 3.11.9创建venv虚拟环境
- 1.2 核心依赖安装 - 安装pdfplumber、PyMuPDF、OpenCV、PaddleOCR等
- 1.3 Web框架依赖安装 - 安装FastAPI、Uvicorn、SQLAlchemy、Pydantic等
- 1.4 依赖版本管理 - 生成requirements.txt，固定依赖版本

#### 2. 项目结构设计（P0）
验收标准：目录结构清晰，符合分层架构规范
- 2.1 后端目录结构 - 创建backend目录，分层组织代码（api/services/crud/database）
- 2.2 脚本目录结构 - 创建scripts目录，存放工具脚本和测试脚本
- 2.3 数据目录结构 - 创建PdfData、uploads、output等数据目录
- 2.4 测试目录结构 - 创建tests目录，组织单元测试和集成测试

#### 3. Claude配置体系建立（P1）
验收标准：Claude配置文件完整，开发规范明确
- 3.1 主配置文件 - 创建.claude/CLAUDE.md，定义项目概览和配置
- 3.2 开发规范文件 - 创建.claude/CORE.md，定义代码规范和注释策略
- 3.3 技术文档目录 - 创建.claude/specs/目录，存放技术规范文档
- 3.4 上下文记录目录 - 创建.claude/context/目录，记录工作进展

#### 4. 基础工具脚本（P1）
验收标准：工具脚本可正常运行，提供便捷的开发辅助
- 4.1 数据库初始化脚本 - 编写init_database.py，初始化数据库表结构
- 4.2 数据库验证脚本 - 编写verify_database.py，验证数据库完整性
- 4.3 测试数据准备 - 收集6个沃尔玛PDF样本，放入PdfData目录

---

### Phase 2: PDF解析

#### 1. PDF解析引擎（P0）
验收标准：成功解析6个测试PDF，准确提取文本和图片
- 1.1 PDF转图片功能 - 使用PyMuPDF将PDF转换为300DPI图片
- 1.2 pdfplumber文本提取 - 使用pdfplumber提取PDF文本和表格内容
- 1.3 图像横向分割 - 基于OpenCV横线检测实现图像分割
- 1.4 左右区域处理 - 处理PDF左右两列布局，分别提取数据

#### 2. OCR识别引擎（P0）
验收标准：OCR识别准确率>90%，坐标偏差<20px
- 2.1 Apple Vision OCR集成 - 集成macOS原生Vision Framework实现OCR
- 2.2 置信度过滤机制 - 实现0.3阈值过滤低质量识别结果
- 2.3 坐标校准系统 - 实现OCR坐标校准，解决坐标偏差问题
- 2.4 中英文混合识别 - 支持中英文混合文档的准确识别

#### 3. 关键词定位与板块分割（P0）
验收标准：准确识别7个财务板块，板块识别准确率100%
- 3.1 7个板块关键词识别 - 识别Header、Sales、Refund、Adjustment、WFS、Other、Footer板块
- 3.2 板块范围计算 - 基于关键词Y坐标计算每个板块的范围
- 3.3 文本块归类 - 将OCR识别的文本块归类到对应板块
- 3.4 Footer误识别过滤 - 实现Footer特殊处理，过滤页眉页脚误识别

#### 4. 数据提取与结构化（P0）
验收标准：数据提取成功率>80%，JSON格式规范
- 4.1 键值对提取 - 提取金额和标签的键值对数据
- 4.2 日期范围提取 - 提取对账单开始和结束日期
- 4.3 金额格式解析 - 解析"$"和"美元"两种金额格式
- 4.4 文本合并策略 - 实现Y坐标阈值30px的文本合并
- 4.5 JSON标准化输出 - 输出标准化的JSON格式数据

#### 5. 坐标校准数据生成（P0）
验收标准：生成校准文件，校准后坐标偏差<10px
- 5.1 校准数据采集 - 采集真实PDF的OCR坐标和实际坐标
- 5.2 校准函数计算 - 计算坐标转换函数（线性变换）
- 5.3 校准文件生成 - 生成pkl格式的校准数据文件
- 5.4 校准效果验证 - 验证校准后的坐标准确性

#### 6. 可视化调试工具（P1）
验收标准：生成标注图片，清晰展示OCR识别结果
- 6.1 批量测试脚本 - 编写批量处理多个PDF的测试脚本
- 6.2 标注图片生成 - 生成带文本框、坐标、板块边界的可视化图片
- 6.3 OCR置信度诊断 - 诊断低置信度识别问题，输出诊断报告
- 6.4 Footer调试工具 - 专门调试Footer识别问题的可视化工具

---

### Phase 3: Web开发

#### 1. 数据库设计与实现（P0）✅ 已完成 - 2025-12-19
验收标准：数据库表结构完整，支持多数据库类型，优化版Schema
- ✅ 1.1 数据库表设计 - 设计10个核心表的字段和关系
- ✅ 1.2 ORM模型编写 - 使用SQLAlchemy编写ORM模型（优化版）
- ✅ 1.3 数据库配置 - 实现支持SQLite/MySQL/PostgreSQL的配置
- ✅ 1.4 数据库初始化 - 编写初始化脚本，自动创建表结构
- ✅ **1.5 字段频率分析** - 基于18个测试结果，确定30%阈值
- ✅ **1.6 字段名规范化** - 实现全角转半角、去标点、同义词映射（13个测试通过）
- ✅ **1.7 核心字段配置** - 定义37个核心字段和中英文映射
- ✅ **1.8 Schema优化** - 7个表添加other_total字段，移除低频字段列
- ✅ **1.9 数据处理器** - 实现规范化+核心字段+other_total计算逻辑
- ✅ **1.10 集成测试** - 5/5测试全部通过

**优化成果**:
- 核心字段: 37个（频率≥30%）
- 低频字段汇总: other_total字段
- 新增文件: 4个核心工具文件（1100行代码）
- 测试覆盖: 100%（5个集成测试）

#### 2. FastAPI项目搭建（P0）
验收标准：API服务可正常启动，健康检查接口可用
- 2.1 FastAPI应用创建 - 创建main.py，初始化FastAPI应用
- 2.2 应用配置管理 - 创建config.py，管理应用配置参数
- 2.3 路由注册机制 - 实现API路由自动注册机制
- 2.4 CORS中间件配置 - 配置跨域请求支持
- 2.5 健康检查接口 - 实现根路径和/health健康检查接口

#### 3. Pydantic数据模型（P0）
验收标准：数据模型完整，支持请求验证和响应序列化
- 3.1 PDF文件模型 - 定义PDFFileCreate/Update/Response模型
- 3.2 对账单头部模型 - 定义StatementHeaderCreate/Update/Response模型
- 3.3 销售明细模型 - 定义SalesDetailCreate/Update/Response模型
- 3.4 退款明细模型 - 定义RefundDetailCreate/Update/Response模型
- 3.5 完整数据模型 - 定义StatementDataResponse完整对账单数据模型
- 3.6 通用响应模型 - 定义PaginatedResponse和MessageResponse模型

#### 4. 数据库CRUD操作（P0）
验收标准：CRUD函数完整，支持事务管理
- 4.1 PDF文件CRUD - 实现PDF的创建、查询、更新、删除操作
- 4.2 对账单数据CRUD - 实现对账单各板块的创建、查询、更新操作
- 4.3 完整数据查询 - 实现获取PDF完整对账单数据的查询函数
- 4.4 完整数据更新 - 实现更新PDF完整对账单数据的更新函数
- 4.5 事务管理 - 实现数据库事务的提交和回滚管理

#### 5. PDF管理API接口（P0）
验收标准：4个接口全部实现，支持PDF上传和管理
- 5.1 PDF上传接口 - 实现POST /pdfs/upload接口，支持文件上传
- 5.2 PDF列表查询接口 - 实现GET /pdfs/接口，支持分页查询
- 5.3 PDF详情查询接口 - 实现GET /pdfs/{pdf_id}接口，查询PDF详情
- 5.4 PDF删除接口 - 实现DELETE /pdfs/{pdf_id}接口，支持级联删除

#### 6. 对账单数据API接口（P0）
验收标准：6个接口全部实现，支持数据查询和修改
- 6.1 完整数据查询接口 - 实现GET /statements/{pdf_id}/data接口
- 6.2 完整数据更新接口 - 实现PUT /statements/{pdf_id}/data接口
- 6.3 头部更新接口 - 实现PATCH /statements/{pdf_id}/header接口
- 6.4 销售更新接口 - 实现PATCH /statements/{pdf_id}/sales接口
- 6.5 退款更新接口 - 实现PATCH /statements/{pdf_id}/refund接口
- 6.6 数据验证接口 - 实现POST /statements/{pdf_id}/validate接口

#### 7. PDF解析服务集成（P0）
验收标准：解析服务可正常调用，数据自动保存到数据库
- 7.1 解析服务封装 - 封装pdf_parser_service.py，集成Phase 2解析流程
- 7.2 关键词提取服务 - 封装keyword_extractor.py，提取板块关键词
- 7.3 数据库保存逻辑 - 实现解析结果自动保存到8个板块表
- 7.4 批量解析支持 - 支持批量解析多个PDF文件

#### 8. 测试脚本编写（P0）
验收标准：测试脚本可正常运行，覆盖主要功能
- 8.1 API接口测试 - 编写test_api.py，测试所有API接口
- 8.2 完整流程测试 - 编写test_parse_pipeline.py，测试端到端流程
- 8.3 数据库验证测试 - 编写verify_database.py，验证数据库完整性

#### 9. API文档编写（P1）
验收标准：文档完整，包含所有接口说明和示例
- 9.1 完整API文档 - 编写API_README.md，包含所有接口详细说明
- 9.2 快速开始指南 - 编写API_QUICKSTART.md，5分钟快速入门
- 9.3 交互式API文档 - 配置Swagger UI，提供/api/docs交互式文档

#### 10. 补充板块支持（P1）
验收标准：8个板块全部支持，数据完整保存
- 10.1 Adjustment板块支持 - 补充adjustment_details的schemas和CRUD
- 10.2 WFS板块支持 - 补充wfs_details的schemas和CRUD
- 10.3 OtherActivity板块支持 - 补充other_activity_details的schemas和CRUD
- 10.4 Footer板块支持 - 补充statement_footers的schemas和CRUD
- 10.5 Payment板块支持 - 补充payment_details的schemas和CRUD

#### 11. 数据导出功能（P1）
验收标准：支持3种格式导出，数据格式规范
- 11.1 Excel导出功能 - 实现导出为Excel格式（.xlsx）
- 11.2 CSV导出功能 - 实现导出为CSV格式（.csv）
- 11.3 JSON导出功能 - 实现导出为JSON格式（.json）
- 11.4 批量导出支持 - 支持批量导出多个PDF的数据

#### 12. 批量处理功能（P2）
验收标准：支持批量上传和解析，任务队列正常工作
- 12.1 批量上传接口 - 实现POST /pdfs/batch-upload批量上传接口
- 12.2 批量解析接口 - 实现POST /pdfs/batch-parse批量解析接口
- 12.3 批量状态查询 - 实现GET /pdfs/batch-status批量状态查询接口
- 12.4 任务队列集成 - 集成Celery + Redis实现异步任务队列

#### 13. 用户认证和权限（P2）
验收标准：认证系统可用，权限控制有效
- 13.1 用户注册登录 - 实现用户注册和登录接口
- 13.2 JWT Token认证 - 实现JWT Token生成和验证
- 13.3 权限装饰器 - 实现权限检查装饰器
- 13.4 RBAC权限控制 - 实现基于角色的访问控制

---

### Phase 4: 数据分析

#### 1. 销售数据分析（P0）
验收标准：提供销售趋势图表，支持多维度分析
- 1.1 销售趋势分析 - 按时间维度分析销售趋势
- 1.2 商品销量统计 - 统计各商品的销量和销售额
- 1.3 销售渠道分析 - 分析不同渠道的销售情况
- 1.4 销售可视化图表 - 使用ECharts/Plotly生成销售图表

#### 2. 退款数据分析（P0）
验收标准：提供退款率统计，识别异常退款
- 2.1 退款率统计 - 计算整体和各商品的退款率
- 2.2 退款原因分析 - 分析退款原因分布
- 2.3 退款趋势分析 - 按时间维度分析退款趋势
- 2.4 异常退款识别 - 识别异常高退款率的商品

#### 3. 对账单对比功能（P0）
验收标准：支持多期对账单对比，差异清晰展示
- 3.1 多期数据对比 - 对比多个时期的对账单数据
- 3.2 差异计算和展示 - 计算并展示差异数据
- 3.3 同比环比分析 - 计算同比和环比增长率
- 3.4 对比可视化图表 - 生成对比图表

#### 4. 财务指标计算（P1）
验收标准：提供关键财务指标，计算准确
- 4.1 利润率计算 - 计算毛利率和净利率
- 4.2 周转率计算 - 计算库存周转率
- 4.3 成本分析 - 分析各项成本占比
- 4.4 盈利能力分析 - 综合评估盈利能力

#### 5. 数据报表生成（P1）
验收标准：支持PDF和Excel报表导出，格式规范
- 5.1 PDF报表生成 - 生成PDF格式的分析报表
- 5.2 Excel报表生成 - 生成Excel格式的数据报表
- 5.3 报表模板管理 - 支持自定义报表模板
- 5.4 定期报表生成 - 支持定期自动生成报表

#### 6. 自定义分析功能（P2）
验收标准：支持用户自定义分析维度和指标
- 6.1 自定义时间范围 - 支持用户自定义分析时间范围
- 6.2 自定义分析维度 - 支持用户自定义分析维度
- 6.3 自定义指标计算 - 支持用户自定义计算指标
- 6.4 保存分析配置 - 支持保存和复用分析配置

---

### Phase 5: 部署上线

#### 1. Docker容器化（P0）
验收标准：Docker镜像可正常构建和运行
- 1.1 Dockerfile编写 - 编写Dockerfile，定义容器构建过程
- 1.2 docker-compose配置 - 编写docker-compose.yml，编排多容器
- 1.3 环境变量配置 - 配置环境变量，分离敏感信息
- 1.4 容器镜像构建 - 构建Docker镜像并推送到镜像仓库

#### 2. Web服务器配置（P0）
验收标准：Nginx可正常代理API服务，HTTPS可用
- 2.1 Nginx安装配置 - 安装Nginx并配置反向代理
- 2.2 负载均衡配置 - 配置Nginx负载均衡（可选）
- 2.3 静态文件服务 - 配置静态文件服务（前端资源）
- 2.4 SSL证书配置 - 配置HTTPS证书，启用加密通信

#### 3. 生产数据库配置（P0）
验收标准：生产数据库可正常连接，数据安全
- 3.1 MySQL/PostgreSQL部署 - 部署生产环境数据库
- 3.2 数据库迁移脚本 - 编写SQLite到MySQL的数据迁移脚本
- 3.3 数据库备份策略 - 配置自动备份策略
- 3.4 数据库性能优化 - 优化数据库索引和查询性能

#### 4. 日志和监控系统（P1）
验收标准：日志完整收集，监控告警及时
- 4.1 日志收集配置 - 配置ELK/Loki日志收集
- 4.2 监控指标配置 - 配置Prometheus监控指标
- 4.3 告警规则配置 - 配置Grafana告警规则
- 4.4 性能监控面板 - 创建Grafana性能监控面板

#### 5. 自动化部署（P1）
验收标准：支持一键部署，CI/CD流程完整
- 5.1 CI/CD流程配置 - 配置GitHub Actions/Jenkins CI/CD
- 5.2 自动化测试 - 在CI中运行自动化测试
- 5.3 自动化构建 - 自动构建Docker镜像
- 5.4 自动化部署 - 自动部署到生产环境

#### 6. 前端界面开发（P2，可选）
验收标准：前端界面可用，用户体验良好
- 6.1 前端框架选择 - 选择React/Vue/Angular前端框架
- 6.2 页面布局设计 - 设计页面布局和导航结构
- 6.3 核心功能页面 - 开发PDF上传、数据查看、数据编辑页面
- 6.4 数据可视化页面 - 开发数据分析和图表展示页面

#### 7. 性能测试和优化（P1）
验收标准：系统响应时间<2秒，并发支持>100
- 7.1 压力测试 - 使用JMeter/Locust进行压力测试
- 7.2 性能瓶颈分析 - 分析并识别性能瓶颈
- 7.3 性能优化实施 - 实施数据库、API、代码层面的优化
- 7.4 性能基准建立 - 建立性能基准和监控指标

#### 8. 安全加固（P1）
验收标准：通过安全扫描，无高危漏洞
- 8.1 依赖漏洞扫描 - 使用Snyk/OWASP扫描依赖漏洞
- 8.2 API安全加固 - 实施Rate Limiting、输入验证等安全措施
- 8.3 数据加密 - 敏感数据加密存储和传输
- 8.4 安全审计日志 - 记录所有敏感操作的审计日志

---

## 附录：快速参考

### 常用命令
```bash
# 激活虚拟环境
source venv/bin/activate

# 启动API服务
cd backend && uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# 初始化数据库
python scripts/init_database.py

# 运行完整流程测试
python scripts/test_parse_pipeline.py

# 运行批量测试
python scripts/batch_test_direct_extraction.py
```

### 重要路径
- **项目根目录**: `/Users/jiaxinming/JxmWork/walmart-a/`
- **数据库文件**: `walmart_pdf_parser.db`
- **API文档**: http://localhost:8000/api/docs
- **测试PDF**: `PdfData/`
- **上传目录**: `uploads/`

### 相关文档
- **主配置**: `.claude/CLAUDE.md`
- **开发规范**: `.claude/CORE.md`
- **API文档**: `API_README.md`
- **快速指南**: `API_QUICKSTART.md`
- **日常任务**: `todo.md`

---

**文件版本**: v1.0
**创建时间**: 2025-12-19
**维护者**: 项目团队
**更新频率**: 重大里程碑后更新
**配合文件**: `todo.md`（日常任务和进度跟踪）

---

**END OF TaskList.md**
