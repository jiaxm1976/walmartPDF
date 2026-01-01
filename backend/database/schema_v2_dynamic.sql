-- Walmart PDF 动态板块数据库初始化脚本 V2
-- 一个 PDF = 一条 statement 记录
-- 每个板块 = 一条 section_data 记录
-- 低频字段合并到 {section_name}_其他

PRAGMA foreign_keys = ON;

-- ============================================================================
-- 表 1: statements (语句主表)
-- ============================================================================
DROP TABLE IF EXISTS section_data;
DROP TABLE IF EXISTS statements;

CREATE TABLE statements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pdf_name VARCHAR(255) NOT NULL UNIQUE,
    statement_period VARCHAR(100),
    payment_to_you DECIMAL(12,2),
    opening_balance DECIMAL(12,2),
    reserve_fund DECIMAL(12,2),
    pending_payment DECIMAL(12,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_statements_pdf_name ON statements(pdf_name);
CREATE INDEX idx_statements_period ON statements(statement_period);

-- ============================================================================
-- 表 2: section_data (板块数据从表)
-- ============================================================================
CREATE TABLE section_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    statement_id INTEGER NOT NULL,
    section_name VARCHAR(50) NOT NULL,
    data JSON NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(statement_id) REFERENCES statements(id) ON DELETE CASCADE,
    UNIQUE(statement_id, section_name)
);

CREATE INDEX idx_section_data_statement_id ON section_data(statement_id);
CREATE INDEX idx_section_data_section_name ON section_data(section_name);

-- ============================================================================
-- 频率字段映射表 (用于导入时识别低频字段)
-- ============================================================================
CREATE TABLE field_frequency (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    section_name VARCHAR(50) NOT NULL,
    field_name VARCHAR(100) NOT NULL,
    frequency INTEGER NOT NULL,
    frequency_percent REAL NOT NULL,
    UNIQUE(section_name, field_name)
);

-- 插入频率数据（基于 6 个 PDF 的分析）
INSERT INTO field_frequency (section_name, field_name, frequency, frequency_percent) VALUES
-- header 板块
('header', '统计区间', 6, 100.0),
('header', '向您支付的金额', 6, 100.0),
('header', '期初余额', 6, 100.0),
('header', '备用金', 6, 100.0),
('header', '回款等待', 6, 100.0),
('header', '期末余额', 5, 83.3),

-- 销售板块
('销售', '产品价格', 6, 100.0),
('销售', '运输', 6, 100.0),
('销售', '已收税净额', 6, 100.0),
('销售', '净佣金', 6, 100.0),
('销售', '扣缴税款净额', 6, 100.0),
('销售', '总计', 6, 100.0),
('销售', 'WFS运输退款', 5, 83.3),
('销售', 'WFS运输税退款', 5, 83.3),
('销售', 'T沃尔玛出资的节余', 5, 83.3),
('销售', '其他税款(费用)', 1, 16.7),

-- 退款板块
('退款', '佣金', 6, 100.0),
('退款', '产品价格', 6, 100.0),
('退款', '运输', 6, 100.0),
('退款', '已收税净额', 6, 100.0),
('退款', '扣缴税款净额', 6, 100.0),
('退款', '总计', 6, 100.0),
('退款', 'WFS总折扣', 6, 100.0),
('退款', 'T沃尔玛出资的节余', 5, 83.3),
('退款', 'T沃尔玛出资的节余总额', 1, 16.7),

-- 其他活动板块
('其他活动', '沃尔玛产品广告', 6, 100.0),

-- 调整板块
('调整', '沃尔玛全球运输标签服务费', 3, 50.0),
('调整', '退货沃尔玛运输服务费', 1, 16.7),

-- WFS 商品服务板块
('沃尔玛商品服务(WFS)', 'WFS总折扣', 6, 100.0),
('沃尔玛商品服务(WFS)', 'WFS商品费', 4, 66.7),
('沃尔玛商品服务(WFS)', 'WFS以太坊费', 4, 66.7),
('沃尔玛商品服务(WFS)', 'WFS退货费', 1, 16.7),
('沃尔玛商品服务(WFS)', '世界FS调整', 1, 16.7),
('沃尔玛商品服务(WFS)', 'WFSRC库存支出', 1, 16.7),

-- WFS 配送服务板块
('沃尔玛配送服务(WFS)', 'WFS配送费', 1, 16.7),
('沃尔玛配送服务(WFS)', 'WFS仓储费', 1, 16.7),

-- footer 板块
('footer', '向您支付的金额', 6, 100.0),
('footer', '专业列表', 1, 16.7),
('footer', '其他', 1, 16.7);

-- ============================================================================
-- 配置表
-- ============================================================================
CREATE TABLE db_config (
    key VARCHAR(100) PRIMARY KEY,
    value TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO db_config (key, value) VALUES
('schema_version', '2.0.0'),
('design_type', 'dynamic_sections'),
('last_updated', CURRENT_TIMESTAMP),
('total_pdfs', '6'),
('total_fields', '31'),
('total_sections', '8'),
('frequency_threshold', '2');

-- ============================================================================
-- 视图：用于常见查询
-- ============================================================================

-- 视图 1: 完整语句（联接所有板块）
CREATE VIEW statements_complete AS
SELECT 
    s.id,
    s.pdf_name,
    s.statement_period,
    s.payment_to_you,
    s.opening_balance,
    s.reserve_fund,
    s.pending_payment,
    GROUP_CONCAT(sd.section_name, ', ') as sections
FROM statements s
LEFT JOIN section_data sd ON s.id = sd.statement_id
GROUP BY s.id;

-- 视图 2: 销售额和退款统计
CREATE VIEW sales_refund_summary AS
SELECT 
    s.statement_period,
    (SELECT json_extract(data, '$.总计') FROM section_data 
     WHERE statement_id = s.id AND section_name = '销售') as sales_total,
    (SELECT json_extract(data, '$.总计') FROM section_data 
     WHERE statement_id = s.id AND section_name = '退款') as refund_total
FROM statements s;
