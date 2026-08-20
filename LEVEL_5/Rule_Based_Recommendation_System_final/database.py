import json
import logging
import mysql.connector
from mysql.connector import errorcode

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("Database")


def get_db_config(config_path="config.json"):
    """Load database configuration from config.json."""
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)
    return config.get("database", {})


def get_db_connection(config_path="config.json", include_db=True):
    """
    Establish and return a MySQL connection using mysql-connector-python.
    """
    db_config = get_db_config(config_path)
    host = db_config.get("host", "localhost")
    port = db_config.get("port", 3306)
    user = db_config.get("user", "root")
    password = db_config.get("password", "")
    database = db_config.get("database", "recommendation_db")

    try:
        conn_params = {
            "host": host,
            "port": port,
            "user": user,
            "password": password
        }
        if include_db:
            conn_params["database"] = database

        conn = mysql.connector.connect(**conn_params)
        return conn
    except mysql.connector.Error as err:
        logger.error(f"MySQL Connection Error: {err}")
        raise err


def initialize_database(config_path="config.json"):
    """
    Create MySQL database and tables if they do not exist.
    """
    db_config = get_db_config(config_path)
    database_name = db_config.get("database", "recommendation_db")

    # Connect to MySQL server (without selecting specific DB first)
    conn = get_db_connection(config_path, include_db=False)
    cursor = conn.cursor()

    try:
        # Create database
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{database_name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
        logger.info(f"Database '{database_name}' checked/created.")
        cursor.close()
        conn.close()

        # Connect to specific database to create tables
        conn = get_db_connection(config_path, include_db=True)
        cursor = conn.cursor()

        tables = {}

        tables["users"] = """
        CREATE TABLE IF NOT EXISTS users (
            user_id VARCHAR(50) PRIMARY KEY,
            username VARCHAR(100) NOT NULL,
            email VARCHAR(100) NOT NULL,
            user_tier VARCHAR(20) NOT NULL DEFAULT 'Standard',
            total_spent DECIMAL(10, 2) DEFAULT 0.00,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB;
        """

        tables["products"] = """
        CREATE TABLE IF NOT EXISTS products (
            product_id VARCHAR(50) PRIMARY KEY,
            product_name VARCHAR(150) NOT NULL,
            category VARCHAR(100) NOT NULL,
            price DECIMAL(10, 2) NOT NULL,
            popularity_score FLOAT DEFAULT 0.0,
            stock_quantity INT DEFAULT 0,
            tags TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB;
        """

        tables["user_behavior"] = """
        CREATE TABLE IF NOT EXISTS user_behavior (
            behavior_id INT AUTO_INCREMENT PRIMARY KEY,
            user_id VARCHAR(50) NOT NULL,
            product_id VARCHAR(50) NOT NULL,
            action_type ENUM('view', 'purchase', 'cart', 'search') NOT NULL,
            search_query VARCHAR(255) NULL,
            interaction_count INT DEFAULT 1,
            timestamp DATETIME NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
            FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE CASCADE
        ) ENGINE=InnoDB;
        """

        tables["recommendations"] = """
        CREATE TABLE IF NOT EXISTS recommendations (
            recommendation_id INT AUTO_INCREMENT PRIMARY KEY,
            user_id VARCHAR(50) NOT NULL,
            product_id VARCHAR(50) NOT NULL,
            score FLOAT NOT NULL,
            rank_order INT NOT NULL,
            applied_rule VARCHAR(100) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
            FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE CASCADE
        ) ENGINE=InnoDB;
        """

        tables["decision_logs"] = """
        CREATE TABLE IF NOT EXISTS decision_logs (
            log_id INT AUTO_INCREMENT PRIMARY KEY,
            user_id VARCHAR(50) NOT NULL,
            applied_rules_json TEXT NOT NULL,
            recommendations_json TEXT NOT NULL,
            relevance_scores_json TEXT NOT NULL,
            timestamp DATETIME NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
        ) ENGINE=InnoDB;
        """

        for table_name, ddl in tables.items():
            cursor.execute(ddl)
            logger.info(f"Table '{table_name}' verified/created.")

        conn.commit()
    finally:
        cursor.close()
        conn.close()
