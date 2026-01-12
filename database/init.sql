-- 戶政司門牌查詢資料庫初始化腳本
-- 建立時會自動執行

-- 使用資料庫
USE household_db;

-- 設定字元集
SET NAMES utf8mb4;
SET CHARACTER SET utf8mb4;

-- ============================================================
-- 查詢批次表：記錄每次批量查詢的資訊
-- 這是最重要的表，用來追蹤資料是什麼時候查詢的
-- ============================================================
CREATE TABLE IF NOT EXISTS query_batches (
    id INT AUTO_INCREMENT PRIMARY KEY,
    batch_uuid VARCHAR(36) NOT NULL COMMENT '批次 UUID，用於程式關聯',
    city_code VARCHAR(20) COMMENT '查詢的城市代碼',
    city_name VARCHAR(50) COMMENT '查詢的城市名稱',
    start_date VARCHAR(20) COMMENT '查詢起始日期',
    end_date VARCHAR(20) COMMENT '查詢結束日期',
    register_kind VARCHAR(10) COMMENT '編釘類別代碼',
    total_districts INT DEFAULT 0 COMMENT '查詢的行政區數量',
    total_records INT DEFAULT 0 COMMENT '查詢到的總筆數',
    status ENUM('running', 'completed', 'failed') DEFAULT 'running' COMMENT '查詢狀態',
    error_message TEXT COMMENT '錯誤訊息',
    query_started_at DATETIME NOT NULL COMMENT '查詢開始時間',
    query_finished_at DATETIME COMMENT '查詢結束時間',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '記錄建立時間',
    UNIQUE KEY uk_batch_uuid (batch_uuid),
    INDEX idx_status (status),
    INDEX idx_query_started_at (query_started_at),
    INDEX idx_city_code (city_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='查詢批次表';

-- ============================================================
-- 門牌資料表：儲存每筆門牌資料
-- batch_id 關聯到 query_batches，可以追蹤每筆資料是哪次查詢抓到的
-- ============================================================
CREATE TABLE IF NOT EXISTS household_records (
    id INT AUTO_INCREMENT PRIMARY KEY,
    batch_id INT COMMENT '關聯的查詢批次 ID',
    city VARCHAR(50) COMMENT '縣市',
    district VARCHAR(50) COMMENT '行政區',
    full_address VARCHAR(500) COMMENT '完整地址',
    edit_date VARCHAR(20) COMMENT '編釘日期',
    edit_type_code VARCHAR(10) COMMENT '編釘類別代碼',
    edit_type_name VARCHAR(50) COMMENT '編釘類別名稱',
    raw_data JSON COMMENT '原始回應資料(JSON格式)',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '建立時間',
    INDEX idx_batch_id (batch_id),
    INDEX idx_city_district (city, district),
    INDEX idx_edit_date (edit_date),
    INDEX idx_edit_type_code (edit_type_code),
    FOREIGN KEY (batch_id) REFERENCES query_batches(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='門牌資料表';

-- ============================================================
-- 各行政區查詢結果表：記錄批次中每個行政區的查詢結果
-- ============================================================
CREATE TABLE IF NOT EXISTS district_query_results (
    id INT AUTO_INCREMENT PRIMARY KEY,
    batch_id INT NOT NULL COMMENT '關聯的查詢批次 ID',
    district_code VARCHAR(20) COMMENT '行政區代碼',
    district_name VARCHAR(50) COMMENT '行政區名稱',
    record_count INT DEFAULT 0 COMMENT '該區查詢到的筆數',
    status ENUM('success', 'failed', 'no_data') DEFAULT 'success' COMMENT '查詢狀態',
    error_message TEXT COMMENT '錯誤訊息',
    queried_at DATETIME COMMENT '查詢時間',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '建立時間',
    INDEX idx_batch_id (batch_id),
    INDEX idx_district_code (district_code),
    FOREIGN KEY (batch_id) REFERENCES query_batches(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='行政區查詢結果表';

-- ============================================================
-- 檢視：查詢批次摘要（方便查看每次查詢的概況）
-- ============================================================
CREATE OR REPLACE VIEW v_batch_summary AS
SELECT 
    qb.id,
    qb.batch_uuid,
    qb.city_name,
    qb.start_date,
    qb.end_date,
    qb.total_districts,
    qb.total_records,
    qb.status,
    qb.query_started_at,
    qb.query_finished_at,
    TIMESTAMPDIFF(SECOND, qb.query_started_at, IFNULL(qb.query_finished_at, NOW())) as duration_seconds
FROM query_batches qb
ORDER BY qb.query_started_at DESC;

-- ============================================================
-- 檢視：各區域資料統計
-- ============================================================
CREATE OR REPLACE VIEW v_district_statistics AS
SELECT 
    hr.city,
    hr.district,
    hr.edit_type_name,
    COUNT(*) as record_count,
    MIN(hr.edit_date) as earliest_date,
    MAX(hr.edit_date) as latest_date,
    MAX(qb.query_started_at) as last_query_time
FROM household_records hr
LEFT JOIN query_batches qb ON hr.batch_id = qb.id
GROUP BY hr.city, hr.district, hr.edit_type_name
ORDER BY hr.city, hr.district, hr.edit_type_name;

-- ============================================================
-- 檢視：最近查詢記錄
-- ============================================================
CREATE OR REPLACE VIEW v_recent_queries AS
SELECT 
    qb.id,
    qb.city_name,
    DATE_FORMAT(qb.query_started_at, '%Y-%m-%d %H:%i:%s') as query_time,
    CONCAT(qb.start_date, ' ~ ', qb.end_date) as date_range,
    qb.total_records,
    qb.status,
    GROUP_CONCAT(
        CONCAT(dqr.district_name, ':', dqr.record_count) 
        ORDER BY dqr.district_name 
        SEPARATOR ', '
    ) as district_details
FROM query_batches qb
LEFT JOIN district_query_results dqr ON qb.id = dqr.batch_id
GROUP BY qb.id
ORDER BY qb.query_started_at DESC
LIMIT 20;

-- 顯示建立結果
SELECT 'Database initialized successfully!' as message;
SHOW TABLES;
