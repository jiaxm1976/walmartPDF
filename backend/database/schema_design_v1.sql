<<<<<<< HEAD
-- schema_design_v1.sql has been archived; please use V2 dynamic schema via scripts/init_database_v2.py
-- Archived on 2026-01-02
=======
-- Walmart PDF 数据库初始化脚本
-- 设计原则：频率 ≥ 2 的字段为 DB 列，频率 = 1 的字段放入 JSON

PRAGMA foreign_keys = ON;

-- 表 1: statement_headers (基本信息)
CREATE TABLE IF NOT EXISTS statement_headers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_pdf_name VARCHAR(255) NOT NULL UNIQUE,
    statement_period VARCHAR(100) NOT NULL,
    payment_to_you DECIMAL(12,2) NOT NULL,
    opening_balance DECIMAL(12,2) NOT NULL,
    reserve_fund DECIMAL(12,2) NOT NULL,
    pending_payment DECIMAL(12,2) NOT NULL,
    closing_balance DECIMAL(12,2) DEFAULT NULL,
    processing_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    extra_data JSON DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_statement_headers_pdf_name ON statement_headers(source_pdf_name);
CREATE INDEX IF NOT EXISTS idx_statement_headers_period ON statement_headers(statement_period);

-- 表 2: sales_details (销售明细)
CREATE TABLE IF NOT EXISTS sales_details (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    header_id INTEGER NOT NULL,
    product_price DECIMAL(12,2) NOT NULL,
    shipping DECIMAL(12,2) NOT NULL,
    tax_collected_net DECIMAL(12,2) NOT NULL,
    net_commission DECIMAL(12,2) NOT NULL,
    withholding_tax_net DECIMAL(12,2) NOT NULL,
    sales_total DECIMAL(12,2) NOT NULL,
    wfs_shipping_refund DECIMAL(12,2) DEFAULT 0.00,
    wfs_shipping_tax_refund DECIMAL(12,2) DEFAULT 0.00,
    walmart_contribution_margin DECIMAL(12,2) DEFAULT NULL,
    extra_data JSON DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(header_id) REFERENCES statement_headers(id) ON DELETE CASCADE,
    CHECK (product_price >= 0),
    CHECK (sales_total >= 0)
);

CREATE INDEX IF NOT EXISTS idx_sales_details_header_id ON sales_details(header_id);

-- 表 3: refund_details (退款明细)
CREATE TABLE IF NOT EXISTS refund_details (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    header_id INTEGER NOT NULL,
    commission DECIMAL(12,2) NOT NULL,
    product_price DECIMAL(12,2) NOT NULL,
    shipping DECIMAL(12,2) NOT NULL,
    tax_collected_net DECIMAL(12,2) NOT NULL,
    withholding_tax_net DECIMAL(12,2) NOT NULL,
    refund_total DECIMAL(12,2) NOT NULL,
    wfs_total_discount DECIMAL(12,2) NOT NULL,
    walmart_contribution_margin DECIMAL(12,2) DEFAULT NULL,
    extra_data JSON DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(header_id) REFERENCES statement_headers(id) ON DELETE CASCADE,
    CHECK (commission >= 0),
    CHECK (refund_total >= 0)
);

CREATE INDEX IF NOT EXISTS idx_refund_details_header_id ON refund_details(header_id);

-- 表 4: other_activities (其他活动)
CREATE TABLE IF NOT EXISTS other_activities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    header_id INTEGER NOT NULL,
    activity_type VARCHAR(100) NOT NULL,
    walmart_product_advertising DECIMAL(12,2) DEFAULT NULL,
    extra_data JSON DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(header_id) REFERENCES statement_headers(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_other_activities_header_id ON other_activities(header_id);

-- 表 5: adjustments (调整)
CREATE TABLE IF NOT EXISTS adjustments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    header_id INTEGER NOT NULL,
    adjustment_type VARCHAR(100) NOT NULL,
    walmart_global_shipping_label_fee DECIMAL(12,2) DEFAULT NULL,
    extra_data JSON DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(header_id) REFERENCES statement_headers(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_adjustments_header_id ON adjustments(header_id);

-- 表 6: wfs_services (WFS 服务)
CREATE TABLE IF NOT EXISTS wfs_services (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    header_id INTEGER NOT NULL,
    service_type VARCHAR(50) NOT NULL,
    wfs_goods_fee DECIMAL(12,2) DEFAULT NULL,
    wfs_ethereum_fee DECIMAL(12,2) DEFAULT NULL,
    wfs_total_discount DECIMAL(12,2) DEFAULT NULL,
    extra_data JSON DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(header_id) REFERENCES statement_headers(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_wfs_services_header_id ON wfs_services(header_id);
CREATE INDEX IF NOT EXISTS idx_wfs_services_type ON wfs_services(service_type);

-- 表 7: section_metadata (板块元数据)
CREATE TABLE IF NOT EXISTS section_metadata (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    header_id INTEGER NOT NULL,
    section_name VARCHAR(50) NOT NULL,
    field_count INTEGER DEFAULT 0,
    detail_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(header_id) REFERENCES statement_headers(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_section_metadata_header_id ON section_metadata(header_id);

-- 视图：完整语句视图
CREATE VIEW IF NOT EXISTS statement_complete AS
SELECT 
    h.id as statement_id,
    h.source_pdf_name,
    h.statement_period,
    h.payment_to_you,
    h.opening_balance,
    h.closing_balance,
    s.product_price as sales_product_price,
    s.sales_total,
    r.product_price as refund_product_price,
    r.refund_total,
    oa.walmart_product_advertising,
    wfs.wfs_goods_fee,
    h.created_at
FROM statement_headers h
LEFT JOIN sales_details s ON h.id = s.header_id
LEFT JOIN refund_details r ON h.id = r.header_id
LEFT JOIN other_activities oa ON h.id = oa.header_id
LEFT JOIN wfs_services wfs ON h.id = wfs.header_id AND wfs.service_type LIKE 'fba_%';

-- 视图：财务汇总
CREATE VIEW IF NOT EXISTS financial_summary AS
SELECT 
    h.statement_period,
    COUNT(DISTINCT h.id) as statement_count,
    ROUND(AVG(h.payment_to_you), 2) as avg_payment,
    ROUND(SUM(h.payment_to_you), 2) as total_payment,
    ROUND(SUM(s.sales_total), 2) as total_sales,
    ROUND(SUM(r.refund_total), 2) as total_refunds
FROM statement_headers h
LEFT JOIN sales_details s ON h.id = s.header_id
LEFT JOIN refund_details r ON h.id = r.header_id
GROUP BY h.statement_period;

-- 配置表
CREATE TABLE IF NOT EXISTS db_config (
    key VARCHAR(100) PRIMARY KEY,
    value TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT OR REPLACE INTO db_config (key, value) VALUES 
    ('schema_version', '1.0.0'),
    ('last_updated', CURRENT_TIMESTAMP),
    ('design_based_on_pdfs', '6'),
    ('total_unique_fields', '31'),
    ('db_fields_count', '19'),
    ('json_fields_count', '12');
>>>>>>> 28b8e1f6342da6913199c0551ceba7975bdf3a7b
