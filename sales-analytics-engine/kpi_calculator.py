import logging
import pandas as pd
import numpy as np
from typing import Dict, Any

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

class KPICalculator:
    """
    KPI Computation module.
    Calculates executive business metrics, period-over-period growth rates using pct_change(),
    regional performance, product contributions, and customer segment aggregations.
    """

    def __init__(self, df: pd.DataFrame):
        if df.empty:
            raise ValueError("Input DataFrame for KPICalculator is empty.")
        self.df = df.copy()

    def compute_overall_kpis(self) -> Dict[str, Any]:
        """
        Computes high-level executive summary metrics.
        """
        total_revenue = self.df["Sales_Amount"].sum()
        total_units = self.df["Quantity"].sum()
        total_transactions = len(self.df)
        avg_order_value = total_revenue / total_transactions if total_transactions > 0 else 0.0
        avg_unit_price = self.df["Unit_Price"].mean() if "Unit_Price" in self.df.columns else 0.0

        return {
            "Total_Sales_Revenue": round(float(total_revenue), 2),
            "Total_Units_Sold": int(total_units),
            "Total_Transactions": int(total_transactions),
            "Average_Order_Value": round(float(avg_order_value), 2),
            "Average_Unit_Price": round(float(avg_unit_price), 2)
        }

    def compute_monthly_growth(self) -> pd.DataFrame:
        """
        Computes monthly sales trends and growth rates using pandas pct_change().
        """
        monthly = self.df.groupby("Year_Month").agg(
            Monthly_Revenue=("Sales_Amount", "sum"),
            Monthly_Units=("Quantity", "sum"),
            Transaction_Count=("Sales_Amount", "count")
        ).reset_index()

        monthly["Monthly_Revenue"] = monthly["Monthly_Revenue"].round(2)
        
        # Calculate month-over-month growth rate % using pct_change()
        monthly["MoM_Growth_Rate_Pct"] = (monthly["Monthly_Revenue"].pct_change() * 100).round(2).fillna(0.0)

        return monthly

    def compute_regional_performance(self) -> pd.DataFrame:
        """
        Computes region-wise revenue, units, transaction counts, and contribution %.
        """
        regional = self.df.groupby("Region").agg(
            Total_Revenue=("Sales_Amount", "sum"),
            Total_Units=("Quantity", "sum"),
            Transaction_Count=("Sales_Amount", "count"),
            Average_Order_Value=("Sales_Amount", "mean")
        ).reset_index()

        total_rev = regional["Total_Revenue"].sum()
        regional["Revenue_Contribution_Pct"] = ((regional["Total_Revenue"] / total_rev) * 100).round(2)
        regional["Total_Revenue"] = regional["Total_Revenue"].round(2)
        regional["Average_Order_Value"] = regional["Average_Order_Value"].round(2)

        return regional.sort_values(by="Total_Revenue", ascending=False)

    def compute_product_performance(self) -> pd.DataFrame:
        """
        Computes product-wise revenue contribution %, total units, and average price.
        """
        prod_col = "Product" if "Product" in self.df.columns else "Product_ID"
        product_stats = self.df.groupby([prod_col, "Category"]).agg(
            Total_Revenue=("Sales_Amount", "sum"),
            Total_Units=("Quantity", "sum"),
            Avg_Unit_Price=("Unit_Price", "mean")
        ).reset_index()

        total_rev = product_stats["Total_Revenue"].sum()
        product_stats["Revenue_Contribution_Pct"] = ((product_stats["Total_Revenue"] / total_rev) * 100).round(2)
        product_stats["Total_Revenue"] = product_stats["Total_Revenue"].round(2)
        product_stats["Avg_Unit_Price"] = product_stats["Avg_Unit_Price"].round(2)

        return product_stats.sort_values(by="Total_Revenue", ascending=False)

    def compute_segment_performance(self) -> pd.DataFrame:
        """
        Computes performance aggregations by Customer Segment.
        """
        segment_stats = self.df.groupby("Customer_Segment").agg(
            Total_Revenue=("Sales_Amount", "sum"),
            Total_Units=("Quantity", "sum"),
            Transaction_Count=("Sales_Amount", "count"),
            Average_Order_Value=("Sales_Amount", "mean")
        ).reset_index()

        total_rev = segment_stats["Total_Revenue"].sum()
        segment_stats["Revenue_Contribution_Pct"] = ((segment_stats["Total_Revenue"] / total_rev) * 100).round(2)
        segment_stats["Total_Revenue"] = segment_stats["Total_Revenue"].round(2)
        segment_stats["Average_Order_Value"] = segment_stats["Average_Order_Value"].round(2)

        return segment_stats.sort_values(by="Total_Revenue", ascending=False)
