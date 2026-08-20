# Project 2 — Rule-Based Recommendation System (MySQL Engine)

An enterprise-grade, modular Python implementation of a **Rule-Based Recommendation System** integrated with a **MySQL database**, **data validation pipeline**, **decoupled scoring, ranking, and optimization engines**, **dual decision audit logging**, and **CSV/Excel report generation**.

---

## 🎯 Executive Overview & Purpose

The goal of this project is to simulate practical recommendation systems used in modern e-commerce and digital platforms. The system analyzes structured user behavior data (product views, purchase history, search queries, category preferences, interaction frequency, and activity recency) to generate personalized, ranked, deduplicated recommendations based on configurable business rules.

---

## 🏗️ Technical Architecture & Workflow

```text
                  +-----------------------------------+
                  |   MySQL Database / User Data      |
                  +-----------------------------------+
                                    |
                                    v (STEP 1 & 2: data_loader.py)
                  +-----------------------------------+
                  |    Data Validation Layer          |
                  |    (validator.py)                 |
                  +-----------------------------------+
                                    |
                                    v (STEP 3: Validated Data)
                  +-----------------------------------+
                  |    External Rule Engine           |
                  |    (rule_engine.py + config.json) |
                  +-----------------------------------+
                                    |
                                    v (STEP 4 & 5: Raw Rule Candidates)
                  +-----------------------------------+
                  |    Relevance Scoring Engine       |
                  |    (scorer.py)                    |
                  +-----------------------------------+
                                    |
                                    v (STEP 6: Scored Candidates)
                  +-----------------------------------+
                  |    Output Optimizer Engine        |
                  |    (optimizer.py)                 |
                  +-----------------------------------+
                                    |
                                    v (STEP 7: Deduplicated & Filtered)
                  +-----------------------------------+
                  |    Ranking Engine                 |
                  |    (ranking.py)                   |
                  +-----------------------------------+
                                    |
                                    v (STEP 8: Top-N Ranked List)
                  +-----------------------------------+
                  |    Dual Decision Logger           |
                  |    (logger.py)                    |
                  +-----------------------------------+
                 /                                     \
                v                                       v
   +--------------------------+           +---------------------------+
   | recommendations_log.txt  |           | MySQL decision_logs table |
   +--------------------------+           +---------------------------+
                                    |
                                    v (STEP 9 & 10: reports.py & main.py)
                  +-----------------------------------+
                  | CSV & Excel Reports + Terminal UI |
                  +-----------------------------------+
```

---

## 📁 Modular Project Structure

```text
rule-based-recommendation-system/
│
├── config.json              # External JSON configuration for business rules, weights, and scoring thresholds
├── database.py              # Pure MySQL connection manager, database creation, DDL execution, connection handling
├── models.py                # Database models & CRUD queries for users, products, behavior, recommendations, logs
├── data_loader.py           # Loads user behavior, product catalog, and user profiles from MySQL into DataFrames
├── validator.py             # Data validation layer: missing values, data types, timestamps, deduplication, cleaning
├── rule_engine.py           # Modular rule evaluation engine implementing all 5 business rules
├── scorer.py                # Calculates relevance scores (frequency, exponential recency decay, popularity, rule weights)
├── ranking.py               # Sorts recommendations by score, assigns numerical ranks, limits to top N
├── optimizer.py             # Deduplicates suggestions, filters purchased/out-of-stock/irrelevant items
├── logger.py                # Dual decision logger storing audit logs in recommendations_log.txt and MySQL decision_logs table
├── reports.py               # Exports recommendation results to CSV (recommendations_report.csv) and Excel (recommendations_report.xlsx)
├── main.py                  # CLI runner executing the 11-step recommendation workflow with formatted ASCII reports
├── test_recommendations.py  # Unit test suite covering DB connectivity, validation, rules, scoring, ranking, optimizer, logs, reports
├── recommendations_log.txt  # Text audit log file
├── requirements.txt         # Project dependencies (pandas, numpy, mysql-connector-python, openpyxl, pyyaml)
└── README.md                # Technical documentation, MySQL setup, schema, rule config, scoring math, execution, outputs
```

---

## 🗄️ Database Schema & DDL (`models.py`)

The system automatically initializes `recommendation_db` and the 5 relational tables upon startup:

