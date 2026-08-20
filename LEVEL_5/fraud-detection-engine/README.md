# Project 3: Fraud & Anomaly Detection Engine

A production-ready, modular Python-based Fraud & Anomaly Detection Engine designed to identify suspicious financial and e-commerce transactions using predefined rule-based validation logic, separate data validation, 3-tier risk scoring, real-time alert generation, audit logging, MySQL database storage, and compliance tracking.

---

## 📌 Project Architecture & Module Overview

The application follows a clean, modular structure suitable for enterprise fraud monitoring systems and internship submission:

```
fraud-detection-engine/
│── database.py            # MySQL database connection, schema setup & query execution
│── data_loader.py         # Transaction dataset ingestion (CSV / Excel)
│── validator.py           # Data quality checks (missing fields, dates, types, duplicates)
│── rule_engine.py         # Modular rule engine (6 fraud detection rules)
│── risk_scorer.py         # Weighted risk scoring engine (LOW, MEDIUM, HIGH)
│── alert_manager.py       # ANSI colorized real-time console alerts
│── logger.py              # Compliance audit trial logger (audit_log.txt & MySQL)
│── compliance_reporter.py # Flagged transaction exporter (fraud_report.csv & MySQL)
│── main.py                # Pipeline orchestrator & Interactive Compliance Menu
│── config.json            # Central configuration file (DB credentials, thresholds, weights)
│── schema.sql             # Ready-made MySQL database creation script
│── sample_transactions.csv# Synthetic test dataset with embedded fraud vectors
│── audit_log.txt          # Generated persistent audit log file
│── fraud_report.csv       # Generated flagged transaction report CSV
└── README.md              # Technical documentation & setup guide
```

---

## 🔄 End-to-End Application Workflow

```
┌─────────────────┐     ┌──────────────────┐     ┌────────────────────┐
│  Load Dataset   │ ──> │  Validate Data   │ ──> │ Apply Fraud Rules  │
│ (data_loader.py)│     │  (validator.py)  │     │  (rule_engine.py)  │
└─────────────────┘     └──────────────────┘     └────────────────────┘
                                                           │
                                                           ▼
┌─────────────────┐     ┌──────────────────┐     ┌────────────────────┐
│ Generate Alerts │ <── │ Calculate Risk   │ <── │ Detect Abnormal    │
│(alert_manager.py│     │ (risk_scorer.py) │     │ Patterns (Rules)   │
└─────────────────┘     └──────────────────┘     └────────────────────┘
        │
        ▼
┌─────────────────┐     ┌──────────────────┐     ┌────────────────────┐
│ Maintain Audit  │ ──> │  Store Flagged   │ ──> │Generate Compliance │
│   (logger.py)   │     │ (database.py/csv)│     │ (reporter.py)      │
└─────────────────┘     └──────────────────┘     └────────────────────┘
```

---

## 🛡️ Predefined Fraud Detection Rules (`rule_engine.py`)

1. **`HighAmountRule`**: Flags transactions exceeding maximum amount threshold (e.g. > $5,000.00).
2. **`RapidVelocityRule`**: Flags high-frequency activity (e.g. > 3 transactions for same user within 15 minutes).
3. **`GeographicalAnomalyRule`**: Flags transactions from unusual/blacklisted locations or rapid location jumps.
4. **`FailedPaymentRule`**: Flags repeated failed payment attempts prior to transaction execution.
5. **`BlacklistRule`**: Flags transactions matching blacklisted User IDs or payment methods.
6. **`SpikeDetectionRule`**: Flags sudden transaction value spikes compared to user's historical average (Z-score anomaly).

---

## 📊 3-Tier Risk Classification (`risk_scorer.py`)

Risk scores are calculated dynamically from triggered rule weights (0–100) and categorized into three risk tiers:

| Risk Level | Score Range | Description |
| :--- | :--- | :--- |
| **`LOW`** | **`0 – 39`** | Low suspicion, normal transaction profile |
| **`MEDIUM`** | **`40 – 69`** | Moderate suspicion, requires secondary review |
| **`HIGH`** | **`70 – 100`** | High suspicion, potential fraud, immediate alert |

---

## 🚀 Setup & Installation Instructions

### 1. Prerequisite Requirements
- Python **3.10** or higher
- MySQL Server (Local or Remote)

Verify Python installation:
```bash
python --version
```

### 2. Install Required Python Libraries
```bash
pip install pandas numpy mysql-connector-python
```
*(Optional fallback driver: `pip install pymysql`)*

---

## 🗄️ MySQL Database Setup (`schema.sql` & `config.json`)

### Step 1: Execute `schema.sql` on your MySQL Server
Run the ready-made SQL script in MySQL Workbench, phpMyAdmin, or MySQL CLI:
```bash
mysql -u root -p < schema.sql
```
This automatically creates:
- Database: `fraud_detection_db`
- Table 1: `transactions`
- Table 2: `flagged_transactions`
- Table 3: `audit_logs`

### Step 2: Configure MySQL Credentials in `config.json`
Edit `config.json` to match your local MySQL credentials:
```json
{
  "database": {
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "password": "YOUR_MYSQL_PASSWORD",
    "database": "fraud_detection_db"
  }
}
```

---

## 🏃 Running the Application

### Option A: Run Detection Pipeline via Command Line
Run detection pipeline on the provided `sample_transactions.csv` dataset:
```bash
python main.py --input sample_transactions.csv
```

Run on a custom CSV or Excel file:
```bash
python main.py --input path/to/your_transactions.csv
```

### Option B: Launch Interactive Compliance Review Menu
```bash
python main.py --menu
```
The interactive menu allows compliance officers to:
1. Ingest new transaction files
2. View all flagged transactions
3. Filter flagged records by minimum risk score
4. Generate monthly fraud summary reports

---

## 📁 Generated Outputs

1. **Flagged Transaction Report (`fraud_report.csv`)**: Contains all transactions flagged with Risk Score, Risk Level (`LOW`, `MEDIUM`, `HIGH`), and list of triggered rules.
2. **Audit Log File (`audit_log.txt`)**: Persistent timestamped log of every transaction evaluation step.
3. **Console Alerts**: Real-time ANSI color-coded suspicious activity alerts printed directly to the terminal.
4. **MySQL Database Tables**:
   - `transactions`: Stores raw validated dataset records.
   - `flagged_transactions`: Stores flagged suspicious records for compliance auditing.
   - `audit_logs`: Stores transactional audit logs.
