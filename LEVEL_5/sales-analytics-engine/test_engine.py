import os
import shutil
import unittest
import pandas as pd
import numpy as np

from sample_data_generator import generate_sample_sales_data
from data_loader import DataLoader
from cleaning import DataCleaner
from kpi_calculator import KPICalculator
from trend_analysis import TrendAnalyzer
from visualization import Visualizer
from report_generator import ReportGenerator

class TestSalesAnalyticsEngine(unittest.TestCase):
    """
    Automated Unit Test Suite for Sales Performance Analytics Engine.
    """

    @classmethod
    def setUpClass(cls):
        cls.test_dir = "test_output"
        os.makedirs(cls.test_dir, exist_ok=True)
        cls.csv_file = os.path.join(cls.test_dir, "test_sales_data.csv")
        cls.excel_file = os.path.join(cls.test_dir, "test_sales_data.xlsx")
        
        # Generate sample test dataset
        generate_sample_sales_data(
            file_path_csv=cls.csv_file,
            file_path_excel=cls.excel_file,
            num_records=100,
            seed=123
        )

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(cls.test_dir):
            shutil.rmtree(cls.test_dir)

    def test_01_data_loader_csv_and_excel(self):
        """Test primary ingestion from CSV and Excel files."""
        df_csv = DataLoader.load_dataset(self.csv_file)
        self.assertFalse(df_csv.empty)
        self.assertIn("Date", df_csv.columns)
        self.assertIn("Sales_Amount", df_csv.columns)

        df_excel = DataLoader.load_dataset(self.excel_file)
        self.assertFalse(df_excel.empty)
        self.assertIn("Date", df_excel.columns)

    def test_02_data_cleaner(self):
        """Test data validation, cleaning, date formatting, and duplicate removal."""
        df_raw = DataLoader.load_dataset(self.csv_file)
        df_clean = DataCleaner.clean_data(df_raw)

        self.assertFalse(df_clean.empty)
        self.assertTrue(pd.api.types.is_datetime64_any_dtype(df_clean["Date"]))
        self.assertIn("Year_Month", df_clean.columns)
        self.assertIn("Quarter", df_clean.columns)
        self.assertEqual(df_clean.duplicated().sum(), 0)

    def test_03_kpi_calculator(self):
        """Test KPI aggregations, totals, and pct_change monthly growth calculation."""
        df_raw = DataLoader.load_dataset(self.csv_file)
        df_clean = DataCleaner.clean_data(df_raw)

        kpi_calc = KPICalculator(df_clean)
        overall = kpi_calc.compute_overall_kpis()

        self.assertGreater(overall["Total_Sales_Revenue"], 0)
        self.assertGreater(overall["Total_Units_Sold"], 0)
        self.assertGreater(overall["Average_Order_Value"], 0)

        monthly = kpi_calc.compute_monthly_growth()
        self.assertIn("MoM_Growth_Rate_Pct", monthly.columns)
        self.assertFalse(monthly.empty)

        regional = kpi_calc.compute_regional_performance()
        self.assertIn("Revenue_Contribution_Pct", regional.columns)
        self.assertAlmostEqual(regional["Revenue_Contribution_Pct"].sum(), 100.0, delta=0.5)

    def test_04_trend_analysis(self):
        """Test peak revenue and seasonality detection."""
        df_raw = DataLoader.load_dataset(self.csv_file)
        df_clean = DataCleaner.clean_data(df_raw)
        kpi_calc = KPICalculator(df_clean)
        monthly = kpi_calc.compute_monthly_growth()

        trend_analyzer = TrendAnalyzer(df_clean, monthly)
        seasonality = trend_analyzer.analyze_seasonality_and_peaks()

        self.assertIn("Peak_Revenue_Month", seasonality)
        self.assertIn("Highest_Growth_Rate_Pct", seasonality)

    def test_05_visualizer(self):
        """Test rendering and saving PNG chart visual artifacts."""
        df_raw = DataLoader.load_dataset(self.csv_file)
        df_clean = DataCleaner.clean_data(df_raw)
        kpi_calc = KPICalculator(df_clean)
        
        monthly = kpi_calc.compute_monthly_growth()
        regional = kpi_calc.compute_regional_performance()
        product = kpi_calc.compute_product_performance()
        segment = kpi_calc.compute_segment_performance()

        charts_dir = os.path.join(self.test_dir, "charts")
        visualizer = Visualizer(output_dir=charts_dir)
        
        p1 = visualizer.plot_monthly_sales_trend(monthly)
        p2 = visualizer.plot_regional_performance(regional)
        p3 = visualizer.plot_revenue_by_category(product)
        p4 = visualizer.plot_customer_segment_matrix(segment)
        p5 = visualizer.plot_top_products(product)

        for p in [p1, p2, p3, p4, p5]:
            self.assertTrue(os.path.exists(p))

    def test_06_report_generator(self):
        """Test Excel and CSV report generation."""
        df_raw = DataLoader.load_dataset(self.csv_file)
        df_clean = DataCleaner.clean_data(df_raw)
        kpi_calc = KPICalculator(df_clean)
        
        overall = kpi_calc.compute_overall_kpis()
        monthly = kpi_calc.compute_monthly_growth()
        regional = kpi_calc.compute_regional_performance()
        product = kpi_calc.compute_product_performance()

        reporter = ReportGenerator(output_dir=self.test_dir)
        
        # Test CSV exports
        csv_paths = reporter.export_csv_reports(
            cleaned_df=df_clean,
            kpi_summary=pd.DataFrame([overall]),
            monthly_df=monthly,
            regional_df=regional
        )
        for name, path in csv_paths.items():
            self.assertTrue(os.path.exists(path))

        # Test Excel export
        excel_path = reporter.export_excel_report(
            cleaned_df=df_clean,
            kpis=overall,
            insights=["Test Insight Statement"],
            regional_df=regional,
            product_df=product,
            monthly_df=monthly,
            file_name="test_sales_report.xlsx"
        )
        self.assertTrue(os.path.exists(excel_path))

if __name__ == "__main__":
    unittest.main()
