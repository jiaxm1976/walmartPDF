-- ============================================================
-- Walmart PDF解析系统 - 数据库表结构设计
-- 数据库: walmart_pdf_parser
-- 版本: v1.0
-- 创建日期: 2025-12-18
-- ============================================================

-- 设置字符集
SET NAMES utf8mb4;
SET CHARACTER SET utf8mb4;

-- ============================================================
-- 1. PDF文件主表
-- ============================================================
CREATE TABLE IF NOT EXISTS pdf_files (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY COMMENT 'PDF文件ID',
    filename VARCHAR(255) NOT NULL COMMENT 'PDF文件名',
    original_filename VARCHAR(255) NOT NULL COMMENT '原始文件名',
    file_path VARCHAR(500) NOT NULL COMMENT '文件存储路径',
    file_size BIGINT UNSIGNED NOT NULL COMMENT '文件大小（字节）',
    file_hash VARCHAR(64) NOT NULL COMMENT 'SHA256文件哈希',
    upload_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '上传时间',
    process_status ENUM('pending', 'processing', 'success', 'failed') NOT NULL DEFAULT 'pending' COMMENT '处理状态',
    process_time DATETIME NULL COMMENT '处理完成时间',
    error_message TEXT NULL COMMENT '错误信息',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',

    INDEX idx_filename (filename),
    INDEX idx_file_hash (file_hash),
    INDEX idx_upload_time (upload_time),
    INDEX idx_process_status (process_status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='PDF文件主表';


-- ============================================================
-- 2. 对账单头部信息表
-- ============================================================
CREATE TABLE IF NOT EXISTS statement_headers (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY COMMENT '头部信息ID',
    pdf_file_id BIGINT UNSIGNED NOT NULL COMMENT 'PDF文件ID（外键）',
    start_date DATE NOT NULL COMMENT '对账单开始日期',
    end_date DATE NOT NULL COMMENT '对账单结束日期',
    opening_balance DECIMAL(15, 2) NOT NULL DEFAULT 0.00 COMMENT '期初余额',
    reserve_funds DECIMAL(15, 2) NOT NULL DEFAULT 0.00 COMMENT '备用金',
    awaiting_payment DECIMAL(15, 2) NOT NULL DEFAULT 0.00 COMMENT '回款等待',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',

    FOREIGN KEY (pdf_file_id) REFERENCES pdf_files(id) ON DELETE CASCADE,
    INDEX idx_pdf_file_id (pdf_file_id),
    INDEX idx_date_range (start_date, end_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='对账单头部信息表';


-- ============================================================
-- 3. 销售明细表
-- ============================================================
CREATE TABLE IF NOT EXISTS sales_details (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY COMMENT '销售明细ID',
    pdf_file_id BIGINT UNSIGNED NOT NULL COMMENT 'PDF文件ID（外键）',
    product_price DECIMAL(15, 2) NOT NULL DEFAULT 0.00 COMMENT '产品价格',
    shipping DECIMAL(15, 2) NOT NULL DEFAULT 0.00 COMMENT '运输费用',
    wfs_shipping_refund DECIMAL(15, 2) NOT NULL DEFAULT 0.00 COMMENT 'WFS运输退款',
    net_tax_collected DECIMAL(15, 2) NOT NULL DEFAULT 0.00 COMMENT '已收税净额',
    other_tax_fees DECIMAL(15, 2) NOT NULL DEFAULT 0.00 COMMENT '其他税款（费用）',
    net_commission DECIMAL(15, 2) NOT NULL DEFAULT 0.00 COMMENT '净佣金',
    withholding_tax DECIMAL(15, 2) NOT NULL DEFAULT 0.00 COMMENT '扣缴税款净额',
    wfs_shipping_tax_refund DECIMAL(15, 2) NOT NULL DEFAULT 0.00 COMMENT 'WFS运输税退款',
    walmart_funded_savings DECIMAL(15, 2) NOT NULL DEFAULT 0.00 COMMENT '沃尔玛出资的节余',
    total DECIMAL(15, 2) NOT NULL DEFAULT 0.00 COMMENT '总计',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',

    FOREIGN KEY (pdf_file_id) REFERENCES pdf_files(id) ON DELETE CASCADE,
    INDEX idx_pdf_file_id (pdf_file_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='销售明细表';


-- ============================================================
-- 4. 退款明细表
-- ============================================================
CREATE TABLE IF NOT EXISTS refund_details (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY COMMENT '退款明细ID',
    pdf_file_id BIGINT UNSIGNED NOT NULL COMMENT 'PDF文件ID（外键）',
    product_price DECIMAL(15, 2) NOT NULL DEFAULT 0.00 COMMENT '产品价格（退款）',
    shipping DECIMAL(15, 2) NOT NULL DEFAULT 0.00 COMMENT '运输费用（退款）',
    net_tax_collected DECIMAL(15, 2) NOT NULL DEFAULT 0.00 COMMENT '已收税净额',
    commission DECIMAL(15, 2) NOT NULL DEFAULT 0.00 COMMENT '佣金',
    withholding_tax DECIMAL(15, 2) NOT NULL DEFAULT 0.00 COMMENT '扣缴税款净额',
    walmart_funded_savings DECIMAL(15, 2) NOT NULL DEFAULT 0.00 COMMENT '沃尔玛出资的节余',
    total DECIMAL(15, 2) NOT NULL DEFAULT 0.00 COMMENT '总计',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',

    FOREIGN KEY (pdf_file_id) REFERENCES pdf_files(id) ON DELETE CASCADE,
    INDEX idx_pdf_file_id (pdf_file_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='退款明细表';


-- ============================================================
-- 5. 调整明细表
-- ============================================================
CREATE TABLE IF NOT EXISTS adjustment_details (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY COMMENT '调整明细ID',
    pdf_file_id BIGINT UNSIGNED NOT NULL COMMENT 'PDF文件ID（外键）',
    return_shipping_fee DECIMAL(15, 2) NOT NULL DEFAULT 0.00 COMMENT '退货沃尔玛运输服务费',
    global_shipping_label_fee DECIMAL(15, 2) NOT NULL DEFAULT 0.00 COMMENT '沃尔玛全球运输标签服务费',
    total DECIMAL(15, 2) NOT NULL DEFAULT 0.00 COMMENT '总计',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',

    FOREIGN KEY (pdf_file_id) REFERENCES pdf_files(id) ON DELETE CASCADE,
    INDEX idx_pdf_file_id (pdf_file_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='调整明细表';


-- ============================================================
-- 6. WFS服务明细表
-- ============================================================
CREATE TABLE IF NOT EXISTS wfs_details (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY COMMENT 'WFS明细ID',
    pdf_file_id BIGINT UNSIGNED NOT NULL COMMENT 'PDF文件ID（外键）',
    wfs_fee DECIMAL(15, 2) NOT NULL DEFAULT 0.00 COMMENT '沃尔玛商品服务（WFS）费用',
    wfs_return_fee DECIMAL(15, 2) NOT NULL DEFAULT 0.00 COMMENT 'WFS退货费',
    wfs_disposal_fee DECIMAL(15, 2) NOT NULL DEFAULT 0.00 COMMENT 'WFS处置费',
    wfs_adjustment DECIMAL(15, 2) NOT NULL DEFAULT 0.00 COMMENT 'WFS调整',
    wfs_rc_inventory_fee DECIMAL(15, 2) NOT NULL DEFAULT 0.00 COMMENT 'WFS RC库存支出',
    total DECIMAL(15, 2) NOT NULL DEFAULT 0.00 COMMENT '总计',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',

    FOREIGN KEY (pdf_file_id) REFERENCES pdf_files(id) ON DELETE CASCADE,
    INDEX idx_pdf_file_id (pdf_file_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='WFS服务明细表';


-- ============================================================
-- 7. 其他活动明细表
-- ============================================================
CREATE TABLE IF NOT EXISTS other_activity_details (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY COMMENT '其他活动明细ID',
    pdf_file_id BIGINT UNSIGNED NOT NULL COMMENT 'PDF文件ID（外键）',
    walmart_product_ads DECIMAL(15, 2) NOT NULL DEFAULT 0.00 COMMENT '沃尔玛产品广告费用',
    total DECIMAL(15, 2) NOT NULL DEFAULT 0.00 COMMENT '总计',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',

    FOREIGN KEY (pdf_file_id) REFERENCES pdf_files(id) ON DELETE CASCADE,
    INDEX idx_pdf_file_id (pdf_file_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='其他活动明细表';


-- ============================================================
-- 8. 对账单尾部信息表
-- ============================================================
CREATE TABLE IF NOT EXISTS statement_footers (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY COMMENT '尾部信息ID',
    pdf_file_id BIGINT UNSIGNED NOT NULL COMMENT 'PDF文件ID（外键）',
    amount_paid_to_you DECIMAL(15, 2) NOT NULL DEFAULT 0.00 COMMENT '向您支付的金额',
    closing_balance DECIMAL(15, 2) NOT NULL DEFAULT 0.00 COMMENT '期末余额',
    savings DECIMAL(15, 2) NOT NULL DEFAULT 0.00 COMMENT '储蓄',
    cost_savings DECIMAL(15, 2) NOT NULL DEFAULT 0.00 COMMENT '节省开支',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',

    FOREIGN KEY (pdf_file_id) REFERENCES pdf_files(id) ON DELETE CASCADE,
    INDEX idx_pdf_file_id (pdf_file_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='对账单尾部信息表';


-- ============================================================
-- 9. 付款详情表
-- ============================================================
CREATE TABLE IF NOT EXISTS payment_details (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY COMMENT '付款详情ID',
    pdf_file_id BIGINT UNSIGNED NOT NULL COMMENT 'PDF文件ID（外键）',
    status VARCHAR(50) NOT NULL DEFAULT '' COMMENT '付款状态',
    payment_date DATE NULL COMMENT '付款日期',
    payment_frequency VARCHAR(50) NOT NULL DEFAULT '' COMMENT '周期付款',
    payment_method VARCHAR(100) NOT NULL DEFAULT '' COMMENT '付款方式',
    device_method VARCHAR(100) NOT NULL DEFAULT '' COMMENT '设备方式',
    amount_to_be_paid DECIMAL(15, 2) NOT NULL DEFAULT 0.00 COMMENT '待付款金额',
    amount_waiting_return DECIMAL(15, 2) NOT NULL DEFAULT 0.00 COMMENT '等待回款金额',
    return_waiting_period VARCHAR(50) NOT NULL DEFAULT '' COMMENT '回款等待期',
    warning_message TEXT NULL COMMENT '警告信息',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',

    FOREIGN KEY (pdf_file_id) REFERENCES pdf_files(id) ON DELETE CASCADE,
    INDEX idx_pdf_file_id (pdf_file_id),
    INDEX idx_payment_date (payment_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='付款详情表';


-- ============================================================
-- 10. 动态字段扩展表（用于存储不规则字段）
-- ============================================================
CREATE TABLE IF NOT EXISTS dynamic_fields (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY COMMENT '动态字段ID',
    pdf_file_id BIGINT UNSIGNED NOT NULL COMMENT 'PDF文件ID（外键）',
    section_type ENUM('sales', 'refund', 'adjustment', 'wfs', 'other', 'footer') NOT NULL COMMENT '板块类型',
    field_name VARCHAR(255) NOT NULL COMMENT '字段名称',
    field_value VARCHAR(500) NOT NULL COMMENT '字段值',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',

    FOREIGN KEY (pdf_file_id) REFERENCES pdf_files(id) ON DELETE CASCADE,
    INDEX idx_pdf_file_id (pdf_file_id),
    INDEX idx_section_type (section_type),
    INDEX idx_field_name (field_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='动态字段扩展表';


-- ============================================================
-- END OF SCHEMA
-- ============================================================
