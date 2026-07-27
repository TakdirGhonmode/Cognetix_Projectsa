import pandas as pd
import numpy as np


def clean_data(df):
    """
    Clean the business dataset.
    """

    print("\nChecking missing values...")
    print(df.isnull().sum())

    # -----------------------------
    # Standardize Column Names
    # -----------------------------
    df.columns = (
        df.columns.str.strip()
        .str.lower()
        .str.replace(" ", "_")
    )

    # -----------------------------
    # Remove Extra Spaces
    # -----------------------------
    text_columns = df.select_dtypes(include="object").columns

    for column in text_columns:
        df[column] = df[column].astype(str).str.strip()

    # -----------------------------
    # Replace Empty Strings with NaN
    # -----------------------------
    df.replace(r'^\s*$', np.nan, regex=True, inplace=True)

    # -----------------------------
    # Convert Data Types
    # -----------------------------
    df["salary"] = pd.to_numeric(df["salary"], errors="coerce")
    df["age"] = pd.to_numeric(df["age"], errors="coerce")
    df["performance_rating"] = pd.to_numeric(
        df["performance_rating"],
        errors="coerce"
    )

    # -----------------------------
    # Fill Missing Values
    # -----------------------------
    df["salary"] = df["salary"].fillna(df["salary"].mean())

    df["performance_rating"] = df["performance_rating"].fillna(
        df["performance_rating"].mean()
    )

    df["employee_name"] = df["employee_name"].fillna("Unknown")

    # -----------------------------
    # Remove Duplicate Records
    # -----------------------------
    duplicate_count = df.duplicated().sum()

    print(f"\nDuplicate Records Found : {duplicate_count}")

    df = df.drop_duplicates()

    # -----------------------------
    # Remove Invalid Salary
    # -----------------------------
    invalid_salary = df[df["salary"] < 0]

    if not invalid_salary.empty:
        print(f"\nInvalid Salary Records Removed : {len(invalid_salary)}")

    df = df[df["salary"] >= 0]

    # -----------------------------
    # Remove Invalid Age
    # -----------------------------
    invalid_age = df[(df["age"] < 18) | (df["age"] > 65)]

    if not invalid_age.empty:
        print(f"\nInvalid Age Records Removed : {len(invalid_age)}")

    df = df[(df["age"] >= 18) & (df["age"] <= 65)]

    # -----------------------------
    # Missing Values After Cleaning
    # -----------------------------
    print("\nMissing Values After Cleaning:")
    print(df.isnull().sum())

    print("\nCleaning Completed Successfully.")

    return df