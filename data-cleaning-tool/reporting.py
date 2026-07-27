import pandas as pd


def generate_report(df):
    """
    Generate summary report of the cleaned dataset.
    """

    print("\nGenerating Summary Report...")

    summary = {}

    # -----------------------------
    # Total Records
    # -----------------------------
    summary["Total Records"] = len(df)

    # -----------------------------
    # Total Salary
    # -----------------------------
    if "salary" in df.columns:
        summary["Total Salary"] = df["salary"].sum()

    # -----------------------------
    # Average Salary
    # -----------------------------
    if "salary" in df.columns:
        summary["Average Salary"] = round(df["salary"].mean(), 2)

    # -----------------------------
    # Minimum Salary
    # -----------------------------
    if "salary" in df.columns:
        summary["Minimum Salary"] = df["salary"].min()

    # -----------------------------
    # Maximum Salary
    # -----------------------------
    if "salary" in df.columns:
        summary["Maximum Salary"] = df["salary"].max()

    # -----------------------------
    # Average Age
    # -----------------------------
    if "age" in df.columns:
        summary["Average Age"] = round(df["age"].mean(), 2)

    # -----------------------------
    # Department-wise Employee Count
    # -----------------------------
    department_count = (
        df.groupby("department")
        .size()
        .reset_index(name="Employee Count")
    )

    # -----------------------------
    # Convert Summary Dictionary to DataFrame
    # -----------------------------
    summary_df = pd.DataFrame(
        summary.items(),
        columns=["Metric", "Value"]
    )

    # -----------------------------
    # Export Summary Report to Excel
    # -----------------------------
    with pd.ExcelWriter("summary_report.xlsx") as writer:
        summary_df.to_excel(
            writer,
            sheet_name="Summary",
            index=False
        )

        department_count.to_excel(
            writer,
            sheet_name="Department Report",
            index=False
        )

    print("Summary Report Generated Successfully.")

    return summary_df