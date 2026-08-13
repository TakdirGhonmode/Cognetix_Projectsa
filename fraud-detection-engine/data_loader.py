import os
import pandas as pd
import logging
from typing import Tuple

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("DataLoader")


class DataLoader:
    """
    Handles transaction data ingestion from CSV or Excel files.
    """

    def __init__(self, filepath: str):
        self.filepath = filepath

    def load_data(self) -> pd.DataFrame:
        """
        Loads raw dataset from CSV or Excel format into a pandas DataFrame.
        """
        if not os.path.exists(self.filepath):
            raise FileNotFoundError(f"Dataset file not found at path: '{self.filepath}'")

        file_ext = os.path.splitext(self.filepath)[1].lower()

        try:
            if file_ext == ".csv":
                df = pd.read_csv(self.filepath)
            elif file_ext in [".xlsx", ".xls"]:
                df = pd.read_excel(self.filepath)
            else:
                raise ValueError(f"Unsupported file format '{file_ext}'. Only CSV and Excel (.xlsx, .xls) are supported.")

            logger.info(f"Loaded {len(df)} records from '{self.filepath}'.")
            return df

        except Exception as e:
            logger.error(f"Error reading transaction dataset '{self.filepath}': {e}")
            raise e
