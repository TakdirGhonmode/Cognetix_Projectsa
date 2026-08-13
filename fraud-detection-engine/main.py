import sys
import json
import argparse
import logging
import pandas as pd

from database import MySQLDatabaseManager
from data_loader import DataLoader
from validator import DataValidator
from rule_engine import RuleEngine
from risk_scorer import RiskScorer
from alert_manager import AlertManager
from logger import AuditLogger
from compliance_reporter import ComplianceReporter

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("FraudDetectionMain")


def load_config(config_path: str = "config.json") -> dict:
    """Loads configuration file or returns default settings."""
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.warning(f"Could not load config '{config_path}': {e}. Using internal defaults.")
        return {}


def run_pipeline(input_file: str, config_path: str = "config.json"):
    """
    Executes the full 9-step Fraud & Anomaly Detection Pipeline:
    1. Load Dataset
    2. Validate Data
    3. Apply Fraud Rules
    4. Detect Abnormal Patterns
    5. Calculate Risk Score
    6. Generate Alerts
    7. Maintain Audit Logs
    8. Store Flagged Transactions
    9. Generate Compliance Reports
    """
    print("\n" + "="*80)
    print("      PROJECT 3: FRAUD & ANOMALY DETECTION ENGINE - PIPELINE STARTING      ")
    print("="*80)

    # Load Configuration
    config = load_config(config_path)

    # Initialize Database Manager
    db_manager = MySQLDatabaseManager(config_path=config_path)
    db_manager.connect()
    db_manager.initialize_schema()

    # STEP 1: Load Dataset
    print("\n[STEP 1/9] Ingesting Transaction Dataset...")
    loader = DataLoader(input_file)
    raw_df = loader.load_data()

    # STEP 2: Validate Data
    print("\n[STEP 2/9] Running Data Validation Checks (validator.py)...")
    validator = DataValidator()
    clean_df, validation_report = validator.validate(raw_df)
    print(f" -> Validation Summary: {validation_report['valid_rows']} valid rows ready out of {validation_report['initial_rows']} initial rows.")

    # Save raw validated transactions to MySQL if connected
    if db_manager.is_connected:
        db_manager.insert_transactions(clean_df)

    # STEP 3 & STEP 4: Apply Fraud Rules & Detect Abnormal Patterns
    print("\n[STEP 3 & 4/9] Applying Fraud Rules & Detecting Abnormal Patterns...")
    rule_engine = RuleEngine(config)
    df_rules, rule_results = rule_engine.evaluate_all(clean_df)

    # STEP 5: Calculate Risk Score
    print("\n[STEP 5/9] Calculating Risk Scores & Classifying Severity (LOW, MEDIUM, HIGH)...")
    scorer = RiskScorer(config)
    df_evaluated = scorer.calculate_scores(df_rules, rule_results)

    # Filter flagged transactions (Is Flagged == True)
    flagged_df = df_evaluated[df_evaluated["Is Flagged"] == True].copy()

    # STEP 6: Generate Alerts
    print("\n[STEP 6/9] Generating Structured Console Alerts...")
    alert_mgr = AlertManager(config)
    alert_mgr.generate_console_alerts(flagged_df)

    # STEP 7: Maintain Audit Logs
    print("\n[STEP 7/9] Writing Audit Logs to 'audit_log.txt' & MySQL database...")
    audit_logger = AuditLogger(
        log_filepath=config.get("output_files", {}).get("audit_log", "audit_log.txt"),
        db_manager=db_manager
    )
    audit_logger.log_evaluation_results(df_evaluated)

    # STEP 8 & STEP 9: Store Flagged Transactions & Generate Compliance Reports
    print("\n[STEP 8 & 9/9] Storing Flagged Records & Generating Compliance Reports...")
    reporter = ComplianceReporter(
        report_filepath=config.get("output_files", {}).get("fraud_report", "fraud_report.csv"),
        db_manager=db_manager
    )
    reporter.save_flagged_transactions(df_evaluated)
    reporter.print_risk_summary(df_evaluated)

    # Display Monthly Fraud Summary Report
    monthly_summary = reporter.generate_monthly_summary(flagged_df)
    if not monthly_summary.empty:
        print("\n--- MONTHLY FRAUD SUMMARY REPORT ---")
        print(monthly_summary.to_string(index=False))
        print("------------------------------------\n")

    print("\n" + "="*80)
    print("      FRAUD & ANOMALY DETECTION ENGINE PIPELINE COMPLETED SUCCESSFULLY      ")
    print("="*80 + "\n")

    return df_evaluated, flagged_df, db_manager


def interactive_menu(config_path: str = "config.json"):
    """Interactive Compliance Review Menu."""
    db_manager = MySQLDatabaseManager(config_path=config_path)
    db_manager.connect()
    reporter = ComplianceReporter(db_manager=db_manager)

    while True:
        print("\n==================================================")
        print("      FRAUD ENGINE COMPLIANCE REVIEW MENU         ")
        print("==================================================")
        print(" 1. Run Detection Pipeline on CSV/Excel file")
        print(" 2. View All Flagged Transactions")
        print(" 3. Filter Flagged Transactions by Minimum Risk Score")
        print(" 4. View Monthly Fraud Summary Report")
        print(" 5. Exit")
        print("==================================================")

        choice = input("Select an option (1-5): ").strip()

        if choice == "1":
            file_path = input("Enter path to CSV/Excel file [default: sample_transactions.csv]: ").strip()
            if not file_path:
                file_path = "sample_transactions.csv"
            run_pipeline(file_path, config_path)

        elif choice == "2":
            flagged = reporter.filter_flagged_transactions(pd.DataFrame())
            if flagged.empty:
                print("\n[INFO] No flagged transactions found.")
            else:
                print("\n--- FLAGGED TRANSACTIONS ---")
                print(flagged.to_string(index=False))

        elif choice == "3":
            try:
                min_score = int(input("Enter minimum Risk Score threshold (e.g. 70 for HIGH risk): ").strip())
                flagged = reporter.filter_flagged_transactions(pd.DataFrame(), min_risk_score=min_score)
                if flagged.empty:
                    print(f"\n[INFO] No flagged transactions with Risk Score >= {min_score}.")
                else:
                    print(f"\n--- FLAGGED TRANSACTIONS (Risk Score >= {min_score}) ---")
                    print(flagged.to_string(index=False))
            except ValueError:
                print("Invalid input. Please enter a numerical score.")

        elif choice == "4":
            summary = reporter.generate_monthly_summary(pd.DataFrame())
            if summary.empty:
                print("\n[INFO] No monthly summary data available.")
            else:
                print("\n--- MONTHLY FRAUD SUMMARY REPORT ---")
                print(summary.to_string(index=False))

        elif choice == "5":
            print("\nExiting Fraud Detection Engine. Goodbye!")
            if db_manager.is_connected:
                db_manager.close()
            sys.exit(0)

        else:
            print("Invalid choice. Please select 1 to 5.")


def main():
    parser = argparse.ArgumentParser(description="Fraud & Anomaly Detection Engine")
    parser.add_argument("--input", "-i", type=str, default="sample_transactions.csv", help="Path to input dataset (CSV/Excel)")
    parser.add_argument("--config", "-c", type=str, default="config.json", help="Path to configuration file")
    parser.add_argument("--menu", "-m", action="store_true", help="Launch interactive compliance review menu")

    args = parser.parse_args()

    if args.menu:
        interactive_menu(args.config)
    else:
        run_pipeline(args.input, args.config)


if __name__ == "__main__":
    main()
