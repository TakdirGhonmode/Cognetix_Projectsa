import json
import logging
import os
import pandas as pd

logger = logging.getLogger("ReportGenerator")


class ReportGenerator:
    def __init__(self, config_path="config.json"):
        self.config_path = config_path
        self.rep_config = self._load_report_config()

    def _load_report_config(self):
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
            return config.get("reports", {})
        except Exception:
            return {}

    def export_reports(self, all_recommendations: list, products_df: pd.DataFrame = None) -> tuple:
        """
        Export final recommendation output to CSV and Excel (.xlsx) files.
        Returns tuple of file paths: (csv_path, excel_path)
        """
        csv_path = self.rep_config.get("csv_report_path", "recommendations_report.csv")
        excel_path = self.rep_config.get("excel_report_path", "recommendations_report.xlsx")

        if not all_recommendations:
            logger.warning("No recommendations available to generate report.")
            df = pd.DataFrame(columns=["user_id", "rank_order", "product_id", "product_name", "category", "price", "relevance_score", "applied_rule", "reason"])
        else:
            df = pd.DataFrame(all_recommendations)

            # Enrich with product catalog details if available
            if products_df is not None and not products_df.empty:
                df = df.merge(
                    products_df[["product_id", "product_name", "category", "price"]],
                    on="product_id",
                    how="left"
                )

            preferred_cols = ["user_id", "rank_order", "product_id", "product_name", "category", "price", "relevance_score", "applied_rule", "reason"]
            available_cols = [c for c in preferred_cols if c in df.columns]
            df = df[available_cols]

        # 1. Export to CSV
        df.to_csv(csv_path, index=False, encoding="utf-8")
        logger.info(f"Successfully exported recommendation report to CSV: '{csv_path}'")

        # 2. Export to Excel (.xlsx) using openpyxl
        try:
            with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
                df.to_excel(writer, sheet_name="Recommendations", index=False)

                # Add summary sheet
                if not df.empty:
                    summary_df = pd.DataFrame([
                        {"Metric": "Total Recommendations", "Value": len(df)},
                        {"Metric": "Unique Users Processed", "Value": df["user_id"].nunique()},
                        {"Metric": "Top Recommended Product", "Value": df["product_id"].mode().iloc[0] if not df["product_id"].empty else "N/A"},
                        {"Metric": "Average Relevance Score", "Value": round(df["relevance_score"].mean(), 4)}
                    ])
                    summary_df.to_excel(writer, sheet_name="Executive Summary", index=False)

            logger.info(f"Successfully exported recommendation report to Excel: '{excel_path}'")
        except Exception as e:
            logger.error(f"Error generating Excel report via openpyxl: {e}")

        return csv_path, excel_path
