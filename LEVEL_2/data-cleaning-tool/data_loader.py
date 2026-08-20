import pandas as pd
import os


def load_dataset(file_path):
    """
    Load CSV or Excel dataset.
    """

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File '{file_path}' not found.")

    if file_path.endswith(".csv"):
        df = pd.read_csv(file_path)

    elif file_path.endswith(".xlsx"):
        df = pd.read_excel(file_path)

    else:
        raise ValueError("Unsupported file format! Please use CSV or Excel.")

    return df