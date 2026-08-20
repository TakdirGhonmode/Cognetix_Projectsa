import pandas as pd
import numpy as np
import logging
from typing import Tuple, Dict, Any

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("DataValidator")


class DataValidator:
    """
    Dedicated Data Validation Module.
    Performs comprehensive data quality checks on transaction datasets:
    - Required fields check
    - Missing values detection & handling
    - Data type verification
    - Date format parsing & validation
    - Duplicate Transaction ID detection
    """

    REQUIRED_FIELDS = [
        "Transaction ID",
        "User ID",
        "Transaction Amount",
        "Date",
        "Location",
        "Payment Method"
    ]

    def __init__(self, required_fields: list = None):
        self.required_fields = required_fields or self.REQUIRED_FIELDS

    def validate(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Validates the transaction DataFrame.
        Returns:
            clean_df: Cleaned and validated DataFrame ready for rule processing.
            validation_report: Summary dictionary detailing dropped/invalid records.
        """
        report = {
            "initial_rows": len(df),
            "missing_required_fields": [],
            "missing_value_rows_dropped": 0,
            "invalid_amount_rows_dropped": 0,
            "invalid_date_rows_dropped": 0,
            "duplicate_id_rows_dropped": 0,
            "valid_rows": 0
        }

        # 1. Verify Required Fields Exist
        missing_cols = [col for col in self.required_fields if col not in df.columns]
        if missing_cols:
            report["missing_required_fields"] = missing_cols
            raise KeyError(f"Dataset is missing required columns: {missing_cols}")

        clean_df = df.copy()

        # 2. Check and Handle Missing/Null Values in Required Columns
        null_mask = clean_df[self.required_fields].isnull().any(axis=1)
        dropped_null_count = null_mask.sum()
        if dropped_null_count > 0:
            logger.warning(f"Validation Warning: Dropping {dropped_null_count} rows with missing required values.")
            clean_df = clean_df[~null_mask].copy()
            report["missing_value_rows_dropped"] = int(dropped_null_count)

        # 3. Validate Data Types: Transaction Amount must be numeric and > 0
        clean_df['Transaction Amount'] = pd.to_numeric(clean_df['Transaction Amount'], errors='coerce')
        invalid_amount_mask = clean_df['Transaction Amount'].isnull() | (clean_df['Transaction Amount'] <= 0)
        dropped_amount_count = invalid_amount_mask.sum()
        if dropped_amount_count > 0:
            logger.warning(f"Validation Warning: Dropping {dropped_amount_count} rows with invalid/non-positive Transaction Amount.")
            clean_df = clean_df[~invalid_amount_mask].copy()
            report["invalid_amount_rows_dropped"] = int(dropped_amount_count)

        # 4. Validate & Parse Date Formats
        clean_df['Date'] = pd.to_datetime(clean_df['Date'], errors='coerce')
        invalid_date_mask = clean_df['Date'].isnull()
        dropped_date_count = invalid_date_mask.sum()
        if dropped_date_count > 0:
            logger.warning(f"Validation Warning: Dropping {dropped_date_count} rows with unparseable date formats.")
            clean_df = clean_df[~invalid_date_mask].copy()
            report["invalid_date_rows_dropped"] = int(dropped_date_count)

        # 5. Check & Handle Duplicate Transaction IDs
        duplicate_mask = clean_df.duplicated(subset=['Transaction ID'], keep='first')
        dropped_dup_count = duplicate_mask.sum()
        if dropped_dup_count > 0:
            logger.warning(f"Validation Warning: Dropping {dropped_dup_count} duplicate Transaction ID records.")
            clean_df = clean_df[~duplicate_mask].copy()
            report["duplicate_id_rows_dropped"] = int(dropped_dup_count)

        # Ensure text fields are clean strings
        clean_df['Transaction ID'] = clean_df['Transaction ID'].astype(str).str.strip()
        clean_df['User ID'] = clean_df['User ID'].astype(str).str.strip()
        clean_df['Location'] = clean_df['Location'].astype(str).str.strip()
        clean_df['Payment Method'] = clean_df['Payment Method'].astype(str).str.strip()

        # Sort by Date for velocity & time-series analysis
        clean_df = clean_df.sort_values(by='Date').reset_index(drop=True)

        report["valid_rows"] = len(clean_df)
        logger.info(f"Data Validation Passed: {len(clean_df)} / {len(df)} records validated successfully.")
        return clean_df, report