```sql
CREATE DATABASE IF NOT EXISTS recommendation_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE recommendation_db;

-- 1. Users Table
CREATE TABLE IF NOT EXISTS users (
    user_id VARCHAR(50) PRIMARY KEY,
    username VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL,
    user_tier VARCHAR(20) NOT NULL DEFAULT 'Standard',
    total_spent DECIMAL(10, 2) DEFAULT 0.00,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- 2. Products Table
CREATE TABLE IF NOT EXISTS products (
    product_id VARCHAR(50) PRIMARY KEY,
    product_name VARCHAR(150) NOT NULL,
    category VARCHAR(100) NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    popularity_score FLOAT DEFAULT 0.0,
    stock_quantity INT DEFAULT 0,
    tags TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- 3. User Behavior Table
CREATE TABLE IF NOT EXISTS user_behavior (
    behavior_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL,
    product_id VARCHAR(50) NOT NULL,
    action_type ENUM('view', 'purchase', 'cart', 'search') NOT NULL,
    search_query VARCHAR(255) NULL,
    interaction_count INT DEFAULT 1,
    timestamp DATETIME NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- 4. Recommendations Table
CREATE TABLE IF NOT EXISTS recommendations (
    recommendation_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL,
    product_id VARCHAR(50) NOT NULL,
    score FLOAT NOT NULL,
    rank_order INT NOT NULL,
    applied_rule VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- 5. Decision Logs Table
CREATE TABLE IF NOT EXISTS decision_logs (
    log_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL,
    applied_rules_json TEXT NOT NULL,
    recommendations_json TEXT NOT NULL,
    relevance_scores_json TEXT NOT NULL,
    timestamp DATETIME NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
) ENGINE=InnoDB;
```

---

## 🔍 Data Validation Layer (`validator.py`)

Before rule processing, raw behavior data passes through `DataValidator`:
1. **Missing Value Filtering**: Drops records missing required fields (`user_id`, `product_id`, `action_type`, `timestamp`).
2. **Type Coercion**: Casts `user_id` and `product_id` to string, `action_type` to lowercase string, and `interaction_count` to positive integer.
3. **Timestamp Validation**: Converts timestamps to standardized `pd.Timestamp` format and rejects unparseable or extreme future dates.
4. **Duplicate Record Removal**: Eliminates exact duplicate interaction entries.
5. **Text Normalization**: Trims whitespace and lowercases search queries and product tags.

---

## ⚙️ Business Rules Engine (`rule_engine.py` & `config.json`)

The system evaluates 5 distinct business rules configured dynamically in `config.json`:

| Rule Name | Weight | Trigger Condition | Description |
| :--- | :---: | :--- | :--- |
| **`RULE_CO_PURCHASE`** | 3.5 | Past product purchase | Recommends complementary cross-sell products from mapping. |
| **`RULE_CATEGORY_TOP`** | 2.5 | Frequent category interaction | Recommends top-selling products in user's preferred category. |
| **`RULE_PREMIUM_CATALOG`**| 4.0 | Gold/Platinum tier or spend ≥ $500 | Recommends high-value luxury catalog products for VIP customers. |
| **`RULE_SEARCH_INTENT`** | 3.0 | Search query match | Matches search terms against product titles and catalog tags. |
| **`RULE_CART_ABANDONMENT`**| 3.2 | Cart items or repeated views without purchase | Re-engages items added to cart or viewed multiple times without checkout. |

### Rule Configuration Structure (`config.json`)
```json
{
  "rules": {
    "RULE_CO_PURCHASE": {
      "enabled": true,
      "weight": 3.5,
      "co_purchase_map": {
        "P101": ["P102", "P105"]
      }
    },
    "RULE_PREMIUM_CATALOG": {
      "enabled": true,
      "weight": 4.0,
      "spend_threshold": 500.0,
      "premium_tiers": ["Gold", "Platinum"],
      "premium_product_ids": ["P101", "P103", "P106", "P110"]
    }
  }
}
```

---

## 🧮 Mathematical Scoring Formula (`scorer.py`)

$$\text{Relevance Score} = (\text{Frequency} \times W_{\text{freq}}) + (e^{-\lambda \cdot \Delta t} \times W_{\text{recency}}) + (\text{Popularity Score} \times W_{\text{pop}}) + \sum (\text{Applied Rule Weights})$$

