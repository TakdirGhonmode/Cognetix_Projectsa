import os
import sys
import argparse
import logging
import pandas as pd

from sample_data_generator import generate_sample_sales_data
from data_loader import DataLoader
from cleaning import DataCleaner
from database import DatabaseManager
from kpi_calculator import KPICalculator
from trend_analysis import TrendAnalyzer
from insight_generator import InsightGenerator
from visualization import Visualizer
from report_generator import ReportGenerator

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def print_banner():
    banner = """
======================================================================
               SALES PERFORMANCE ANALYTICS ENGINE                    
      Business Intelligence & Data Analytics Decision Platform        
======================================================================
"""
    print(banner)

def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Sales Performance Analytics Engine - BI & Decision System"
    )
    parser.add_argument(
        "--input", "-i", type=str, default="sales_data.csv",
        help="Path to input sales dataset (CSV or Excel file). Default: sales_data.csv"
    )
    parser.add_argument(
        "--output-dir", "-o", type=str, default="output",
        help="Directory to save exported reports and visualizations. Default: output"
    )
    parser.add_argument(
        "--generate-sample", "-g", action="store_true",
        help="Generate synthetic sample CSV and Excel sales datasets before running analysis."
    )
    parser.add_argument(
        "--skip-db", action="store_true",
        help="Skip MySQL database ingestion step if MySQL server is not running locally."
    )
    return parser.parse_args()

def main():
    print_banner()
    args = parse_arguments()

    # Step 0: Optional Synthetic Data Generation
    if args.generate_sample or not os.path.exists(args.input):
        logger.info(f"Input file '{args.input}' not found or --generate-sample flag set.")
        logger.info("Generating synthetic primary sales datasets (sales_data.csv & sales_data.xlsx)...")
        generate_sample_sales_data(file_path_csv="sales_data.csv", file_path_excel="sales_data.xlsx")
        args.input = "sales_data.csv"

    # Step 1: Load Structured Sales Dataset
    print("\n[STEP 1] Ingesting Primary Sales Dataset...")
    raw_df = DataLoader.load_dataset(args.input)
    print(f" -> Ingested {len(raw_df)} records from '{args.input}'.")

    # Step 2 & 3: Validate, Clean & Normalize Data
    print("\n[STEP 2 & 3] Validating & Cleaning Data Integrity...")
    cleaned_df = DataCleaner.clean_data(raw_df)
    print(f" -> Data cleaned and normalized. Final valid records: {len(cleaned_df)}.")

    # Step 4: Post-Cleaning MySQL Database Storage
    print("\n[STEP 4] MySQL Database Ingestion Layer...")
    if not args.skip_db:
        db_mgr = DatabaseManager()
        success = db_mgr.save_cleaned_data(cleaned_df)
        if success:
            print(" -> Cleaned dataset successfully stored into MySQL database ('products' & 'sales' tables).")
            # Fetch data back from MySQL to verify database roundtrip
            analytical_df = db_mgr.fetch_sales_data()
            if not analytical_df.empty:
                cleaned_df = analytical_df
        else:
            print(" -> Warning: MySQL storage step could not complete (Check MySQL connection). Continuing with cleaned DataFrame.")
    else:
        print(" -> Skipping MySQL Database ingestion as requested by --skip-db flag.")

    # Step 5: KPI Calculation
    print("\n[STEP 5] Computing Financial & Operational KPIs...")
    kpi_calc = KPICalculator(cleaned_df)
    overall_kpis = kpi_calc.compute_overall_kpis()
    monthly_kpis = kpi_calc.compute_monthly_growth()
    regional_kpis = kpi_calc.compute_regional_performance()
    product_kpis = kpi_calc.compute_product_performance()
    segment_kpis = kpi_calc.compute_segment_performance()

    print("\n--- EXECUTIVE KEY PERFORMANCE INDICATORS (KPIs) ---")
    for metric, value in overall_kpis.items():
        if isinstance(value, float):
            print(f" • {metric.replace('_', ' ')}: ${value:,.2f}")
        else:
            print(f" • {metric.replace('_', ' ')}: {value:,}")

    # Step 6: Trend & Growth Analysis
    print("\n[STEP 6] Performing Trend & Growth Analysis...")
    trend_analyzer = TrendAnalyzer(cleaned_df, monthly_kpis)
    seasonality = trend_analyzer.analyze_seasonality_and_peaks()
    cat_reg_trends = trend_analyzer.analyze_category_and_region_trends()
    ml_trends = trend_analyzer.predict_sales_trend()

    print(f" -> Peak Revenue Month: {seasonality.get('Peak_Revenue_Month')} (${seasonality.get('Peak_Revenue_Amount', 0):,.2f})")
    print(f" -> Top Performing Region: {cat_reg_trends.get('Top_Performing_Region')}")
    print(f" -> Best Product Category: {cat_reg_trends.get('Best_Category')}")

    # Step 7: Insight Generation
    print("\n[STEP 7] Generating Business Insights & Actionable Recommendations...")
    insights = InsightGenerator.generate_insights(
        overall_kpis, seasonality, cat_reg_trends, product_kpis, ml_trends
    )

    print("\n--- BUSINESS INSIGHTS & MANAGEMENT RECOMMENDATIONS ---")
    for idx, insight in enumerate(insights, 1):
        print(f" [{idx}] {insight}")

    # Step 8: Visualization
    print("\n[STEP 8] Rendering Visual Analytics & Charts...")
    charts_dir = os.path.join(args.output_dir, "charts")
    visualizer = Visualizer(output_dir=charts_dir)
    visualizer.plot_monthly_sales_trend(monthly_kpis)
    visualizer.plot_regional_performance(regional_kpis)
    visualizer.plot_revenue_by_category(product_kpis)
    visualizer.plot_customer_segment_matrix(segment_kpis)
    visualizer.plot_top_products(product_kpis)
    print(f" -> High-resolution charts saved into: {charts_dir}")

    # Step 9: Export Reports
    print("\n[STEP 9] Exporting Management Reports (Excel, CSV, HTML)...")
    reporter = ReportGenerator(output_dir=args.output_dir)
    
    # Export CSVs
    reporter.export_csv_reports(
        cleaned_df=cleaned_df,
        kpi_summary=pd.DataFrame([overall_kpis]),
        monthly_df=monthly_kpis,
        regional_df=regional_kpis
    )

    # Export Excel Workbook
    excel_path = reporter.export_excel_report(
        cleaned_df=cleaned_df,
        kpis=overall_kpis,
        insights=insights,
        regional_df=regional_kpis,
        product_df=product_kpis,
        monthly_df=monthly_kpis
    )

    # Export Optional HTML Dashboard
    html_path = reporter.export_optional_html_report(
        kpis=overall_kpis,
        insights=insights
    )

    print("\n======================================================================")
    print("                  ANALYTICAL PIPELINE COMPLETE                        ")
    print("======================================================================")
    print(f" • Cleaned Dataset:  {os.path.join(args.output_dir, 'cleaned_sales_data.csv')}")
    print(f" • KPI Summary CSV:   {os.path.join(args.output_dir, 'kpi_summary.csv')}")
    print(f" • Excel Report:      {excel_path}")
    print(f" • Visual Dashboard:  {html_path}")
    print(f" • Charts Directory:  {charts_dir}")
    print("======================================================================\n")

if __name__ == "__main__":
    main()
