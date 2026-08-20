import json
import logging
import pandas as pd
from typing import Dict, List, Optional, Any

# Configure logger for database module
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("MySQLDatabase")

# Driver compatibility: try mysql.connector first, then pymysql
MYSQL_AVAILABLE = False
try:
    import mysql.connector
    from mysql.connector import Error as MySQLError
    MYSQL_DRIVER = "mysql.connector"
    MYSQL_AVAILABLE = True
except ImportError:
    try:
        import pymysql
        MySQLError = pymysql.Error
        MYSQL_DRIVER = "pymysql"
        MYSQL_AVAILABLE = True
    except ImportError:
        MYSQL_DRIVER = None
        MYSQL_AVAILABLE = False


class MySQLDatabaseManager:
    """
    Manages MySQL database connection, table initialization,
    and query execution for transactions, flagged_transactions, and audit_logs.
    """

    def __init__(self, config_path: str = "config.json"):
        self.config = self._load_config(config_path)
        self.db_config = self.config.get("database", {})
        self.connection = None
        self.is_connected = False

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Loads DB credentials from config file."""
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Could not load config file '{config_path}': {e}. Using default DB settings.")
            return {
                "database": {
                    "host": "localhost",
                    "port": 3306,
                    "user": "root",
                    "password": "",
                    "database": "fraud_detection_db"
                }
            }

    def connect(self) -> bool:
        """Establishes connection to MySQL database server."""
        if not MYSQL_AVAILABLE:
            logger.warning("Neither 'mysql-connector-python' nor 'pymysql' is installed. "
                           "MySQL operations will run in simulation mode. Install with: pip install mysql-connector-python")
            self.is_connected = False
            return False

        try:
            host = self.db_config.get("host", "localhost")
            port = int(self.db_config.get("port", 3306))
            user = self.db_config.get("user", "root")
            password = self.db_config.get("password", "")
            db_name = self.db_config.get("database", "fraud_detection_db")

            if MYSQL_DRIVER == "mysql.connector":
                # First connect without DB to ensure database exists
                conn_no_db = mysql.connector.connect(
                    host=host, port=port, user=user, password=password
                )
                cursor = conn_no_db.cursor()
                cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name};")
                cursor.close()
                conn_no_db.close()

                # Connect to specific database
                self.connection = mysql.connector.connect(
                    host=host, port=port, user=user, password=password, database=db_name
                )
            elif MYSQL_DRIVER == "pymysql":
                conn_no_db = pymysql.connect(host=host, port=port, user=user, password=password)
                cursor = conn_no_db.cursor()
                cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name};")
                cursor.close()
                conn_no_db.close()

                self.connection = pymysql.connect(
                    host=host, port=port, user=user, password=password, database=db_name,
                    autocommit=True
                )

            self.is_connected = True
            logger.info(f"Successfully connected to MySQL database '{db_name}' using driver '{MYSQL_DRIVER}'.")
            return True

        except Exception as e:
            logger.warning(f"Unable to connect to MySQL database: {e}. Engine will operate with CSV/log outputs.")
            self.is_connected = False
            return False

    def initialize_schema(self) -> bool:
        """Creates required tables: transactions, flagged_transactions, audit_logs."""
        if not self.is_connected and not self.connect():
            return False

        create_transactions_tbl = """
        CREATE TABLE IF NOT EXISTS transactions (
            id INT AUTO_INCREMENT PRIMARY KEY,
            transaction_id VARCHAR(50) NOT NULL UNIQUE,
            user_id VARCHAR(50) NOT NULL,
            transaction_amount DECIMAL(12, 2) NOT NULL,
            transaction_date DATETIME NOT NULL,
            location VARCHAR(100) NOT NULL,
            payment_method VARCHAR(50) NOT NULL,
            status VARCHAR(20) DEFAULT 'SUCCESS',
            device_id VARCHAR(100) DEFAULT 'UNKNOWN',
            ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_user_id (user_id),
            INDEX idx_transaction_date (transaction_date)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """

        create_flagged_tbl = """
        CREATE TABLE IF NOT EXISTS flagged_transactions (
            id INT AUTO_INCREMENT PRIMARY KEY,
            transaction_id VARCHAR(50) NOT NULL,
            user_id VARCHAR(50) NOT NULL,
            transaction_amount DECIMAL(12, 2) NOT NULL,
            transaction_date DATETIME NOT NULL,
            location VARCHAR(100) NOT NULL,
            payment_method VARCHAR(50) NOT NULL,
            risk_score INT NOT NULL,
            risk_level ENUM('LOW', 'MEDIUM', 'HIGH') NOT NULL,
            triggered_rules TEXT NOT NULL,
            rule_count INT NOT NULL DEFAULT 1,
            status VARCHAR(30) DEFAULT 'FLAGGED',
            flagged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_risk_level (risk_level),
            INDEX idx_flagged_user (user_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """

        create_audit_tbl = """
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INT AUTO_INCREMENT PRIMARY KEY,
            transaction_id VARCHAR(50) NOT NULL,
            timestamp DATETIME NOT NULL,
            event_type VARCHAR(50) NOT NULL,
            triggered_rules TEXT,
            risk_score INT,
            status VARCHAR(30) NOT NULL,
            log_message TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_audit_tx (transaction_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """

        try:
            cursor = self.connection.cursor()
            cursor.execute(create_transactions_tbl)
            cursor.execute(create_flagged_tbl)
            cursor.execute(create_audit_tbl)
            if hasattr(self.connection, "commit"):
                self.connection.commit()
            cursor.close()
            logger.info("MySQL tables ('transactions', 'flagged_transactions', 'audit_logs') initialized.")
            return True
        except Exception as e:
            logger.error(f"Error initializing MySQL schema: {e}")
            return False

    def insert_transactions(self, df: pd.DataFrame) -> int:
        """Inserts raw ingested transactions into MySQL transactions table."""
        if not self.is_connected and not self.connect():
            return 0

        query = """
        INSERT INTO transactions 
        (transaction_id, user_id, transaction_amount, transaction_date, location, payment_method, status, device_id)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE 
        transaction_amount = VALUES(transaction_amount),
        location = VALUES(location);
        """
        inserted_count = 0
        try:
            cursor = self.connection.cursor()
            for idx, row in df.iterrows():
                tx_date = row['Date'].strftime('%Y-%m-%d %H:%M:%S') if isinstance(row['Date'], pd.Timestamp) else str(row['Date'])
                status = str(row.get('Status', 'SUCCESS'))
                device = str(row.get('Device ID', 'UNKNOWN'))

                vals = (
                    str(row['Transaction ID']),
                    str(row['User ID']),
                    float(row['Transaction Amount']),
                    tx_date,
                    str(row['Location']),
                    str(row['Payment Method']),
                    status,
                    device
                )
                cursor.execute(query, vals)
                inserted_count += 1

            if hasattr(self.connection, "commit"):
                self.connection.commit()
            cursor.close()
            logger.info(f"Stored {inserted_count} transaction records in MySQL database.")
            return inserted_count
        except Exception as e:
            logger.error(f"Failed to insert transactions into MySQL: {e}")
            return 0

    def insert_flagged_transactions(self, df: pd.DataFrame) -> int:
        """Inserts flagged transactions into MySQL flagged_transactions table."""
        if not self.is_connected and not self.connect():
            return 0

        query = """
        INSERT INTO flagged_transactions 
        (transaction_id, user_id, transaction_amount, transaction_date, location, payment_method, risk_score, risk_level, triggered_rules, rule_count, status)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
        """
        inserted_count = 0
        try:
            cursor = self.connection.cursor()
            for idx, row in df.iterrows():
                tx_date = row['Date'].strftime('%Y-%m-%d %H:%M:%S') if isinstance(row['Date'], pd.Timestamp) else str(row['Date'])
                rules_str = ", ".join(row['Triggered Rules']) if isinstance(row['Triggered Rules'], list) else str(row['Triggered Rules'])
                rule_count = int(row.get('Rule Count', 1))

                vals = (
                    str(row['Transaction ID']),
                    str(row['User ID']),
                    float(row['Transaction Amount']),
                    tx_date,
                    str(row['Location']),
                    str(row['Payment Method']),
                    int(row['Risk Score']),
                    str(row['Risk Level']),
                    rules_str,
                    rule_count,
                    'FLAGGED'
                )
                cursor.execute(query, vals)
                inserted_count += 1

            if hasattr(self.connection, "commit"):
                self.connection.commit()
            cursor.close()
            logger.info(f"Stored {inserted_count} flagged transactions in MySQL 'flagged_transactions' table.")
            return inserted_count
        except Exception as e:
            logger.error(f"Failed to insert flagged transactions into MySQL: {e}")
            return 0

    def insert_audit_log(self, tx_id: str, timestamp: str, event_type: str, rules: str, risk_score: int, status: str, message: str) -> bool:
        """Inserts a single log record into MySQL audit_logs table."""
        if not self.is_connected and not self.connect():
            return False

        query = """
        INSERT INTO audit_logs (transaction_id, timestamp, event_type, triggered_rules, risk_score, status, log_message)
        VALUES (%s, %s, %s, %s, %s, %s, %s);
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute(query, (tx_id, str(timestamp), event_type, rules, risk_score, status, message))
            if hasattr(self.connection, "commit"):
                self.connection.commit()
            cursor.close()
            return True
        except Exception as e:
            logger.error(f"Failed to write audit log to MySQL: {e}")
            return False

    def fetch_flagged_transactions(self, min_risk_score: Optional[int] = None, date_from: Optional[str] = None, date_to: Optional[str] = None) -> pd.DataFrame:
        """Fetches flagged transactions with optional risk score and date filtering."""
        if not self.is_connected and not self.connect():
            return pd.DataFrame()

        query = "SELECT transaction_id, user_id, transaction_amount, transaction_date, location, payment_method, risk_score, risk_level, triggered_rules, status FROM flagged_transactions WHERE 1=1"
        params = []

        if min_risk_score is not None:
            query += " AND risk_score >= %s"
            params.append(min_risk_score)
        if date_from:
            query += " AND transaction_date >= %s"
            params.append(date_from)
        if date_to:
            query += " AND transaction_date <= %s"
            params.append(date_to)

        query += " ORDER BY risk_score DESC;"

        try:
            cursor = self.connection.cursor()
            cursor.execute(query, tuple(params))
            rows = cursor.fetchall()
            columns = [col[0] for col in cursor.description]
            cursor.close()

            df = pd.DataFrame(rows, columns=columns)
            return df
        except Exception as e:
            logger.error(f"Failed to fetch flagged transactions from MySQL: {e}")
            return pd.DataFrame()

    def fetch_monthly_summary(self) -> pd.DataFrame:
        """Fetches monthly fraud summary report aggregated by YYYY-MM."""
        if not self.is_connected and not self.connect():
            return pd.DataFrame()

        query = """
        SELECT 
            DATE_FORMAT(transaction_date, '%Y-%m') AS month,
            COUNT(*) AS total_flagged_transactions,
            SUM(transaction_amount) AS total_flagged_amount,
            AVG(risk_score) AS average_risk_score,
            SUM(CASE WHEN risk_level = 'HIGH' THEN 1 ELSE 0 END) AS high_risk_count,
            SUM(CASE WHEN risk_level = 'MEDIUM' THEN 1 ELSE 0 END) AS medium_risk_count,
            SUM(CASE WHEN risk_level = 'LOW' THEN 1 ELSE 0 END) AS low_risk_count
        FROM flagged_transactions
        GROUP BY DATE_FORMAT(transaction_date, '%Y-%m')
        ORDER BY month DESC;
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute(query)
            rows = cursor.fetchall()
            columns = [col[0] for col in cursor.description]
            cursor.close()

            return pd.DataFrame(rows, columns=columns)
        except Exception as e:
            logger.error(f"Failed to fetch monthly summary from MySQL: {e}")
            return pd.DataFrame()

    def close(self):
        """Closes the MySQL database connection."""
        if self.connection and self.is_connected:
            try:
                self.connection.close()
                self.is_connected = False
                logger.info("MySQL connection closed.")
            except Exception as e:
                logger.error(f"Error closing MySQL connection: {e}")