Where:
- $\text{Frequency}$: Total count of user interactions for the target product.
- $W_{\text{freq}} = 1.5$: Interaction frequency multiplier.
- $\Delta t$: Days elapsed since the most recent interaction.
- $\lambda = \frac{\ln(2)}{T_{1/2}}$: Exponential recency decay factor ($T_{1/2} = 7$ days by default).
- $\text{Popularity Score}$: Product catalog popularity score normalized on a 0–10 scale.
- $W_{\text{pop}} = 1.0$: Popularity multiplier.
- $\sum (\text{Applied Rule Weights})$: Accumulated weights of all business rules triggering for the candidate item.

---

## 🔝 Ranking & Output Optimization (`ranking.py`, `optimizer.py`)

- **Deduplication**: When multiple rules recommend the same product, candidate metadata is merged, accumulated rule weights are added as consensus bonus score, and applied rules are concatenated.
- **Filtering**:
  - Excludes already purchased products (`exclude_already_purchased: true`).
  - Excludes out-of-stock products (`stock_quantity <= 0`).
  - Excludes low relevance products (`min_score_threshold: 0.5`).
- **Ranking**: Sorts candidate products descending by relevance score, assigns `rank_order` positions (1..N), and caps output to Top N (default 5).

---

## 📝 Dual-Target Audit Logging (`logger.py`)

Recommendation decisions are recorded simultaneously in two locations:
1. **`recommendations_log.txt`**: Human-readable text audit file documenting user ID, timestamp, applied rules, rank positions, relevance scores, and matching business reasons.
2. **`decision_logs` (MySQL Table)**: Machine-readable database table storing user ID, JSON-encoded rules, JSON-encoded recommendations, JSON-encoded scores, and timestamps.

---

## 📊 Report Generation (`reports.py`)

1. **`recommendations_report.csv`**: Flat tabular CSV containing user ID, rank order, product ID, product name, category, price, relevance score, applied rule, and business reason.
2. **`recommendations_report.xlsx`**: Multi-sheet Excel workbook generated via `openpyxl` with:
   - **Recommendations Sheet**: Detailed tabular report.
   - **Executive Summary Sheet**: High-level key metrics (total recommendations, unique users processed, top recommended product, average relevance score).

---

## 🚀 Step-by-Step Setup & Execution Guide

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure MySQL Connection (`config.json`)
Set your local MySQL root password in `config.json`:
```json
{
  "database": {
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "password": "YOUR_MYSQL_PASSWORD",
    "database": "recommendation_db"
  }
}
```

### 3. Run Recommendation System
```bash
# Process recommendations across all users
python main.py

# Process recommendations for a specific user ID
python main.py --user U1001
```

### 4. Run Automated Unit Tests
```bash
python -m unittest -v test_recommendations.py
```

---

## 🖥️ Sample Execution Output

```text
======================================================================
      PROJECT 2 — RULE-BASED RECOMMENDATION SYSTEM (MySQL ENGINE)
======================================================================

[STEP 1] Initializing MySQL Database & Seeding Data...
[STEP 2] Loading Behavior, Products, and User Data...
[STEP 3] Validating and Cleaning Behavior Data...
[STEP 4] Loading Business Rules Configuration...

Processing recommendations for 5 user(s)...

--- Processing User: U1001 ---
  Top Recommendations for U1001:
    Rank #1 | Product: P102 (Wireless Noise-Canceling Headphones) | Score: 15.0414 | Rule: RULE_CO_PURCHASE, RULE_CATEGORY_TOP, RULE_SEARCH_INTENT, RULE_CART_ABANDONMENT
    Rank #2 | Product: P105 (Fast Charging Power Bank 20000mAh) | Score: 12.4691 | Rule: RULE_CO_PURCHASE, RULE_SEARCH_INTENT, RULE_CART_ABANDONMENT
    Rank #3 | Product: P106 (Premium Titanium Smart Watch) | Score: 6.4 | Rule: RULE_CATEGORY_TOP, RULE_PREMIUM_CATALOG
    Rank #4 | Product: P110 (All-Weather Insulated Jacket) | Score: 5.87 | Rule: RULE_PREMIUM_CATALOG
    Rank #5 | Product: P103 (Smart Espresso Coffee Machine) | Score: 5.82 | Rule: RULE_PREMIUM_CATALOG

[STEP 10] Generating Recommendation Reports (CSV & Excel)...
  -> CSV Report Saved:   recommendations_report.csv
  -> Excel Report Saved: recommendations_report.xlsx

======================================================================
      RECOMMENDATION WORKFLOW COMPLETED SUCCESSFULLY!
======================================================================
```
