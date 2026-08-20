-- ====================================================================
-- FRAUD & ANOMALY DETECTION ENGINE - MYSQL DATABASE SCHEMA
-- ====================================================================

-- 1. Create Database
CREATE DATABASE IF NOT EXISTS fraud_detection_db;
USE fraud_detection_db;

-- 2. Create Table: transactions
-- Stores all ingested & validated transaction records
CREATE TABLE IF NOT EXISTS transactions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    transaction_id VARCHAR(50) NOT NULL UNIQUE,
    user_id VARCHAR(50) NOT NULL,
    transaction_amount DECIMAL(12, 2) NOT NULL,
    transaction_date DATETIME NOT NULL,
    location VARCHAR(100) NOT NULL,
    payment_method VARCHAR(50) NOT NULL,
    status VARCHAR(20) DEFAULT 'SUCCESS',
    device_id VARCHAR(100) DEFAULT 'UNKNOWN',
    ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_user_id (user_id),
    INDEX idx_transaction_date (transaction_date),
    INDEX idx_transaction_id (transaction_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 3. Create Table: flagged_transactions
-- Stores transactions identified as suspicious with calculated risk scores
CREATE TABLE IF NOT EXISTS flagged_transactions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    transaction_id VARCHAR(50) NOT NULL,
    user_id VARCHAR(50) NOT NULL,
    transaction_amount DECIMAL(12, 2) NOT NULL,
    transaction_date DATETIME NOT NULL,
    location VARCHAR(100) NOT NULL,
    payment_method VARCHAR(50) NOT NULL,
    risk_score INT NOT NULL,
    risk_level ENUM('LOW', 'MEDIUM', 'HIGH') NOT NULL,
    triggered_rules TEXT NOT NULL,
    rule_count INT NOT NULL DEFAULT 1,
    status VARCHAR(30) DEFAULT 'FLAGGED',
    flagged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (transaction_id) REFERENCES transactions(transaction_id) ON DELETE CASCADE,
    INDEX idx_risk_level (risk_level),
    INDEX idx_flagged_user (user_id),
    INDEX idx_flagged_date (transaction_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 4. Create Table: audit_logs
-- Maintains complete audit trial for compliance monitoring
CREATE TABLE IF NOT EXISTS audit_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    transaction_id VARCHAR(50) NOT NULL,
    timestamp DATETIME NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    triggered_rules TEXT,
    risk_score INT,
    status VARCHAR(30) NOT NULL,
    log_message TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_audit_tx (transaction_id),
    INDEX idx_audit_time (timestamp)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ====================================================================
-- USEFUL COMPLIANCE & REVIEW QUERIES
-- ====================================================================

-- Query A: Get All High-Risk Flagged Transactions
-- SELECT * FROM flagged_transactions WHERE risk_level = 'HIGH' ORDER BY risk_score DESC;

-- Query B: Monthly Fraud Summary Report
-- SELECT 
--     DATE_FORMAT(transaction_date, '%Y-%m') AS month,
--     COUNT(*) AS total_flagged_transactions,
--     SUM(transaction_amount) AS total_flagged_amount,
--     AVG(risk_score) AS average_risk_score,
--     SUM(CASE WHEN risk_level = 'HIGH' THEN 1 ELSE 0 END) AS high_risk_count,
--     SUM(CASE WHEN risk_level = 'MEDIUM' THEN 1 ELSE 0 END) AS medium_risk_count,
--     SUM(CASE WHEN risk_level = 'LOW' THEN 1 ELSE 0 END) AS low_risk_count
-- FROM flagged_transactions
-- GROUP BY DATE_FORMAT(transaction_date, '%Y-%m')
-- ORDER BY month DESC;

-- Query C: Top Suspicious Users by Triggered Fraud Rules
-- SELECT 
--     user_id,
--     COUNT(*) AS flagged_count,
--     AVG(risk_score) AS avg_risk,
--     SUM(transaction_amount) AS total_suspicious_volume
-- FROM flagged_transactions
-- GROUP BY user_id
-- ORDER BY flagged_count DESC, avg_risk DESC;
