
# Business Data Cleaning & Reporting Tool

## Project Overview

The Business Data Cleaning & Reporting Tool is a Python-based application that cleans raw business datasets and generates summary reports. It helps identify missing values, duplicate records, invalid data, and applies cleaning rules to produce a clean dataset suitable for business analysis.

## Features

- Import CSV and Excel files
- Detect missing values
- Remove duplicate records
- Standardize column names
- Trim extra whitespace
- Convert data types
- Fill missing values
- Remove invalid records
- Generate summary statistics
- Export cleaned dataset
- Export summary report

## Technologies Used

- Python 3.10+
- Pandas
- OpenPyXL

## Project Structure

```
data-cleaning-tool/
│── data_loader.py
│── cleaning_rules.py
│── reporting.py
│── main.py
│── raw_data.csv
│── cleaned_data.csv
│── summary_report.xlsx
│── README.md
```

## Dataset

The project uses a business dataset containing employee information such as:

- Employee ID
- Employee Name
- Department
- Salary
- Age
- Performance Rating

## How to Run

### 1. Install Dependencies

```bash
pip install pandas openpyxl
```

### 2. Run the Project

```bash
python main.py
```

### 3. Enter Dataset Path

Example:

```
raw_data.csv
```

## Output Files

### cleaned_data.csv

Contains the cleaned dataset after removing duplicates, filling missing values, and correcting formatting.

### summary_report.xlsx

Contains summary statistics including:

- Total Records
- Average Salary
- Minimum Salary
- Maximum Salary
- Department-wise Employee Count

## Project Workflow

1. Load CSV or Excel dataset.
2. Validate the dataset.
3. Detect missing values and duplicate records.
4. Apply data cleaning rules.
5. Generate summary metrics.
6. Export cleaned dataset.
7. Export summary report.

## Sample Output

```
Loading dataset...
Checking missing values...
Removing duplicate records...
Cleaning completed successfully.
Generating summary report...
Files exported successfully.
```

## Learning Outcomes

This project demonstrates:

- File Handling
- Data Cleaning
- Data Validation
- Exception Handling
- Pandas DataFrame Operations
- Business Data Analysis
- Report Generation

## Author

**Takdir Ghonmode**

Internship Project – Python Level 2

---
