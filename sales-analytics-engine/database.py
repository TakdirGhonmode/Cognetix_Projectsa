import os
import logging
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError
from pymysql.err import MySQLError
import database_config as config

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

class DatabaseManager:
    """
    Manages MySQL database connectivity, schema initialization, 
    data insertion, and analytical query execution using SQLAlchemy and Pandas.
    """
    def __init__(self):
        self.connection_string = config.get_connection_string(include_db=True)
        self.server_connection_string = config.get_connection_string(include_db=False)
        self._engine = None

    def get_engine(self):
        """Lazy initialization of SQLAlchemy engine."""
        if self._engine is None:
            self._engine = create_engine(self.connection_string, pool_recycle=3600)
        return self._engine

    def init_db(self, schema_file: str = "mysql_schema.sql") -> bool:
        """
        Executes DDL statements to create database and tables.
        """
        try:
            # First create database if missing using server engine
            server_engine = create_engine(self.server_connection_string)
            with server_engine.connect() as conn:
                conn.execute(text(f"CREATE DATABASE IF NOT EXISTS {config.DB_NAME};"))
                conn.commit()
            server_engine.dispose()

            # Execute schema file statements
            if os.path.exists(schema_file):
                with open(schema_file, "r", encoding="utf-8") as f:
                    sql_content = f.read()

                statements = [s.strip() for s in sql_content.split(";") if s.strip()]
                engine = self.get_engine()
                with engine.connect() as conn:
                    for statement in statements:
                        conn.execute(text(statement))
                    conn.commit()
                logger.info("MySQL Database schema initialized successfully.")
                return True
            else:
                logger.warning(f"Schema file {schema_file} not found. Creating default schema...")
                return self._create_default_schema()

        except (OperationalError, MySQLError, Exception) as e:
            logger.error(f"Failed to initialize MySQL Database: {e}")
            return False

    def _create_default_schema(self) -> bool:
        """Fallback inline DDL execution."""
        ddl_products = """
        CREATE TABLE IF NOT EXISTS products (
            product_id VARCHAR(50) PRIMARY KEY,
            product_name VARCHAR(100) NOT NULL,
            category VARCHAR(50) NOT NULL,
            unit_price DECIMAL(10, 2) NOT NULL
        );
        """
        ddl_sales = """
        CREATE TABLE IF NOT EXISTS sales (
            transaction_id VARCHAR(50) PRIMARY KEY,
            date DATE NOT NULL,
            product_id VARCHAR(50) NOT NULL,
            region VARCHAR(50) NOT NULL,
            quantity INT NOT NULL,
            sales_amount DECIMAL(12, 2) NOT NULL,
            discount_pct DECIMAL(5, 4) DEFAULT 0.0000,
            customer_segment VARCHAR(50) NOT NULL,
            payment_method VARCHAR(50),
            FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE CASCADE
        );
        """
        try:
            engine = self.get_engine()
            with engine.connect() as conn:
                conn.execute(text(ddl_products))
                conn.execute(text(ddl_sales))
                conn.commit()
            logger.info("Default MySQL schema created successfully.")
            return True
        except Exception as e:
            logger.error(f"Error creating default schema: {e}")
            return False

    def save_cleaned_data(self, cleaned_df: pd.DataFrame) -> bool:
        """
        Splits cleaned DataFrame into relational tables ('products' and 'sales')
        and persists them into MySQL via pandas to_sql.
        """
        try:
            engine = self.get_engine()

            # Ensure schema is ready
            self.init_db()

            # Clear previous table contents to enable clean re-execution
            with engine.connect() as conn:
                conn.execute(text("SET FOREIGN_KEY_CHECKS = 0;"))
                conn.execute(text("TRUNCATE TABLE sales;"))
                conn.execute(text("TRUNCATE TABLE products;"))
                conn.execute(text("SET FOREIGN_KEY_CHECKS = 1;"))
                conn.commit()

            # Extract distinct products table
            prod_name_col = 'Product' if 'Product' in cleaned_df.columns else 'Product_Name'
            products_df = cleaned_df[[
                'Product_ID', prod_name_col, 'Category', 'Unit_Price'
            ]].drop_duplicates(subset=['Product_ID']).copy()
            
            products_df.columns = ['product_id', 'product_name', 'category', 'unit_price']

            # Extract sales table
            sales_df = cleaned_df[[
                'Transaction_ID', 'Date', 'Product_ID', 'Region', 
                'Quantity', 'Sales_Amount', 'Discount_Pct', 
                'Customer_Segment', 'Payment_Method'
            ]].copy()

            sales_df.columns = [
                'transaction_id', 'date', 'product_id', 'region', 
                'quantity', 'sales_amount', 'discount_pct', 
                'customer_segment', 'payment_method'
            ]

            # Ingest products first (dimension table)
            products_df.to_sql(
                name='products',
                con=engine,
                if_exists='append',
                index=False,
                chunksize=500,
                method='multi'
            )
            logger.info(f"Loaded {len(products_df)} products into MySQL 'products' table.")

            # Ingest sales (fact table)
            sales_df.to_sql(
                name='sales',
                con=engine,
                if_exists='append',
                index=False,
                chunksize=1000,
                method='multi'
            )
            logger.info(f"Loaded {len(sales_df)} transactions into MySQL 'sales' table.")
            return True

        except Exception as e:
            logger.error(f"Failed to save cleaned data into MySQL: {e}")
            return False

    def fetch_sales_data(self) -> pd.DataFrame:
        """
        Fetches combined sales dataset from MySQL using SQL JOIN for downstream analytics.
        """
        query = """
        SELECT 
            s.transaction_id AS Transaction_ID,
            s.date AS Date,
            s.product_id AS Product_ID,
            p.product_name AS Product,
            p.category AS Category,
            p.unit_price AS Unit_Price,
            s.region AS Region,
            s.quantity AS Quantity,
            s.sales_amount AS Sales_Amount,
            s.discount_pct AS Discount_Pct,
            s.customer_segment AS Customer_Segment,
            s.payment_method AS Payment_Method
        FROM sales s
        JOIN products p ON s.product_id = p.product_id
        ORDER BY s.date ASC;
        """
        try:
            engine = self.get_engine()
            df = pd.read_sql(query, con=engine)
            df['Date'] = pd.to_datetime(df['Date'])
            logger.info(f"Fetched {len(df)} records from MySQL database.")
            return df
        except Exception as e:
            logger.error(f"Failed to fetch data from MySQL: {e}")
            return pd.DataFrame()
