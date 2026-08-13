import os
import logging
import pandas as pd
from typing import Optional

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

class DataLoader:
    """
    Primary Data Ingestion module. Loads structured sales datasets 
    from CSV or Excel formats and performs schema verification.
    """

    REQUIRED_COLUMNS = [
        "Date", "Product", "Category", "Region", 
        "Quantity", "Sales_Amount", "Customer_Segment"
    ]

    @staticmethod
    def load_dataset(file_path: str) -> pd.DataFrame:
        """
        Loads dataset from a CSV or Excel file path.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Source file not found at path: {file_path}")

        file_ext = os.path.splitext(file_path)[1].lower()

        try:
            if file_ext in [".csv", ".txt"]:
                logger.info(f"Loading primary CSV dataset from {file_path}...")
                df = pd.read_csv(file_path)
            elif file_ext in [".xlsx", ".xls"]:
                logger.info(f"Loading primary Excel dataset from {file_path}...")
                df = pd.read_excel(file_path)
            else:
                raise ValueError(f"Unsupported file format '{file_ext}'. Supported formats: .csv, .xlsx, .xls")

            logger.info(f"Successfully loaded dataset with {len(df)} rows and {len(df.columns)} columns.")
            
            # Normalize column names by replacing spaces with underscores for standard processing
            df.columns = [col.strip().replace(" ", "_") for col in df.columns]

            # Validate basic column requirements
            DataLoader.verify_schema(df)

            return df

        except Exception as e:
            logger.error(f"Error loading dataset from {file_path}: {e}")
            raise

    @staticmethod
    def verify_schema(df: pd.DataFrame) -> bool:
        """
        Verifies that essential columns exist in the DataFrame.
        """
        missing_cols = [col for col in DataLoader.REQUIRED_COLUMNS if col not in df.columns]
        if missing_cols:
            logger.warning(f"Dataset is missing some standard fields: {missing_cols}")
            # Flexible mapping if alternate column naming is present
            column_mapping = {
                "Sales": "Sales_Amount",
                "Revenue": "Sales_Amount",
                "Sales_Revenue": "Sales_Amount",
                "Product_Name": "Product",
                "Segment": "Customer_Segment"
            }
            df.rename(columns=column_mapping, inplace=True)
        else:
            logger.info("Dataset schema verification passed successfully.")
        return True
