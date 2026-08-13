import logging
import pandas as pd
import numpy as np

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

class DataCleaner:
    """
    Data Validation & Cleaning module.
    Ensures dataset integrity, standardized types, duplicate removal, 
    missing value imputation, and derived calculations.
    """

    @staticmethod
    def clean_data(df: pd.DataFrame) -> pd.DataFrame:
        """
        Executes end-to-end data cleaning workflow.
        """
        logger.info("Starting Data Validation and Cleaning...")
        cleaned_df = df.copy()

        # 1. Clean string column whitespace
        string_cols = cleaned_df.select_dtypes(include=['object']).columns
        for col in string_cols:
            cleaned_df[col] = cleaned_df[col].astype(str).str.strip()

        # Replace string 'nan' / 'None' with actual NaN
        cleaned_df.replace(["nan", "None", "NULL", ""], np.nan, inplace=True)

        # 2. Duplicate Removal
        initial_rows = len(cleaned_df)
        cleaned_df.drop_duplicates(inplace=True)
        dedup_rows = len(cleaned_df)
        if initial_rows > dedup_rows:
            logger.info(f"Removed {initial_rows - dedup_rows} duplicate record(s).")

        # 3. Date Parsing & Standardization
        if "Date" in cleaned_df.columns:
            cleaned_df["Date"] = pd.to_datetime(cleaned_df["Date"], errors='coerce')
            # Drop rows with unparseable dates
            missing_dates = cleaned_df["Date"].isna().sum()
            if missing_dates > 0:
                logger.warning(f"Dropping {missing_dates} rows with invalid dates.")
                cleaned_df = cleaned_df.dropna(subset=["Date"])

            # Extract temporal attributes for trend analysis
            cleaned_df["Year"] = cleaned_df["Date"].dt.year
            cleaned_df["Month"] = cleaned_df["Date"].dt.month
            cleaned_df["Month_Name"] = cleaned_df["Date"].dt.strftime("%b")
            cleaned_df["Year_Month"] = cleaned_df["Date"].dt.to_period("M").astype(str)
            cleaned_df["Quarter"] = "Q" + cleaned_df["Date"].dt.quarter.astype(str)
            cleaned_df["Day_Of_Week"] = cleaned_df["Date"].dt.day_name()

        # 4. Numeric Type Enforcement & Derived Field Computation
        numeric_fields = ["Quantity", "Unit_Price", "Sales_Amount", "Discount_Pct"]
        for field in numeric_fields:
            if field in cleaned_df.columns:
                cleaned_df[field] = pd.to_numeric(cleaned_df[field], errors='coerce')

        # Fill missing discounts with 0.0
        if "Discount_Pct" in cleaned_df.columns:
            cleaned_df["Discount_Pct"] = cleaned_df["Discount_Pct"].fillna(0.0)
        else:
            cleaned_df["Discount_Pct"] = 0.0

        # Enforce positive quantities
        if "Quantity" in cleaned_df.columns:
            cleaned_df = cleaned_df[cleaned_df["Quantity"] > 0]

        # Derive Product_ID if missing
        if "Product_ID" not in cleaned_df.columns and "Product" in cleaned_df.columns:
            logger.info("Generating Product_ID mapping...")
            unique_prods = cleaned_df["Product"].unique()
            prod_map = {name: f"PROD-{idx+101}" for idx, name in enumerate(unique_prods)}
            cleaned_df["Product_ID"] = cleaned_df["Product"].map(prod_map)

        # Derive Unit_Price if missing
        if "Unit_Price" not in cleaned_df.columns:
            if "Sales_Amount" in cleaned_df.columns and "Quantity" in cleaned_df.columns:
                cleaned_df["Unit_Price"] = (cleaned_df["Sales_Amount"] / cleaned_df["Quantity"]).round(2)
            else:
                cleaned_df["Unit_Price"] = 100.0

        # Derive Sales_Amount if missing or inaccurate
        if "Sales_Amount" not in cleaned_df.columns or cleaned_df["Sales_Amount"].isna().sum() > 0:
            logger.info("Recomputing missing or invalid Sales_Amount values...")
            calc_sales = cleaned_df["Quantity"] * cleaned_df["Unit_Price"] * (1 - cleaned_df["Discount_Pct"])
            cleaned_df["Sales_Amount"] = cleaned_df["Sales_Amount"].fillna(calc_sales).round(2)

        # Handle missing non-critical categorical columns
        if "Payment_Method" in cleaned_df.columns:
            cleaned_df["Payment_Method"] = cleaned_df["Payment_Method"].fillna("Unspecified")

        if "Customer_Segment" in cleaned_df.columns:
            cleaned_df["Customer_Segment"] = cleaned_df["Customer_Segment"].fillna("General")

        if "Region" in cleaned_df.columns:
            cleaned_df["Region"] = cleaned_df["Region"].fillna("Unknown")

        if "Category" in cleaned_df.columns:
            cleaned_df["Category"] = cleaned_df["Category"].fillna("General")

        # Guarantee unique Transaction_ID
        if "Transaction_ID" not in cleaned_df.columns or cleaned_df["Transaction_ID"].isna().any():
            cleaned_df["Transaction_ID"] = [f"TXN-{10000+i}" for i in range(1, len(cleaned_df) + 1)]

        logger.info(f"Data Cleaning completed cleanly. Final record count: {len(cleaned_df)} rows.")
        return cleaned_df
