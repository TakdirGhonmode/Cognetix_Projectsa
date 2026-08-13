import logging
from typing import Dict, Any, List
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

class InsightGenerator:
    """
    Business Insight Generation module.
    Translates raw numbers and aggregations into clear executive-level business 
    insights and strategic management recommendations.
    """

    @staticmethod
    def generate_insights(
        kpis: Dict[str, Any],
        trends: Dict[str, Any],
        cat_region_trends: Dict[str, Any],
        top_products: pd.DataFrame,
        ml_trends: Dict[str, Any]
    ) -> List[str]:
        """
        Generates a collection of structured, actionable executive insights.
        """
        insights = []

        # 1. High Level Executive Overview
        insights.append(
            f"EXECUTIVE SUMMARY: Total revenue generated stands at ${kpis['Total_Sales_Revenue']:,.2f} "
            f"across {kpis['Total_Transactions']:,} transactions, with an Average Order Value (AOV) of ${kpis['Average_Order_Value']:,.2f}."
        )

        # 2. Product Category Performance
        if "Best_Category" in cat_region_trends:
            insights.append(
                f"CATEGORY LEADERSHIP: '{cat_region_trends['Best_Category']}' is the best-performing product category, "
                f"generating ${cat_region_trends['Best_Category_Revenue']:,.2f} in revenue. "
                f"Conversely, '{cat_region_trends['Underperforming_Category']}' represents the smallest category share (${cat_region_trends['Underperforming_Category_Revenue']:,.2f})."
            )

        # 3. Top Performing Individual Product
        if not top_products.empty:
            top_prod_name = top_products.iloc[0]["Product"] if "Product" in top_products.columns else top_products.iloc[0]["Product_ID"]
            top_prod_rev = top_products.iloc[0]["Total_Revenue"]
            top_prod_share = top_products.iloc[0]["Revenue_Contribution_Pct"]
            insights.append(
                f"FLAGSHIP PRODUCT: '{top_prod_name}' is the single largest revenue driver, generating "
                f"${top_prod_rev:,.2f} ({top_prod_share:.1f}% of overall revenue)."
            )

        # 4. Seasonal Fluctuation & Peak Sales Month
        if "Peak_Revenue_Month" in trends:
            insights.append(
                f"SEASONALITY & PEAKS: Peak revenue occurred in {trends['Peak_Revenue_Month']} (${trends['Peak_Revenue_Amount']:,.2f}). "
                f"Highest month-over-month growth spike was observed in {trends['Highest_Growth_Month']} (+{trends['Highest_Growth_Rate_Pct']:.1f}% MoM)."
            )

        # 5. Regional Trajectory
        if "Top_Performing_Region" in cat_region_trends:
            insights.append(
                f"GEOGRAPHIC DISTRIBUTION: '{cat_region_trends['Top_Performing_Region']}' leads regional sales with "
                f"${cat_region_trends['Top_Region_Revenue']:,.2f}. Strategic sales push and resource allocation is recommended for "
                f"underperforming territory '{cat_region_trends['Underperforming_Region']}' (${cat_region_trends['Underperforming_Region_Revenue']:,.2f})."
            )

        # 6. Predictive Trend Insight (Optional)
        if ml_trends.get("status") == "Success":
            insights.append(
                f"FORECASTING: Sales velocity shows a {ml_trends['trend_direction']} "
                f"(Slope: ${ml_trends['monthly_slope_coef']:,.2f}/month). Projected revenue for next month is ~${ml_trends['predicted_next_month_revenue']:,.2f}."
            )

        # 7. Actionable Recommendations
        insights.append(
            "MANAGEMENT ACTION PLAN: 1) Expand inventory and marketing budget for flagship category items. "
            "2) Introduce regional promos in low-performing territories. 3) Capitalize on seasonal peak months with targeted customer campaigns."
        )

        return insights
