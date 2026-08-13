import os
import pandas as pd
import logging
from datetime import datetime
from typing import Dict, Any, Optional, Tuple
from database import MySQLDatabaseManager

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("ComplianceReporter")


class ComplianceReporter:
    """
    Handles flagged transaction storage and compliance reporting.
    - Exports flagged records to 'fraud_report.csv'
    - Persists flagged records to MySQL 'flagged_transactions' table
    - Provides filtering by date range or risk score threshold
    - Generates monthly fraud summary reports
    """

    def __init__(self, report_filepath: str = "fraud_report.csv", db_manager: Optional[MySQLDatabaseManager] = None):
        self.report_filepath = report_filepath
        self.db_manager = db_manager

    def save_flagged_transactions(self, df_evaluated: pd.DataFrame) -> pd.DataFrame:
        """
        Filters flagged transactions (Risk Score >= 30 or Is Flagged == True),
        exports to 'fraud_report.csv', and inserts into MySQL database.
        """
        flagged_df = df_evaluated[df_evaluated["Is Flagged"] == True].copy()

        if flagged_df.empty:
            logger.info("No flagged transactions to save.")
            return flagged_df

        # Format Triggered Rules for CSV storage
        export_df = flagged_df.copy()
        if "Triggered Rules" in export_df.columns:
            export_df["Triggered Rules"] = export_df["Triggered Rules"].apply(
                lambda x: ", ".join(x) if isinstance(x, list) else str(x)
            )

        # Drop temporary rule columns from CSV export for clean output
        rule_cols = [c for c in export_df.columns if c.startswith("rule_")]
        export_df = export_df.drop(columns=rule_cols, errors="ignore")

        # Export to CSV
        export_df.to_csv(self.report_filepath, index=False)
        logger.info(f"Compliance Report: Exported {len(export_df)} flagged transactions to '{self.report_filepath}'.")

        # Insert into MySQL database
        if self.db_manager and self.db_manager.is_connected:
            self.db_manager.insert_flagged_transactions(flagged_df)

        return export_df

    def filter_flagged_transactions(
        self,
        df_flagged: pd.DataFrame,
        min_risk_score: Optional[int] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Filters flagged transactions by minimum risk score or date range.
        Supports both in-memory DataFrame filtering and MySQL database query filtering.
        """
        # If MySQL connection is active, query directly from MySQL database
        if self.db_manager and self.db_manager.is_connected:
            return self.db_manager.fetch_flagged_transactions(
                min_risk_score=min_risk_score,
                date_from=date_from,
                date_to=date_to
            )

        # In-memory fallback
        filtered = df_flagged.copy()
        if filtered.empty:
            return filtered

        if min_risk_score is not None:
            filtered = filtered[filtered["Risk Score"] >= min_risk_score]

        if date_from:
            filtered = filtered[filtered["Date"] >= pd.to_datetime(date_from)]

        if date_to:
            filtered = filtered[filtered["Date"] <= pd.to_datetime(date_to)]

        return filtered.sort_values(by="Risk Score", ascending=False)

    def generate_monthly_summary(self, df_flagged: pd.DataFrame) -> pd.DataFrame:
        """
        Generates a monthly aggregated fraud summary report.
        """
        # If MySQL is connected, use DB query
        if self.db_manager and self.db_manager.is_connected:
            db_summary = self.db_manager.fetch_monthly_summary()
            if not db_summary.empty:
                return db_summary

        # In-memory pandas summary fallback
        if df_flagged.empty:
            return pd.DataFrame()

        df_calc = df_flagged.copy()
        df_calc['Month'] = pd.to_datetime(df_calc['Date']).dt.strftime('%Y-%m')

        summary = df_calc.groupby('Month').agg(
            total_flagged_transactions=('Transaction ID', 'count'),
            total_flagged_amount=('Transaction Amount', 'sum'),
            average_risk_score=('Risk Score', 'mean'),
            high_risk_count=('Risk Level', lambda x: (x == 'HIGH').sum()),
            medium_risk_count=('Risk Level', lambda x: (x == 'MEDIUM').sum()),
            low_risk_count=('Risk Level', lambda x: (x == 'LOW').sum())
        ).reset_index()

        summary['average_risk_score'] = summary['average_risk_score'].round(2)
        summary['total_flagged_amount'] = summary['total_flagged_amount'].round(2)

        return summary.sort_values(by='Month', ascending=False)

    def print_risk_summary(self, df_evaluated: pd.DataFrame):
        """
        Prints a clean risk score summary to console.
        """
        total = len(df_evaluated)
        flagged = len(df_evaluated[df_evaluated["Is Flagged"] == True])
        high = len(df_evaluated[df_evaluated["Risk Level"] == "HIGH"])
        med = len(df_evaluated[df_evaluated["Risk Level"] == "MEDIUM"])
        low = len(df_evaluated[df_evaluated["Risk Level"] == "LOW"])

        print("\n" + "="*70)
        print("                FRAUD ENGINE RISK SCORE SUMMARY                ")
        print("="*70)
        print(f"  Total Ingested Transactions : {total}")
        print(f"  Total Flagged Suspicious    : {flagged} ({flagged/total*100:.1f}%)" if total > 0 else "  Total Flagged: 0")
        print("-" * 70)
        print(f"  HIGH Risk Count   (70-100)  : {high}")
        print(f"  MEDIUM Risk Count (40-69)   : {med}")
        print(f"  LOW Risk Count    (0-39)    : {low}")
        print("="*70 + "\n")
