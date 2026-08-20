import os
import logging
import pandas as pd
import matplotlib
matplotlib.use("Agg")  # Non-interactive backend for headless execution
import matplotlib.pyplot as plt
import seaborn as sns

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

class Visualizer:
    """
    Visualization module.
    Renders publication-quality charts (line, bar, pie/donut) saved as high-resolution PNG images.
    """

    def __init__(self, output_dir: str = "output/charts"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        # Apply modern Seaborn theme
        sns.set_theme(style="whitegrid", palette="muted")
        plt.rcParams.update({"font.family": "sans-serif", "font.size": 10})

    def plot_monthly_sales_trend(self, monthly_df: pd.DataFrame) -> str:
        """
        Renders Line Chart for Monthly Sales Trend & MoM Growth.
        """
        fig, ax1 = plt.subplots(figsize=(10, 5))

        color = '#1f77b4'
        ax1.set_xlabel("Year-Month", fontweight="bold")
        ax1.set_ylabel("Monthly Revenue ($)", color=color, fontweight="bold")
        line1 = ax1.plot(
            monthly_df["Year_Month"], monthly_df["Monthly_Revenue"], 
            marker="o", linewidth=2.5, color=color, label="Revenue ($)"
        )
        ax1.tick_params(axis="y", labelcolor=color)
        plt.xticks(rotation=45, ha="right")

        # Second axis for growth rate %
        ax2 = ax1.twinx()
        color = '#ff7f0e'
        ax2.set_ylabel("MoM Growth Rate (%)", color=color, fontweight="bold")
        line2 = ax2.plot(
            monthly_df["Year_Month"], monthly_df["MoM_Growth_Rate_Pct"], 
            marker="s", linestyle="--", linewidth=1.5, color=color, label="MoM Growth %"
        )
        ax2.tick_params(axis="y", labelcolor=color)

        plt.title("Monthly Sales Revenue & Growth Rate Trend", fontsize=14, fontweight="bold", pad=15)
        fig.tight_layout()

        file_path = os.path.join(self.output_dir, "monthly_sales_trend.png")
        plt.savefig(file_path, dpi=300, bbox_inches="tight")
        plt.close()
        logger.info(f"Saved visualization: {file_path}")
        return file_path

    def plot_regional_performance(self, regional_df: pd.DataFrame) -> str:
        """
        Renders Bar Chart comparing Region-wise Revenue and Units Sold.
        """
        fig, ax = plt.subplots(figsize=(9, 5))

        sns.barplot(
            data=regional_df, x="Region", y="Total_Revenue", 
            palette="viridis", ax=ax
        )

        plt.title("Region-wise Sales Revenue Comparison", fontsize=14, fontweight="bold", pad=15)
        plt.xlabel("Region", fontweight="bold")
        plt.ylabel("Total Revenue ($)", fontweight="bold")

        # Add data labels
        for p in ax.patches:
            height = p.get_height()
            ax.annotate(
                f"${height:,.0f}",
                (p.get_x() + p.get_width() / 2., height),
                ha='center', va='bottom', fontsize=9, xytext=(0, 3),
                textcoords='offset points'
            )

        file_path = os.path.join(self.output_dir, "regional_performance.png")
        plt.savefig(file_path, dpi=300, bbox_inches="tight")
        plt.close()
        logger.info(f"Saved visualization: {file_path}")
        return file_path

    def plot_revenue_by_category(self, product_df: pd.DataFrame) -> str:
        """
        Renders Donut/Pie Chart for Revenue Distribution across Product Categories.
        """
        cat_df = product_df.groupby("Category")["Total_Revenue"].sum().reset_index()

        fig, ax = plt.subplots(figsize=(7, 7))
        colors = sns.color_palette("pastel")[0:len(cat_df)]

        wedges, texts, autotexts = ax.pie(
            cat_df["Total_Revenue"], 
            labels=cat_df["Category"], 
            autopct="%1.1f%%",
            startangle=140, 
            colors=colors,
            pctdistance=0.75,
            textprops=dict(fontweight="bold")
        )

        # Draw circle for Donut appearance
        centre_circle = plt.Circle((0, 0), 0.50, fc='white')
        fig.gca().add_artist(centre_circle)

        plt.title("Revenue Contribution by Category", fontsize=14, fontweight="bold", pad=15)

        file_path = os.path.join(self.output_dir, "revenue_by_category.png")
        plt.savefig(file_path, dpi=300, bbox_inches="tight")
        plt.close()
        logger.info(f"Saved visualization: {file_path}")
        return file_path

    def plot_customer_segment_matrix(self, segment_df: pd.DataFrame) -> str:
        """
        Renders Bar Chart for Customer Segment Performance.
        """
        fig, ax = plt.subplots(figsize=(8, 5))

        sns.barplot(
            data=segment_df, x="Customer_Segment", y="Total_Revenue",
            palette="magma", ax=ax
        )

        plt.title("Revenue Breakdown by Customer Segment", fontsize=14, fontweight="bold", pad=15)
        plt.xlabel("Customer Segment", fontweight="bold")
        plt.ylabel("Total Revenue ($)", fontweight="bold")

        for p in ax.patches:
            height = p.get_height()
            ax.annotate(
                f"${height:,.0f}",
                (p.get_x() + p.get_width() / 2., height),
                ha='center', va='bottom', fontsize=9, xytext=(0, 3),
                textcoords='offset points'
            )

        file_path = os.path.join(self.output_dir, "customer_segment_matrix.png")
        plt.savefig(file_path, dpi=300, bbox_inches="tight")
        plt.close()
        logger.info(f"Saved visualization: {file_path}")
        return file_path

    def plot_top_products(self, product_df: pd.DataFrame) -> str:
        """
        Renders Horizontal Bar Chart of Top Products by Revenue.
        """
        top10 = product_df.head(10).sort_values(by="Total_Revenue", ascending=True)

        fig, ax = plt.subplots(figsize=(10, 5))
        prod_col = "Product" if "Product" in top10.columns else "Product_ID"

        sns.barplot(
            data=top10, y=prod_col, x="Total_Revenue",
            palette="Blues_r", ax=ax
        )

        plt.title("Top Products by Revenue Generation", fontsize=14, fontweight="bold", pad=15)
        plt.xlabel("Total Revenue ($)", fontweight="bold")
        plt.ylabel("Product", fontweight="bold")

        for p in ax.patches:
            width = p.get_width()
            ax.annotate(
                f"${width:,.0f}",
                (width, p.get_y() + p.get_height() / 2.),
                ha='left', va='center', fontsize=9, xytext=(5, 0),
                textcoords='offset points'
            )

        file_path = os.path.join(self.output_dir, "top_products_bar.png")
        plt.savefig(file_path, dpi=300, bbox_inches="tight")
        plt.close()
        logger.info(f"Saved visualization: {file_path}")
        return file_path
