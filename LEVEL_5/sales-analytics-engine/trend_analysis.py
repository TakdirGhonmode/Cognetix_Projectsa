import logging
import pandas as pd
import numpy as np
from typing import Dict, Any

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

class TrendAnalyzer:
    """
    Trend & Growth Analysis module.
    Evaluates seasonal fluctuations, peak/declining sales months, 
    regional trajectory, and optional ML trend forecasting.
    """

    def __init__(self, df: pd.DataFrame, monthly_kpis: pd.DataFrame):
        self.df = df.copy()
        self.monthly_kpis = monthly_kpis.copy()

    def analyze_seasonality_and_peaks(self) -> Dict[str, Any]:
        """
        Identifies peak revenue month, highest growth month, and seasonal patterns.
        """
        if self.monthly_kpis.empty:
            return {}

        peak_revenue_row = self.monthly_kpis.loc[self.monthly_kpis["Monthly_Revenue"].idxmax()]
        lowest_revenue_row = self.monthly_kpis.loc[self.monthly_kpis["Monthly_Revenue"].idxmin()]
        
        # Exclude initial row for growth rate comparison if pct_change resulted in zero
        growth_subset = self.monthly_kpis.iloc[1:] if len(self.monthly_kpis) > 1 else self.monthly_kpis
        highest_growth_row = growth_subset.loc[growth_subset["MoM_Growth_Rate_Pct"].idxmax()] if not growth_subset.empty else peak_revenue_row

        # Average revenue by Month Name (seasonality)
        if "Month_Name" in self.df.columns:
            monthly_seasonal = self.df.groupby("Month_Name")["Sales_Amount"].sum().reset_index()
            peak_season_month = monthly_seasonal.loc[monthly_seasonal["Sales_Amount"].idxmax()]["Month_Name"]
        else:
            peak_season_month = "Q4"

        return {
            "Peak_Revenue_Month": str(peak_revenue_row["Year_Month"]),
            "Peak_Revenue_Amount": float(peak_revenue_row["Monthly_Revenue"]),
            "Lowest_Revenue_Month": str(lowest_revenue_row["Year_Month"]),
            "Lowest_Revenue_Amount": float(lowest_revenue_row["Monthly_Revenue"]),
            "Highest_Growth_Month": str(highest_growth_row["Year_Month"]),
            "Highest_Growth_Rate_Pct": float(highest_growth_row["MoM_Growth_Rate_Pct"]),
            "Peak_Seasonal_Month": str(peak_season_month)
        }

    def analyze_category_and_region_trends(self) -> Dict[str, Any]:
        """
        Identifies top and underperforming categories and regions.
        """
        region_sales = self.df.groupby("Region")["Sales_Amount"].sum()
        top_region = region_sales.idxmax()
        lowest_region = region_sales.idxmin()

        cat_sales = self.df.groupby("Category")["Sales_Amount"].sum()
        top_cat = cat_sales.idxmax()
        lowest_cat = cat_sales.idxmin()

        return {
            "Top_Performing_Region": str(top_region),
            "Top_Region_Revenue": float(region_sales[top_region]),
            "Underperforming_Region": str(lowest_region),
            "Underperforming_Region_Revenue": float(region_sales[lowest_region]),
            "Best_Category": str(top_cat),
            "Best_Category_Revenue": float(cat_sales[top_cat]),
            "Underperforming_Category": str(lowest_cat),
            "Underperforming_Category_Revenue": float(cat_sales[lowest_cat])
        }

    def predict_sales_trend(self, periods_ahead: int = 3) -> Dict[str, Any]:
        """
        OPTIONAL Advanced Analytics: Predicts future sales trend baseline using scikit-learn.
        """
        try:
            from sklearn.linear_model import LinearRegression
            
            if len(self.monthly_kpis) < 3:
                return {"status": "Insufficient data for ML trend forecasting"}

            # Prepare time series index
            X = np.arange(len(self.monthly_kpis)).reshape(-1, 1)
            y = self.monthly_kpis["Monthly_Revenue"].values

            model = LinearRegression()
            model.fit(X, y)

            # Predict next N months
            future_X = np.arange(len(self.monthly_kpis), len(self.monthly_kpis) + periods_ahead).reshape(-1, 1)
            predictions = model.predict(future_X)

            trend_direction = "Upward / Positive Growth" if model.coef_[0] > 0 else "Downward / Declining Trend"

            return {
                "status": "Success",
                "trend_direction": trend_direction,
                "monthly_slope_coef": round(float(model.coef_[0]), 2),
                "predicted_next_month_revenue": round(float(predictions[0]), 2),
                "predicted_3_month_avg": round(float(predictions.mean()), 2)
            }

        except ImportError:
            logger.info("scikit-learn optional module not loaded for trend prediction.")
            return {"status": "scikit-learn not installed (optional feature)"}
        except Exception as e:
            logger.warning(f"Trend prediction calculation skipped: {e}")
            return {"status": f"Error: {e}"}
