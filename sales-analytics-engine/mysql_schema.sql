-- Sales Performance Analytics Engine Database Schema
-- Database Creation
CREATE DATABASE IF NOT EXISTS sales_analytics_db;
USE sales_analytics_db;

-- Products Dimension Table
CREATE TABLE IF NOT EXISTS products (
    product_id VARCHAR(50) PRIMARY KEY,
    product_name VARCHAR(100) NOT NULL,
    category VARCHAR(50) NOT NULL,
    unit_price DECIMAL(10, 2) NOT NULL
);

-- Sales Fact Table
CREATE TABLE IF NOT EXISTS sales (
    transaction_id VARCHAR(50) PRIMARY KEY,
    date DATE NOT NULL,
    product_id VARCHAR(50) NOT NULL,
    region VARCHAR(50) NOT NULL,
    quantity INT NOT NULL,
    sales_amount DECIMAL(12, 2) NOT NULL,
    discount_pct DECIMAL(5, 4) DEFAULT 0.0000,
    customer_segment VARCHAR(50) NOT NULL,
    payment_method VARCHAR(50),
    FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE CASCADE
);

-- Analytical Performance Indexes
CREATE INDEX idx_sales_date ON sales(date);
CREATE INDEX idx_sales_region ON sales(region);
CREATE INDEX idx_sales_customer_segment ON sales(customer_segment);
