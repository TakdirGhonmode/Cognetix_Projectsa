# Sales Performance Analytics Engine

An end-to-end Python-based **Sales Performance Analytics Engine** developed to analyze structured sales datasets (CSV / Excel), validate and clean raw data, store normalized records into a MySQL database, compute executive KPIs, perform trend & growth analysis, generate actionable business insights, render visual analytical charts, and export management-ready Excel and CSV reports.

---

## 📊 Architecture & Flow Chart

```
┌────────────────────────┐
│  Structured Dataset    │  <-- PRIMARY Data Ingestion (CSV / Excel)
└───────────┬────────────┘
            │
            ▼
┌────────────────────────┐
│     Data Loader        │  (data_loader.py)
└───────────┬────────────┘
            │
            ▼
┌────────────────────────┐
│   Data Validation      │  (cleaning.py)
└───────────┬────────────┘
            │
            ▼
┌────────────────────────┐
│     Data Cleaning      │  (cleaning.py)
└───────────┬────────────┘
            │
            ▼
┌────────────────────────┐
│    MySQL Database      │  (database.py, database_config.py, mysql_schema.sql)
└───────────┬────────────┘  <-- Post-Cleaning Data Storage (products & sales tables)
            │
            ▼
┌────────────────────────┐
│    KPI Calculation     │  (kpi_calculator.py)
└───────────┬────────────┘
            │
            ▼
┌────────────────────────┐
│    Trend Analysis      │  (trend_analysis.py)
└───────────┬────────────┘
            │
            ▼
┌────────────────────────┐
│  Insight Generation    │  (insight_generator.py)
└───────────┬────────────┘
            │
            ▼
┌────────────────────────┐
│     Visualization      │  (visualization.py)
└───────────┬────────────┘
            │
            ▼
┌────────────────────────┐
│   Report Generation    │  (report_generator.py)
└───────────┬────────────┘
            │
            ▼
┌────────────────────────┐
│  CSV / Excel Exports   │  (sales_report.xlsx, cleaned_sales_data.csv, etc.)
└────────────────────────┘
```

---

## 🛠️ Technology Stack & Required Libraries

- **Language**: Python 3.10+
- **Core Analytics & Data Processing**: `pandas`, `numpy`
- **Database Storage & ORM**: `SQLAlchemy`, `PyMySQL`, `MySQL`
- **Data Visualization**: `matplotlib`, `seaborn`
- **Excel Formatting & Export**: `openpyxl`
- **Optional Predictive Analytics**: `scikit-learn`

---

## 📂 Project Structure

```text
sales-analytics-engine/
│── database_config.py         # MySQL connection parameters & configuration
│── mysql_schema.sql           # MySQL database schema (products & sales tables)
│── database.py                # Database manager (schema init, data loading, SQL queries)
│── sample_data_generator.py   # (Optional) Synthetic multi-year sales dataset generator
│── data_loader.py             # Primary CSV/Excel data ingestion module
│── cleaning.py                # Data validation, cleaning, date formatting & deduplication
│── kpi_calculator.py          # Executive KPI calculator & MoM growth rate computation
│── trend_analysis.py          # Trend analysis, seasonal peak detection & ML forecasting
│── insight_generator.py       # Natural language business insight generation
│── visualization.py           # Chart renderer (Line, Bar, Donut charts -> PNG format)
│── report_generator.py        # Multi-tab formatted Excel & CSV report exporter
│── main.py                    # Main CLI pipeline controller
│── test_engine.py             # Automated unit test suite
│── requirements.txt           # Project dependencies file
└── README.md                  # Complete technical documentation
```

---

## 🗄️ MySQL Database Setup & Schema

The engine stores cleaned sales data in a relational MySQL database (`sales_analytics_db`) across two normalized tables:

### Database Schema (`mysql_schema.sql`)
1. **`products` Table** (Dimension Table):
   - `product_id` (VARCHAR(50), PRIMARY KEY)
   - `product_name` (VARCHAR(100))
   - `category` (VARCHAR(50))
   - `unit_price` (DECIMAL(10, 2))

2. **`sales` Table** (Fact Table):
   - `transaction_id` (VARCHAR(50), PRIMARY KEY)
   - `date` (DATE)
   - `product_id` (VARCHAR(50), FOREIGN KEY references `products(product_id)`)
   - `region` (VARCHAR(50))
   - `quantity` (INT)
   - `sales_amount` (DECIMAL(12, 2))
   - `discount_pct` (DECIMAL(5, 4))
   - `customer_segment` (VARCHAR(50))
   - `payment_method` (VARCHAR(50))

### Database Configuration (`database_config.py`)
Set environment variables or edit `database_config.py`:
```bash
export DB_HOST="localhost"
export DB_PORT=3306
export DB_USER="root"
export DB_PASSWORD="your_password"
export DB_NAME="sales_analytics_db"
```

---

## 🚀 Execution & Usage Guide

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Generate Sample Dataset (Optional)
If you do not have an existing dataset, generate `sales_data.csv` and `sales_data.xlsx`:
```bash
python sample_data_generator.py
```

### 3. Run Full Analytical Engine Pipeline
```bash
python main.py
```

#### CLI Command Options:
```bash
# Custom input CSV / Excel dataset
python main.py --input path/to/my_sales_data.xlsx

# Specify custom output directory
python main.py --output-dir custom_reports

# Automatically generate sample data & run engine
python main.py --generate-sample

# Skip MySQL database step (if local MySQL server is offline)
python main.py --skip-db
```

---

## 🧪 Automated Testing

Execute the unit test suite to verify module integrity:
```bash
python -m unittest test_engine.py
```

---

## 📈 Exported Deliverables

Upon completion, the engine produces management-ready deliverables in the `output/` directory:

1. **`sales_report.xlsx`**: Multi-tab formatted Excel workbook containing:
   - *Executive Summary*: KPI Cards & Key Insights
   - *Monthly Trends*: Month-by-month financial indicators & growth rates
   - *Regional & Product Stats*: Regional performance and category breakdown
   - *Cleaned Data*: Full normalized sales records
2. **`cleaned_sales_data.csv`**: Normalized raw dataset
3. **`kpi_summary.csv`**: Key metrics table
4. **`monthly_trends.csv`**: Monthly revenue & MoM growth % table
5. **`regional_performance.csv`**: Region-wise sales summary table
6. **`output/charts/`**: High-resolution PNG visual analytics:
   - `monthly_sales_trend.png` (Line Chart)
   - `regional_performance.png` (Bar Chart)
   - `revenue_by_category.png` (Donut Chart)
   - `customer_segment_matrix.png` (Bar Chart)
   - `top_products_bar.png` (Horizontal Bar Chart)
7. **`sales_report.html`**: Visual executive web dashboard
